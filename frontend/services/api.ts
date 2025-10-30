import axios, { AxiosInstance } from 'axios';
import type {
  SearchRequest,
  SearchResponse,
  UploadRequest,
  UploadResponse,
  FollowUpQuestionRequest,
  FollowUpQuestionResponse,
  IntelligentQARequest,
  IntelligentQAResponse,
  APIError,
} from '../types';

/**
 * API Service for Multimodal RAG Backend
 *
 * Base URL: /api (proxied to backend server via Vite config)
 * Backend should be running on http://localhost:8000
 */

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const apiError: APIError = {
          error: error.response?.data?.error || 'Unknown error',
          message: error.response?.data?.message || error.message,
          statusCode: error.response?.status || 500,
        };
        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Search for documents using natural language query
   *
   * POST /api/search
   *
   * Request body:
   * {
   *   "query": "查询电机支架 CAD 的孔径与中心距",
   *   "model": "gpt-4o",
   *   "strategy": "hybrid",
   *   "topK": 10,
   *   "filters": { ... }
   * }
   *
   * Response:
   * {
   *   "results": [...],
   *   "totalCount": 10,
   *   "queryTime": 1234,
   *   "model": "gpt-4o",
   *   "strategy": "hybrid"
   * }
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    console.log('[API] 调用 /search 接口', request);
    try {
      const response = await this.client.post<SearchResponse>('/search', request);
      console.log('[API] /search 响应成功', response.data);
      return response.data;
    } catch (error) {
      console.error('[API] /search 请求失败', error);
      throw error;
    }
  }

  /**
   * Upload a document (image, CAD file, PDF, etc.)
   *
   * POST /api/upload
   * Content-Type: multipart/form-data
   *
   * Form data:
   * - file: File
   * - metadata: JSON string (optional)
   *
   * Response:
   * {
   *   "success": true,
   *   "fileId": "abc123",
   *   "fileName": "drawing.dwg",
   *   "message": "File uploaded successfully"
   * }
   */
  async uploadDocument(request: UploadRequest): Promise<UploadResponse> {
    console.log('[API] 调用 /upload 接口', { fileName: request.file.name, fileSize: request.file.size, metadata: request.metadata });

    const formData = new FormData();
    formData.append('file', request.file);

    if (request.metadata) {
      formData.append('metadata', JSON.stringify(request.metadata));
    }

    try {
      const response = await this.client.post<UploadResponse>('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('[API] /upload 响应成功', response.data);
      return response.data;
    } catch (error) {
      console.error('[API] /upload 请求失败', error);
      throw error;
    }
  }

  /**
   * Ask a follow-up question about a specific document
   *
   * POST /api/question
   *
   * Request body:
   * {
   *   "documentId": "abc123",
   *   "question": "中心距是否满足 v1.2 工艺规范？",
   *   "model": "gpt-4o"
   * }
   *
   * Response:
   * {
   *   "answer": "根据图纸分析，中心距为 42mm，符合 v1.2 工艺规范要求（40-45mm）。",
   *   "citations": [1],
   *   "confidence": 0.95
   * }
   */
  async askFollowUpQuestion(
    request: FollowUpQuestionRequest
  ): Promise<FollowUpQuestionResponse> {
    const response = await this.client.post<FollowUpQuestionResponse>(
      '/question',
      request
    );
    return response.data;
  }

  /**
   * Intelligent QA - Ask a question and get direct answers
   *
   * POST /api/ask
   *
   * Request body:
   * {
   *   "question": "这张图中有几个卧室？",
   *   "filters": { ... },
   *   "top_k": 3
   * }
   *
   * Response:
   * {
   *   "answer": "这张平面布置图有3个卧室：主卧、次卧、儿童房",
   *   "sources": [...],
   *   "confidence": 0.95,
   *   "query_type": "exact_query"
   * }
   */
  async intelligentQA(request: IntelligentQARequest): Promise<IntelligentQAResponse> {
    console.log('[API] 调用 /ask 接口', request);
    try {
      const response = await this.client.post<IntelligentQAResponse>('/ask', request);
      console.log('[API] /ask 响应成功', response.data);
      return response.data;
    } catch (error) {
      console.error('[API] /ask 请求失败', error);
      throw error;
    }
  }

  /**
   * Get document preview/thumbnail
   *
   * GET /api/preview/{documentId}
   *
   * Returns: Image URL or Base64 encoded image
   */
  getPreviewUrl(documentId: string): string {
    return `${this.client.defaults.baseURL}/preview/${documentId}`;
  }

  /**
   * Get document thumbnail
   *
   * GET /api/thumbnail/{documentId}
   *
   * Returns: Image URL or Base64 encoded thumbnail
   */
  getThumbnailUrl(documentId: string): string {
    return `${this.client.defaults.baseURL}/thumbnail/${documentId}`;
  }

  /**
   * Download original document
   *
   * GET /api/download/{documentId}
   */
  async downloadDocument(documentId: string, fileName: string): Promise<void> {
    const response = await this.client.get(`/download/${documentId}`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  /**
   * Health check endpoint
   *
   * GET /api/health
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const apiService = new APIService();
