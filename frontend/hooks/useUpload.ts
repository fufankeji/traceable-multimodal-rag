import { useState } from 'react';
import { service } from '../services';
import type { UploadRequest, UploadResponse, APIError } from '../types';

interface UseUploadReturn {
  isUploading: boolean;
  error: string | null;
  uploadProgress: number;
  uploadDocument: (file: File, metadata?: UploadRequest['metadata']) => Promise<UploadResponse | null>;
  clearError: () => void;
}

/**
 * Hook for document upload functionality
 */
export function useUpload(): UseUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadDocument = async (
    file: File,
    metadata?: UploadRequest['metadata']
  ): Promise<UploadResponse | null> => {
    // Validate file
    if (!file) {
      setError('请选择要上传的文件');
      return null;
    }

    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('文件大小不能超过 50MB');
      return null;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const request: UploadRequest = {
        file,
        metadata,
      };

      // Simulate upload progress (in real implementation, use axios onUploadProgress)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const response = await service.uploadDocument(request);

      clearInterval(progressInterval);
      setUploadProgress(100);

      return response;
    } catch (err) {
      const apiError = err as APIError;
      setError(apiError.message || '上传失败，请稍后重试');
      return null;
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  const clearError = () => {
    setError(null);
  };

  return {
    isUploading,
    error,
    uploadProgress,
    uploadDocument,
    clearError,
  };
}
