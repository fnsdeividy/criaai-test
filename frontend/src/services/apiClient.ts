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
   * Cria um AbortController com timeout
   */
  private createAbortController(): AbortController {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), this.timeout);
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
      const controller = this.createAbortController();

      return fetch(`${this.baseUrl}/extract`, {
        method: "POST",
        headers: createSecureHeaders(),
        body: JSON.stringify(request),
        signal: controller.signal,
      });
    });
  }

  /**
   * Processa PDF via upload
   */
  async extractFromUpload(
    request: UploadRequest,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<ProcessData>> {
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();

      formData.append("file", request.file);
      formData.append("case_id", request.case_id);

      // Progress tracking
      if (onProgress) {
        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            onProgress(progress);
          }
        });
      }

      xhr.timeout = this.timeout;

      xhr.addEventListener("load", () => {
        try {
          if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            resolve({
              data: data as ProcessData,
              status: xhr.status,
            });
          } else {
            let errorResponse: ApiErrorResponse;
            try {
              errorResponse = JSON.parse(xhr.responseText);
            } catch {
              errorResponse = {
                detail: `HTTP ${xhr.status}: ${xhr.statusText}`,
              };
            }

            resolve({
              error: errorResponse,
              status: xhr.status,
            });
          }
        } catch (error) {
          resolve({
            error: {
              detail: "Erro ao processar resposta do servidor",
              type: "ParseError",
            },
            status: xhr.status,
          });
        }
      });

      xhr.addEventListener("error", () => {
        resolve({
          error: {
            detail: "Erro de conexão durante upload",
            type: "NetworkError",
          },
          status: 0,
        });
      });

      xhr.addEventListener("timeout", () => {
        resolve({
          error: {
            detail: "Timeout durante upload",
            type: "TimeoutError",
          },
          status: 0,
        });
      });

      xhr.open("POST", `${this.baseUrl}/upload`);
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      xhr.send(formData);
    });
  }

  /**
   * Consulta processo existente
   */
  async getProcess(caseId: string): Promise<ApiResponse<ProcessData>> {
    return this.executeWithRetry<ProcessData>(() => {
      const controller = this.createAbortController();

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
      const controller = this.createAbortController();

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
