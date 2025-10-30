import type {
  SearchRequest,
  SearchResponse,
  UploadRequest,
  UploadResponse,
  FollowUpQuestionRequest,
  FollowUpQuestionResponse,
  SearchResult,
} from '../types';

/**
 * Mock API Service for development/testing
 * This simulates backend responses with mock data
 */

// Mock search results
const mockResults: SearchResult[] = [
  {
    id: "1",
    fileName: "MotorBracket_v1.2.dwg",
    filePath: "/工程制造/机械零件/电机支架/v1.2/",
    fileType: "CAD",
    similarity: 87,
    page: "View A",
    date: "2025-09-21",
    snippet:
      "孔径 Ø8mm；中心距 42mm；材质 6061-T6；适用于标准电机安装，符合 GB/T 规范要求。",
    citationNumber: 1,
    thumbnailType: "cad",
    version: "v1.2",
    structuredData: [
      { label: "孔径", value: "Ø8mm" },
      { label: "中心距", value: "42mm" },
      { label: "材质", value: "6061-T6" },
      { label: "公差等级", value: "IT7" },
    ],
  },
  {
    id: "2",
    fileName: "PlantFlow_v3_arch.pdf",
    filePath: "/研发架构/系统架构图/2025Q3/",
    fileType: "流程图",
    similarity: 82,
    page: "Page 12",
    date: "2025-08-15",
    snippet:
      "消息队列模块采用 Kafka 架构，处理实时数据流，支持高并发场景下的异步通信。",
    citationNumber: 2,
    thumbnailType: "pdf",
    version: "v3.0",
    structuredData: [
      { label: "模块", value: "消息队列" },
      { label: "技术栈", value: "Apache Kafka" },
      { label: "吞吐量", value: "100k msg/s" },
      { label: "部署模式", value: "分布式集群" },
    ],
  },
  {
    id: "3",
    fileName: "Assembly_BOM_2025Q3.xlsx",
    filePath: "/工业档案/装配清单/2025/Q3/",
    fileType: "BOM",
    similarity: 78,
    page: "Sheet 2",
    date: "2025-07-10",
    snippet:
      "装配清单包含 156 个零部件，主要材料为铝合金与不锈钢，总成本预算 ¥245,600。",
    citationNumber: 3,
    thumbnailType: "image",
    version: "2025Q3",
    structuredData: [
      { label: "零件数量", value: "156个" },
      { label: "主材料", value: "铝合金/不锈钢" },
      { label: "总成本", value: "¥245,600" },
      { label: "周期", value: "2025Q3" },
    ],
  },
];

// Simulate network delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

class MockAPIService {
  /**
   * Mock search implementation
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    await delay(800); // Simulate network latency

    // Filter results based on query (simple contains check)
    let results = mockResults;
    if (request.query) {
      const queryLower = request.query.toLowerCase();
      results = mockResults.filter(
        (result) =>
          result.fileName.toLowerCase().includes(queryLower) ||
          result.snippet.toLowerCase().includes(queryLower) ||
          result.fileType.toLowerCase().includes(queryLower)
      );
    }

    // Apply topK limit
    const topK = request.topK || 10;
    results = results.slice(0, topK);

    return {
      results,
      totalCount: results.length,
      queryTime: 823,
      model: request.model,
      strategy: request.strategy,
    };
  }

  /**
   * Mock upload implementation
   */
  async uploadDocument(request: UploadRequest): Promise<UploadResponse> {
    await delay(1500); // Simulate upload time

    return {
      success: true,
      fileId: `mock-${Date.now()}`,
      fileName: request.file.name,
      message: "文件上传成功（模拟）",
    };
  }

  /**
   * Mock follow-up question implementation
   */
  async askFollowUpQuestion(
    request: FollowUpQuestionRequest
  ): Promise<FollowUpQuestionResponse> {
    await delay(600);

    const mockAnswers = [
      `根据图纸分析，中心距为 42mm，符合 v1.2 工艺规范要求（40-45mm）。[1]`,
      `该组件的材质为 6061-T6 铝合金，具有良好的强度和耐腐蚀性。[1]`,
      `消息队列模块采用 Kafka 架构，吞吐量可达 100k msg/s，适用于高并发场景。[2]`,
      `装配清单中共包含 156 个零部件，主要材料为铝合金与不锈钢。[3]`,
    ];

    return {
      answer: mockAnswers[Math.floor(Math.random() * mockAnswers.length)],
      citations: [1],
      confidence: 0.85 + Math.random() * 0.15,
    };
  }

  /**
   * Mock preview URL
   */
  getPreviewUrl(documentId: string): string {
    return `/mock-preview/${documentId}`;
  }

  /**
   * Mock thumbnail URL
   */
  getThumbnailUrl(documentId: string): string {
    return `/mock-thumbnail/${documentId}`;
  }

  /**
   * Mock download (just logs to console)
   */
  async downloadDocument(documentId: string, fileName: string): Promise<void> {
    await delay(500);
    console.log(`[Mock] Downloading document: ${fileName} (ID: ${documentId})`);
    alert(`模拟下载: ${fileName}`);
  }

  /**
   * Mock health check
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    await delay(100);
    return {
      status: "ok (mock)",
      timestamp: new Date().toISOString(),
    };
  }
}

// Export singleton instance
export const mockApiService = new MockAPIService();
