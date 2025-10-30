/**
 * Core data types for the Multimodal RAG application
 */

// VLM Model types supported by the backend
export type VLMModel = "gpt-4o" | "qwen-vl" | "intern-vl";

// Retrieval strategy types
export type RetrievalStrategy = "vector" | "hybrid" | "two-stage";

// File type classifications
export type FileType = "CAD" | "PDF" | "流程图" | "BOM" | "架构图" | "工程图纸" | "其他";

// Thumbnail display types
export type ThumbnailType = "cad" | "pdf" | "image";

// Structured data extracted from documents
export interface StructuredData {
  label: string;
  value: string;
}

// Main search result interface
export interface SearchResult {
  id: string;
  fileName: string;
  filePath: string;
  fileType: FileType;
  similarity: number;
  page?: string;
  date: string;
  snippet: string;
  citationNumber: number;
  thumbnailType: ThumbnailType;
  thumbnailUrl?: string;  // URL to actual thumbnail image
  previewUrl?: string;    // URL to full document preview
  version: string;
  structuredData: StructuredData[];
}

// Search request payload
export interface SearchRequest {
  query: string;
  model: VLMModel;
  strategy: RetrievalStrategy;
  topK?: number;          // Number of results to return
  minSimilarity?: number; // Minimum similarity threshold (0-1), default 0.3
  filters?: SearchFilters;
}

// Optional search filters
export interface SearchFilters {
  fileTypes?: FileType[];
  dateRange?: {
    start: string;
    end: string;
  };
  minSimilarity?: number;
  tags?: string[];
}

// Search response from backend
export interface SearchResponse {
  results: SearchResult[];
  totalCount: number;
  queryTime: number;      // Time taken in milliseconds
  model: VLMModel;
  strategy: RetrievalStrategy;
}

// Document upload request
export interface UploadRequest {
  file: File;
  metadata?: {
    tags?: string[];
    category?: string;
    description?: string;
  };
}

// Document upload response
export interface UploadResponse {
  success: boolean;
  fileId: string;
  fileName: string;
  message?: string;
}

// Follow-up question on a specific document
export interface FollowUpQuestionRequest {
  documentId: string;
  question: string;
  model: VLMModel;
}

// Follow-up question response
export interface FollowUpQuestionResponse {
  answer: string;
  citations: number[];    // Reference to citation numbers
  confidence: number;
}

// Q&A history item
export interface QAHistoryItem {
  question: string;
  answer: string;
  timestamp: string;
}

// Empty state types
export type EmptyStateType = "initial" | "no-results";

// API Error response
export interface APIError {
  error: string;
  message: string;
  statusCode: number;
}

// Intelligent QA types
export type QueryType = "exact_query" | "filter_query" | "general_query";

// Intelligent QA request
export interface IntelligentQARequest {
  question: string;
  filters?: Record<string, any>;
  top_k?: number;
}

// Source information in QA response
export interface QASource {
  file_id: string;
  file_name: string;
  file_type: string;
  similarity: number;
  chunk_text?: string;
  extracted_info?: Record<string, any>;
}

// Intelligent QA response
export interface IntelligentQAResponse {
  answer: string;
  sources: QASource[];
  confidence: number;
  query_type: QueryType;
}
