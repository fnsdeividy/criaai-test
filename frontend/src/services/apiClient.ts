/**
 * Cliente API seguro com retry e error handling
 */

import { API_CONFIG } from "@/config/app";
import { createSecureHeaders, isSecureUrl } from "@/utils/security";
import type {
  ApiResponse,
  ProcessData,
  ExtractRequest,
  UploadRequest,
  ApiErrorResponse
} from "@/types/api";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: ApiErrorResponse
  ) {
    super(message);
    this.name = "ApiError";
  }
}

class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private retryAttempts: number;
  private retryDelay: number;

  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
    this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS;
    this.retryDelay = API_CONFIG.RETRY_DELAY;
  }

  /**
   * Executa uma requisição com retry automático
   */
  private async executeWithRetry<T>(
    requestFn: () => Promise<Response>,
    attempt: number = 1
  ): Promise<ApiResponse<T>> {
    try {
      const response = await requestFn();

      if (response.ok) {
        const data = await response.json();
        return {
          data: data as T,
          status: response.status,
        };
      }

      // Tentar obter erro do corpo da resposta
      let errorResponse: ApiErrorResponse;
      try {
        errorResponse = await response.json();
      } catch {
        errorResponse = {
          detail: `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      // Se for erro 4xx, não tentar novamente
      if (response.status >= 400 && response.status < 500) {
        return {
          error: errorResponse,
          status: response.status,
        };
      }

      // Para erros 5xx, tentar novamente se ainda há tentativas
      if (attempt < this.retryAttempts) {
        await this.delay(this.retryDelay * attempt);
        return this.executeWithRetry<T>(requestFn, attempt + 1);
      }

      return {
        error: errorResponse,
        status: response.status,
      };

    } catch (error) {
      // Erro de rede - tentar novamente se ainda há tentativas
      if (attempt < this.retryAttempts) {
        await this.delay(this.retryDelay * attempt);
        return this.executeWithRetry<T>(requestFn, attempt + 1);
      }

      return {
        error: {
          detail: error instanceof Error ? error.message : "Erro de conexão",
          type: "NetworkError",
        },
        status: 0,
      };
    }
  }

  /**
   * Delay helper para retry
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Cria um AbortController com timeout específico
   */
  private createAbortController(customTimeout?: number): AbortController {
    const controller = new AbortController();
    const timeoutMs = customTimeout || this.timeout;
    setTimeout(() => controller.abort(), timeoutMs);
    return controller;
  }

  /**
   * Processa PDF via URL
   */
  async extractFromUrl(request: ExtractRequest): Promise<ApiResponse<ProcessData>> {
    // Validar URL de segurança
    if (!isSecureUrl(request.pdf_url)) {
      return {
        error: {
          detail: "URL não é segura para processamento",
          type: "SecurityError",
        },
        status: 400,
      };
    }

    return this.executeWithRetry<ProcessData>(() => {
      const controller = this.createAbortController(API_CONFIG.TIMEOUT_UPLOAD);

      return fetch(`${this.baseUrl}/extract`, {
        method: "POST",
        headers: createSecureHeaders(),
        body: JSON.stringify(request),
        signal: controller.signal,
      });
    });
  }

  /**
   * Inicia upload assíncrono com chunks para arquivos grandes
   */
  async startAsyncUpload(request: UploadRequest): Promise<ApiResponse<{ task_id: string }>> {
    const formData = new FormData();
    formData.append("file", request.file);
    formData.append("case_id", request.case_id);

    return this.executeWithRetry(() => {
      const controller = this.createAbortController();

      return fetch(`${this.baseUrl}/upload/async`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
    });
  }


  /**
   * Verifica status de uma tarefa
   */
  async getTaskStatus(taskId: string): Promise<ApiResponse<any>> {
    return this.executeWithRetry(() => {
      const controller = this.createAbortController();

      return fetch(`${this.baseUrl}/upload/status/${encodeURIComponent(taskId)}`, {
        method: "GET",
        headers: createSecureHeaders(),
        signal: controller.signal,
      });
    });
  }

  /**
   * Processa PDF via upload assíncrono com polling
   */
  async extractFromUpload(
    request: UploadRequest,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<ProcessData>> {
    try {
      // 1. Iniciar upload assíncrono
      if (onProgress) onProgress(10); // Upload iniciado
      
      const uploadResponse = await this.startAsyncUpload(request);
      
      if (uploadResponse.error) {
        return uploadResponse as ApiResponse<ProcessData>;
      }

      const taskId = uploadResponse.data!.task_id;
      if (onProgress) onProgress(25); // Upload concluído, processamento iniciado

      // 2. Polling para acompanhar o progresso
      return await this.pollTaskStatus(taskId, onProgress);
      
    } catch (error) {
      return {
        error: {
          detail: error instanceof Error ? error.message : "Erro durante upload assíncrono",
          type: "AsyncUploadError",
        },
        status: 0,
      };
    }
  }

  /**
   * Faz polling do status da tarefa até completar
   */
  private async pollTaskStatus(
    taskId: string, 
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<ProcessData>> {
    const maxAttempts = 180; // 3 minutos com polling a cada segundo
    let attempts = 0;
    
    while (attempts < maxAttempts) {
      try {
        const statusResponse = await this.getTaskStatus(taskId);
        
        if (statusResponse.error) {
          return statusResponse as ApiResponse<ProcessData>;
        }

        const status = statusResponse.data;
        
        // Atualizar progresso baseado no status
        if (onProgress) {
          const baseProgress = 25; // Upload já concluído
          const processingProgress = Math.min(75, attempts * 2); // Progresso estimado
          onProgress(baseProgress + processingProgress);
        }

        // Verificar se a tarefa foi concluída
        if (status.status === 'completed' && status.result) {
          if (onProgress) onProgress(100);
          return {
            data: status.result as ProcessData,
            status: 200,
          };
        }
        
        // Verificar se houve erro
        if (status.status === 'failed') {
          return {
            error: {
              detail: status.error || "Processamento falhou",
              type: "ProcessingError",
            },
            status: 500,
          };
        }

        // Aguardar antes da próxima verificação
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
        
      } catch (error) {
        // Em caso de erro no polling, tentar novamente
        await new Promise(resolve => setTimeout(resolve, 2000));
        attempts++;
      }
    }

    // Timeout no polling
    return {
      error: {
        detail: "Timeout aguardando processamento completar",
        type: "PollingTimeout",
      },
      status: 408,
    };
  }

  /**
   * Consulta processo existente
   */
  async getProcess(caseId: string): Promise<ApiResponse<ProcessData>> {
    return this.executeWithRetry<ProcessData>(() => {
      const controller = this.createAbortController(API_CONFIG.TIMEOUT_SHORT);

      return fetch(`${this.baseUrl}/extract/${encodeURIComponent(caseId)}`, {
        method: "GET",
        headers: createSecureHeaders(),
        signal: controller.signal,
      });
    });
  }

  /**
   * Health check da API
   */
  async healthCheck(): Promise<ApiResponse<{ status: string; version: string }>> {
    return this.executeWithRetry(() => {
      const controller = this.createAbortController(API_CONFIG.TIMEOUT_HEALTH);

      return fetch(`${this.baseUrl}/health`, {
        method: "GET",
        headers: createSecureHeaders(),
        signal: controller.signal,
      });
    });
  }
}

// Singleton instance
export const apiClient = new ApiClient();
export { ApiError };
