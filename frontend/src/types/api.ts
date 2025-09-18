/**
 * Tipos TypeScript para a API
 */

// Request Types
export interface ExtractRequest {
  pdf_url: string;
  case_id: string;
}

export interface UploadRequest {
  file: File;
  case_id: string;
}

// Response Types
export interface TimelineEvent {
  event_id: number;
  event_name: string;
  event_description: string;
  event_date: string;
  event_page_init: number;
  event_page_end: number;
}

export interface Evidence {
  evidence_id: number;
  evidence_name: string;
  evidence_flaw: string | null;
  evidence_page_init: number;
  evidence_page_end: number;
}

export interface ProcessData {
  case_id: string;
  resume: string;
  timeline: TimelineEvent[];
  evidence: Evidence[];
  persisted_at: string;
}

export interface ApiErrorResponse {
  detail: string;
  type?: string;
  code?: string;
}

// API Response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: ApiErrorResponse;
  status: number;
}

// Processing states
export type ProcessingState = "idle" | "validating" | "uploading" | "processing" | "polling" | "completed" | "error";

// Upload progress
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// File validation result
export interface FileValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// API client configuration
export interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}
