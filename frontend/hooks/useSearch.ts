import { useState } from 'react';
import { service } from '../services';
import type {
  SearchRequest,
  SearchResponse,
  SearchResult,
  VLMModel,
  RetrievalStrategy,
  APIError,
} from '../types';

interface UseSearchReturn {
  results: SearchResult[];
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  queryTime: number;
  search: (query: string, model: VLMModel, strategy: RetrievalStrategy) => Promise<void>;
  clearResults: () => void;
}

/**
 * Hook for document search functionality
 */
export function useSearch(): UseSearchReturn {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [queryTime, setQueryTime] = useState(0);

  const search = async (
    query: string,
    model: VLMModel,
    strategy: RetrievalStrategy
  ) => {
    console.log('🔍 [useSearch] 开始搜索', { query, model, strategy });

    if (!query.trim()) {
      console.log('⚠️ [useSearch] 搜索关键词为空');
      setError('请输入搜索关键词');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: SearchRequest = {
        query: query.trim(),
        model,
        strategy,
        topK: 10,
        minSimilarity: 0.48,  // 相似度阈值 0.48，只返回高质量结果（使用倒数归一化：1/(1+distance)）
      };

      console.log('📤 [useSearch] 发送请求', request);
      const response: SearchResponse = await service.search(request);
      console.log('📥 [useSearch] 收到响应', response);

      setResults(response.results);
      setTotalCount(response.totalCount);
      setQueryTime(response.queryTime);
    } catch (err) {
      console.error('❌ [useSearch] 搜索失败', err);
      const apiError = err as APIError;
      setError(apiError.message || '搜索失败，请稍后重试');
      setResults([]);
    } finally {
      setIsLoading(false);
      console.log('✓ [useSearch] 搜索完成');
    }
  };

  const clearResults = () => {
    setResults([]);
    setError(null);
    setTotalCount(0);
    setQueryTime(0);
  };

  return {
    results,
    isLoading,
    error,
    totalCount,
    queryTime,
    search,
    clearResults,
  };
}
