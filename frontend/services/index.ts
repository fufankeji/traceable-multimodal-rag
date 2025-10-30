/**
 * Service layer exports
 *
 * Toggle between real API and mock API using environment variable
 */

import { apiService } from './api';
import { mockApiService } from './mockApi';

// Check if we should use mock API (for development/testing)
const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === 'true';

console.log('[Service] USE_MOCK_API =', USE_MOCK_API);
console.log('[Service] Using:', USE_MOCK_API ? 'mockApiService' : 'apiService (REAL BACKEND)');

// Export the appropriate service based on configuration
// FORCE USE REAL API - 强制使用真实后端
export const service = apiService;  // 直接使用真实API，不使用mock

// Also export individual services for explicit use
export { apiService, mockApiService };
