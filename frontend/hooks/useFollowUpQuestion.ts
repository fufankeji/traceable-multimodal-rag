import { useState } from 'react';
import { service } from '../services';
import type {
  FollowUpQuestionRequest,
  FollowUpQuestionResponse,
  QAHistoryItem,
  VLMModel,
  APIError,
} from '../types';

interface UseFollowUpQuestionReturn {
  qaHistory: QAHistoryItem[];
  isAsking: boolean;
  error: string | null;
  askQuestion: (documentId: string, question: string, model: VLMModel) => Promise<void>;
  clearHistory: () => void;
}

/**
 * Hook for follow-up questions on documents
 */
export function useFollowUpQuestion(): UseFollowUpQuestionReturn {
  const [qaHistory, setQaHistory] = useState<QAHistoryItem[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const askQuestion = async (
    documentId: string,
    question: string,
    model: VLMModel
  ) => {
    if (!question.trim()) {
      setError('请输入问题');
      return;
    }

    setIsAsking(true);
    setError(null);

    try {
      const request: FollowUpQuestionRequest = {
        documentId,
        question: question.trim(),
        model,
      };

      const response: FollowUpQuestionResponse = await service.askFollowUpQuestion(
        request
      );

      // Add to history
      const newQA: QAHistoryItem = {
        question: question.trim(),
        answer: response.answer,
        timestamp: new Date().toISOString(),
      };

      setQaHistory((prev) => [...prev, newQA]);
    } catch (err) {
      const apiError = err as APIError;
      setError(apiError.message || '提问失败，请稍后重试');
    } finally {
      setIsAsking(false);
    }
  };

  const clearHistory = () => {
    setQaHistory([]);
    setError(null);
  };

  return {
    qaHistory,
    isAsking,
    error,
    askQuestion,
    clearHistory,
  };
}
