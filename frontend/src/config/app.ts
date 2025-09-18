/**
 * Configuração centralizada da aplicação
 */

// Configurações da API
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL ||
    (import.meta.env.MODE === "production"
      ? import.meta.env.VITE_API_BASE_URL_PRODUCTION || "https://localhost:8000"
      : import.meta.env.VITE_API_BASE_URL_DEVELOPMENT || "http://localhost:8000"),
  TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT) || 1800000, // 30 minutos (1800000ms) para arquivos grandes
  TIMEOUT_SHORT: Number(import.meta.env.VITE_API_TIMEOUT_SHORT) || 30000, // 30 segundos para operações rápidas
  TIMEOUT_UPLOAD: Number(import.meta.env.VITE_API_TIMEOUT_UPLOAD) || 1800000, // 30 minutos para uploads
  TIMEOUT_HEALTH: Number(import.meta.env.VITE_API_TIMEOUT_HEALTH) || 5000, // 5 segundos para health check
  RETRY_ATTEMPTS: Number(import.meta.env.VITE_API_RETRY_ATTEMPTS) || 3,
  RETRY_DELAY: Number(import.meta.env.VITE_API_RETRY_DELAY) || 1000, // 1 segundo
} as const;

// Configurações de upload
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE: Number(import.meta.env.VITE_MAX_FILE_SIZE) || (14 * 1024 * 1024), // 14MB em bytes
  ALLOWED_TYPES: (import.meta.env.VITE_ALLOWED_TYPES?.split(',') as readonly string[]) || ["application/pdf"] as const,
  ALLOWED_EXTENSIONS: (import.meta.env.VITE_ALLOWED_EXTENSIONS?.split(',') as readonly string[]) || [".pdf"] as const,
} as const;

// Configurações da aplicação
export const APP_CONFIG = {
  NAME: import.meta.env.VITE_APP_NAME || "PDF.AI",
  DESCRIPTION: import.meta.env.VITE_APP_DESCRIPTION || "Transforme PDFs Jurídicos em Insights com IA",
  VERSION: import.meta.env.VITE_APP_VERSION || "1.0.0",
  MAX_RETRIES: Number(import.meta.env.VITE_APP_MAX_RETRIES) || 3,
} as const;

// Configurações de validação
export const VALIDATION_CONFIG = {
  MIN_URL_LENGTH: Number(import.meta.env.VITE_MIN_URL_LENGTH) || 10,
  MAX_URL_LENGTH: Number(import.meta.env.VITE_MAX_URL_LENGTH) || 2048,
  MAX_CASE_ID_LENGTH: Number(import.meta.env.VITE_MAX_CASE_ID_LENGTH) || 100,
  URL_PATTERNS: {
    HTTP: /^https?:\/\/.+/i,
    PDF_URL: /^https?:\/\/.+\.pdf(\?.*)?$/i,
  },
} as const;

// Environment checks
export const IS_DEVELOPMENT = import.meta.env.MODE === "development";
export const IS_PRODUCTION = import.meta.env.MODE === "production";

// Feature flags
export const FEATURES = {
  DEBUG_MODE: IS_DEVELOPMENT,
  ERROR_REPORTING: IS_PRODUCTION,
  ANALYTICS: IS_PRODUCTION,
} as const;
