/**
 * Utilitários de segurança para o frontend
 */

import { VALIDATION_CONFIG, UPLOAD_CONFIG } from "@/config/app";
import type { FileValidationResult } from "@/types/api";

/**
 * Gera um ID seguro e único para casos
 */
export function generateSecureCaseId(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  const uuid = crypto.randomUUID ? crypto.randomUUID().substring(0, 8) : random;

  return `case_${timestamp}_${uuid}`;
}

/**
 * Valida uma URL de forma segura
 */
export function validateUrl(url: string): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!url || typeof url !== "string") {
    errors.push("URL é obrigatória");
    return { isValid: false, errors };
  }

  const trimmedUrl = url.trim();

  if (trimmedUrl.length < VALIDATION_CONFIG.MIN_URL_LENGTH) {
    errors.push("URL muito curta");
  }

  if (trimmedUrl.length > VALIDATION_CONFIG.MAX_URL_LENGTH) {
    errors.push("URL muito longa");
  }

  if (!VALIDATION_CONFIG.URL_PATTERNS.HTTP.test(trimmedUrl)) {
    errors.push("URL deve começar com http:// ou https://");
  }

  try {
    new URL(trimmedUrl);
  } catch {
    errors.push("Formato de URL inválido");
  }

  return { isValid: errors.length === 0, errors };
}

/**
 * Valida um arquivo de upload de forma segura
 */
export function validateFile(file: File): FileValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!file) {
    errors.push("Arquivo é obrigatório");
    return { isValid: false, errors, warnings };
  }

  // Validar tipo MIME
  if (!UPLOAD_CONFIG.ALLOWED_TYPES.includes(file.type as any)) {
    errors.push("Apenas arquivos PDF são permitidos");
  }

  // Validar extensão
  const extension = file.name.toLowerCase().substring(file.name.lastIndexOf("."));
  if (!UPLOAD_CONFIG.ALLOWED_EXTENSIONS.includes(extension as any)) {
    errors.push("Extensão de arquivo não permitida");
  }

  // Validar tamanho
  if (file.size > UPLOAD_CONFIG.MAX_FILE_SIZE) {
    const maxSizeMB = UPLOAD_CONFIG.MAX_FILE_SIZE / (1024 * 1024);
    errors.push(`Arquivo muito grande. Máximo permitido: ${maxSizeMB}MB`);
  }

  // Validar nome do arquivo
  if (file.name.length > 255) {
    errors.push("Nome do arquivo muito longo");
  }

  // Verificar caracteres perigosos no nome
  const dangerousChars = /[<>:"/\\|?*\x00-\x1f]/;
  if (dangerousChars.test(file.name)) {
    warnings.push("Nome do arquivo contém caracteres especiais");
  }

  // Verificar se o arquivo está vazio
  if (file.size === 0) {
    errors.push("Arquivo está vazio");
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}

/**
 * Sanitiza uma string para prevenir XSS
 */
export function sanitizeString(input: string): string {
  if (!input || typeof input !== "string") {
    return "";
  }

  return input
    .replace(/[<>]/g, "") // Remove < e >
    .replace(/javascript:/gi, "") // Remove javascript:
    .replace(/on\w+=/gi, "") // Remove event handlers
    .trim();
}

/**
 * Valida um case_id
 */
export function validateCaseId(caseId: string): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!caseId || typeof caseId !== "string") {
    errors.push("Case ID é obrigatório");
    return { isValid: false, errors };
  }

  const trimmed = caseId.trim();

  if (trimmed.length === 0) {
    errors.push("Case ID não pode estar vazio");
  }

  if (trimmed.length > VALIDATION_CONFIG.MAX_CASE_ID_LENGTH) {
    errors.push("Case ID muito longo");
  }

  // Permitir apenas caracteres alfanuméricos, hífens e underscores
  const validPattern = /^[a-zA-Z0-9_-]+$/;
  if (!validPattern.test(trimmed)) {
    errors.push("Case ID contém caracteres inválidos");
  }

  return { isValid: errors.length === 0, errors };
}

/**
 * Cria headers seguros para requisições
 */
export function createSecureHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest", // Proteção CSRF básica
    "Cache-Control": "no-cache",
  };
}

/**
 * Verifica se uma URL é segura para requisição
 */
export function isSecureUrl(url: string): boolean {
  try {
    const urlObj = new URL(url);

    // Apenas HTTPS em produção
    if (import.meta.env.PROD && urlObj.protocol !== "https:") {
      return false;
    }

    // Bloquear URLs locais em produção
    if (import.meta.env.PROD) {
      const hostname = urlObj.hostname;
      if (
        hostname === "localhost" ||
        hostname === "127.0.0.1" ||
        hostname.startsWith("192.168.") ||
        hostname.startsWith("10.") ||
        hostname.startsWith("172.")
      ) {
        return false;
      }
    }

    return true;
  } catch {
    return false;
  }
}
