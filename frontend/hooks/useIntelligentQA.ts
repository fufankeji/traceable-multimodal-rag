import { useState } from 'react';
import { apiService } from '../services/api';
import type {
  IntelligentQARequest,
  IntelligentQAResponse,
  QASource,
  QueryType,
  APIError,
} from '../types';

interface UseIntelligentQAReturn {
  answer: string | null;
  sources: QASource[];
  confidence: number;
  queryType: QueryType | null;
  isLoading: boolean;
  error: string | null;
  ask: (question: string, filters?: Record<string, any>, topK?: number) => Promise<void>;
  clearAnswer: () => void;
}

/**
 * Hook for intelligent QA functionality
 * Allows users to ask questions and get direct answers from document metadata
 */
export function useIntelligentQA(): UseIntelligentQAReturn {
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<QASource[]>([]);
  const [confidence, setConfidence] = useState(0);
  const [queryType, setQueryType] = useState<QueryType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async (
    question: string,
    filters?: Record<string, any>,
    topK: number = 3
  ) => {
    console.log('🤖 [useIntelligentQA] 开始问答', { question, filters, topK });

    if (!question.trim()) {
      console.log('⚠️ [useIntelligentQA] 问题为空');
      setError('请输入问题');
      return;
    }

    setIsLoading(true);
    setError(null);
    setAnswer(null);
    setSources([]);
    setConfidence(0);
    setQueryType(null);

    try {
      const request: IntelligentQARequest = {
        question: question.trim(),
        filters,
        top_k: topK,
      };

      console.log('📤 [useIntelligentQA] 发送请求', request);
      const response: IntelligentQAResponse = await apiService.intelligentQA(request);
      console.log('📥 [useIntelligentQA] 收到响应', response);

      setAnswer(response.answer);
      setSources(response.sources);
      setConfidence(response.confidence);
      setQueryType(response.query_type);
    } catch (err) {
      console.error('❌ [useIntelligentQA] 问答失败', err);
      const apiError = err as APIError;
      setError(apiError.message || '问答失败，请稍后重试');
      setAnswer(null);
      setSources([]);
    } finally {
      setIsLoading(false);
      console.log('✓ [useIntelligentQA] 问答完成');
    }
  };

  const clearAnswer = () => {
    setAnswer(null);
    setSources([]);
    setConfidence(0);
    setQueryType(null);
    setError(null);
  };

  return {
    answer,
    sources,
    confidence,
    queryType,
    isLoading,
    error,
    ask,
    clearAnswer,
  };
}
