"""
多模态 RAG 主服务
整合 PDF 解析、图像分析、向量检索功能，对接前端API
"""
import os
import sys
import uuid
import asyncio
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import shutil
import time

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件

# ============ 配置日志系统 ============
# 简单的日志配置，直接输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)

# 创建应用日志记录器
logger = logging.getLogger("RAG_Service")

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# 添加项目路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "Information-Extraction"))
sys.path.insert(0, str(backend_path / "image_analysis"))

# 导入现有模块
from simple_vlm_analyzer import SimpleVLMAnalyzer, ImageType
from unified.unified_pdf_extraction_service import PDFExtractionService
from qwen_embeddings import QwenEmbeddings
from simple_logger import log_request

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


# ============ 数据模型 ============

class VLMModel:
    GPT_4O = "gpt-4o"
    QWEN_VL = "qwen-vl"
    INTERN_VL = "intern-vl"


class RetrievalStrategy:
    VECTOR = "vector"
    HYBRID = "hybrid"
    TWO_STAGE = "two-stage"


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    model: str = VLMModel.GPT_4O
    strategy: str = RetrievalStrategy.HYBRID
    topK: int = 10
    minSimilarity: float = 0.0  # 最小相似度阈值（0-1），默认0.0（不过滤）
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """搜索结果"""
    id: str
    fileName: str
    filePath: str
    fileType: str
    similarity: float
    page: Optional[str] = None
    date: str
    snippet: str
    citationNumber: int
    thumbnailType: str
    thumbnailUrl: Optional[str] = None
    previewUrl: Optional[str] = None
    version: str
    structuredData: List[Dict[str, str]]


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[SearchResult]
    totalCount: int
    queryTime: float
    model: str
    strategy: str


class UploadResponse(BaseModel):
    """上传响应"""
    success: bool
    fileId: str
    fileName: str
    message: Optional[str] = None
    detectedImageType: Optional[str] = None  # 检测到的图片类型


class FollowUpQuestionRequest(BaseModel):
    """追问请求"""
    documentId: str
    question: str
    model: str = VLMModel.GPT_4O


class FollowUpQuestionResponse(BaseModel):
    """追问响应"""
    answer: str
    citations: List[int]
    confidence: float


class IntelligentQARequest(BaseModel):
    """智能问答请求"""
    question: str
    filters: Optional[Dict[str, Any]] = None  # 可选的过滤条件
    top_k: int = 3


class IntelligentQAResponse(BaseModel):
    """智能问答响应"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query_type: str  # exact_query, filter_query, general_query


# ============ 向量数据库管理器 ============

class VectorStoreManager:
    """向量数据库管理器 - 使用 ChromaDB"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """初始化向量数据库"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        # 根据配置选择 Embedding 模型
        logger.info("初始化 Embedding 模型...")
        embedding_type = os.getenv("EMBEDDING_TYPE", "huggingface").lower()

        if embedding_type == "qwen":
            # 使用通义千问 Embedding
            logger.info("  使用通义千问 text-embedding-v4")
            self.embeddings = QwenEmbeddings(
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-v4"),
                dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
            )
        else:
            # 使用 HuggingFace Embedding（默认，离线可用）
            print("  使用 HuggingFace Embedding")
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

        # 初始化 Chroma
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name="multimodal_rag"
        )

        # 文本分割器
        chunk_size = int(os.getenv("CHUNK_SIZE", "300"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )

        logger.info(f"✓ 向量数据库初始化完成")
        logger.info(f"  Embedding类型: {embedding_type}")
        logger.info(f"  分块大小: {chunk_size}, 重叠: {chunk_overlap}")

    async def add_document(
        self,
        file_id: str,
        file_name: str,
        file_type: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> int:
        """添加文档到向量库"""
        print(f"\n📥 添加文档到向量库: {file_name}")

        # 分割文本
        chunks = self.text_splitter.split_text(content)
        logger.info(f"  分割为 {len(chunks)} 个文本块")

        # 创建 Document 对象
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = {
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "chunk_id": i,
                "total_chunks": len(chunks),
                "upload_date": datetime.now().isoformat(),
                **metadata
            }

            documents.append(Document(
                page_content=chunk,
                metadata=doc_metadata
            ))

        # 添加到向量库
        ids = [f"{file_id}_chunk_{i}" for i in range(len(documents))]
        self.vector_store.add_documents(documents, ids=ids)

        logger.info(f"✓ 文档已添加到向量库，共 {len(documents)} 个块")
        return len(documents)

    async def search(
        self,
        query: str,
        top_k: int = 10,
        file_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        print(f"\n🔍 执行向量检索: {query[:50]}...")

        # 构建过滤器
        where_filter = {}
        if file_type_filter:
            where_filter["file_type"] = file_type_filter

        # 执行检索
        if where_filter:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k,
                filter=where_filter
            )
        else:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k
            )

        # 格式化结果
        formatted_results = []
        for doc, score in results:
            # ChromaDB 使用 L2 (欧几里得距离) 或余弦距离
            # L2 距离范围可能很大，余弦距离范围是 [0, 2]
            #
            # 方案1：使用倒数归一化（适用于各种距离度量）
            # similarity = 1 / (1 + distance)
            #
            # 方案2：余弦距离转相似度
            # similarity = 1 - (distance / 2)
            #
            # 我们使用方案1，因为它对任何距离都有效
            similarity = 1.0 / (1.0 + score)  # 距离越小，相似度越高

            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity": float(similarity),
                "distance": float(score)  # 保留原始距离用于调试
            })

        logger.info(f"✓ 找到 {len(formatted_results)} 个相关结果")

        # 【调试】显示距离和相似度的对应关系
        if formatted_results:
            logger.info(f"  距离范围: {min(r['distance'] for r in formatted_results):.4f} ~ {max(r['distance'] for r in formatted_results):.4f}")
            logger.info(f"  相似度范围: {min(r['similarity'] for r in formatted_results):.4f} ~ {max(r['similarity'] for r in formatted_results):.4f}")

        return formatted_results


# ============ 主服务类 ============

class MultimodalRAGService:
    """多模态 RAG 主服务"""

    def __init__(self):
        """初始化服务"""
        # 初始化各个组件
        self.pdf_service = PDFExtractionService()
        self.vector_manager = VectorStoreManager()

        # VLM 配置（从环境变量读取）
        self.vlm_model_url = os.getenv("VLM_MODEL_URL", None)
        self.vlm_api_key = os.getenv("VLM_API_KEY", None)
        self.vlm_model_name = os.getenv("VLM_MODEL_NAME", "gpt-4o")

        # 初始化 VLM 分析器
        self.vlm_analyzer = SimpleVLMAnalyzer(
            model_url=self.vlm_model_url,
            api_key=self.vlm_api_key,
            model_name=self.vlm_model_name
        )

        # 文件存储目录
        self.upload_dir = Path("./uploads")
        self.upload_dir.mkdir(exist_ok=True)

        # 预览图存储
        self.preview_dir = Path("./previews")
        self.preview_dir.mkdir(exist_ok=True)

        print("✓ 服务初始化完成")
        print("="*60 + "\n")

    def _format_extracted_info_to_natural_language(self, info: Dict[str, Any]) -> str:
        """将结构化信息转换为自然语言"""
        if not info:
            return ""

        lines = []

        # 总体尺寸
        if "total_dimensions" in info:
            dims = info["total_dimensions"]
            lines.append(
                f"建筑总长度{dims.get('length', 0)}米，"
                f"总宽度{dims.get('width', 0)}米，"
                f"总面积{dims.get('total_area', 0)}平方米。"
            )

        # 房间信息
        if "rooms" in info and info["rooms"]:
            room_count = len(info["rooms"])
            lines.append(f"\n该平面图共有{room_count}个房间：")

            for room in info["rooms"]:
                parts = [f"- {room.get('name', '未命名房间')}"]

                if "position" in room:
                    parts.append(f"位于{room['position']}")

                if "dimensions" in room and "area" in room["dimensions"]:
                    parts.append(f"，面积{room['dimensions']['area']}平方米")

                if "furniture" in room and room["furniture"]:
                    parts.append(f"，配有{' '.join(room['furniture'])}")

                lines.append("".join(parts))

        # 动线信息
        if "circulation" in info:
            circ = info["circulation"]
            if "main_path" in circ:
                lines.append(f"\n动线设计：{circ['main_path']}")
            if "layout_type" in circ:
                lines.append(f"布局类型：{circ['layout_type']}")

        # CAD 图纸信息
        if "drawing_title" in info:
            lines.insert(0, f"图纸名称：{info['drawing_title']}")

        if "main_dimensions" in info:
            dims_text = "，".join([f"{k}{v}" for k, v in info["main_dimensions"].items()])
            lines.append(f"\n主要尺寸：{dims_text}")

        # 架构图信息
        if "main_components" in info:
            components = info["main_components"]
            lines.append(f"\n主要组件：{', '.join(components)}")

        if "layers" in info:
            layers = info["layers"]
            lines.append(f"系统层级：{', '.join(layers)}")

        return "\n".join(lines)

    async def _detect_image_type(
        self,
        image_path: Path,
        user_specified_type: Optional[str] = None
    ) -> str:
        """
        智能检测图片类型

        Args:
            image_path: 图片路径
            user_specified_type: 用户指定的类型（如果有）

        Returns:
            ImageType 枚举值
        """
        # 如果用户指定了类型，直接使用
        if user_specified_type:
            logger.info(f"  使用用户指定的图片类型: {user_specified_type}")
            return user_specified_type

        logger.info(f"🔍 智能检测图片类型...")

        # 基于文件扩展名的初步判断
        file_ext = image_path.suffix.lower()
        if file_ext in ['.dwg', '.dxf']:
            logger.info(f"  根据扩展名判断为: CAD")
            return ImageType.CAD

        # 使用 VLM 进行智能识别
        try:
            detection_prompt = """请快速识别这张图片的类型，从以下选项中选择最合适的一个：

1. **cad** - CAD工程制造图纸（包含尺寸标注、技术参数、零部件结构图）
2. **floor_plan** - 室内平面布置图/建筑平面图（包含房间布局、家具摆放、空间尺寸）
3. **architecture** - 研发架构图/流程图/系统图（包含模块、组件、数据流、业务流程）
4. **technical_doc** - 工业技术档案/工艺文件（包含表格、工艺参数、检验报告）

**判断依据：**
- 如果有大量尺寸标注、剖面图、零件视图 → cad
- 如果有房间、家具、门窗、动线 → floor_plan
- 如果有流程图、架构图、组件关系、箭头连接 → architecture
- 如果有表格、工艺流程、检验数据 → technical_doc

**请直接返回类型名称（小写），不要有其他内容。**"""

            # 使用较小的 token 限制快速判断
            from PIL import Image
            image = Image.open(image_path)
            image_base64 = self.vlm_analyzer.image_to_base64(image, max_size=1000)

            # 调用 VLM API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": detection_prompt
                        }
                    ]
                }
            ]

            response = await self.vlm_analyzer.openai_client.chat.completions.create(
                model=self.vlm_model_name,
                messages=messages,
                max_tokens=50,
                temperature=0.0
            )

            detected_type = response.choices[0].message.content.strip().lower()

            # 验证返回的类型
            valid_types = [ImageType.CAD, ImageType.FLOOR_PLAN, ImageType.ARCHITECTURE, ImageType.TECHNICAL_DOC]
            if detected_type in valid_types:
                logger.info(f"  ✓ 智能识别结果: {detected_type}")
                return detected_type
            else:
                logger.warning(f"  ⚠️ 无法识别类型: {detected_type}，使用默认类型: architecture")
                return ImageType.ARCHITECTURE

        except Exception as e:
            logger.warning(f"  ⚠️ 智能识别失败: {e}，使用默认类型: architecture")
            return ImageType.ARCHITECTURE

    def _generate_pdf_thumbnail(self, pdf_path: Path, file_id: str) -> Path:
        """生成PDF首页缩略图"""
        import fitz
        from PIL import Image
        import io

        try:
            # 打开PDF
            doc = fitz.open(str(pdf_path))

            # 获取第一页
            page = doc[0]

            # 渲染为图像（提高分辨率以获得更清晰的缩略图）
            mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放
            pix = page.get_pixmap(matrix=mat)

            # 转换为PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # 创建缩略图（保持宽高比）
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)

            # 保存缩略图
            thumbnail_path = self.preview_dir / f"{file_id}_thumb.png"
            img.save(thumbnail_path, "PNG", optimize=True)

            doc.close()

            logger.info(f"✓ PDF缩略图已生成: {thumbnail_path}")
            return thumbnail_path

        except Exception as e:
            logger.error(f"生成PDF缩略图失败: {e}")
            return None

    async def _analyze_pdf_images(
        self,
        pdf_path: Path,
        extraction_result: Dict[str, Any]
    ) -> str:
        """
        分析PDF中的图片页面，使用VLM提取信息

        Args:
            pdf_path: PDF文件路径
            extraction_result: PDF提取结果

        Returns:
            图片分析的文本内容
        """
        import fitz
        from PIL import Image
        import io

        logger.info("🖼️ 开始分析PDF中的图片页面...")

        image_analysis_results = []

        try:
            doc = fitz.open(str(pdf_path))

            # 遍历每一页
            for page_num in range(len(doc)):
                page = doc[page_num]

                # 获取页面图片
                image_list = page.get_images(full=True)

                # 如果这一页有图片，或者这一页主要是图片（文本很少）
                text_length = len(page.get_text().strip())

                # 判断是否为图片页：有图片且文本少于100字符
                if image_list and text_length < 100:
                    logger.info(f"  发现图片页: 第 {page_num + 1} 页")

                    # 渲染整页为图片
                    mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放
                    pix = page.get_pixmap(matrix=mat)

                    # 转换为PIL Image
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))

                    # 智能检测图片类型
                    # 先保存临时文件用于检测
                    temp_path = self.upload_dir / f"temp_page_{page_num}.png"
                    image.save(temp_path, "PNG")

                    detected_type = await self._detect_image_type(temp_path)

                    # 使用 VLM 分析
                    analysis_result = await self.vlm_analyzer.analyze_image(
                        image,
                        question=f"这是PDF文档第{page_num + 1}页的内容，请详细描述这张图的所有信息。",
                        image_type=detected_type
                    )

                    # 删除临时文件
                    if temp_path.exists():
                        temp_path.unlink()

                    # 保存分析结果
                    image_analysis_results.append({
                        'page': page_num + 1,
                        'type': detected_type,
                        'analysis': analysis_result.answer,
                        'structured_info': analysis_result.extracted_info
                    })

                    logger.info(f"  ✓ 第 {page_num + 1} 页分析完成 (类型: {detected_type})")

            doc.close()

            # 格式化图片分析结果
            if image_analysis_results:
                formatted_results = "\n\n=== PDF图片页面分析 ===\n\n"
                for result in image_analysis_results:
                    formatted_results += f"【第{result['page']}页 - {result['type']}】\n"
                    formatted_results += f"{result['analysis']}\n"
                    if result['structured_info']:
                        formatted_results += f"结构化信息: {result['structured_info']}\n"
                    formatted_results += "\n"

                logger.info(f"✓ PDF图片分析完成，共分析 {len(image_analysis_results)} 页")
                return formatted_results
            else:
                logger.info("  未发现需要VLM分析的图片页面")
                return ""

        except Exception as e:
            logger.error(f"❌ PDF图片分析失败: {e}")
            import traceback
            traceback.print_exc()
            return ""

    async def handle_search(
        self,
        request: SearchRequest
    ) -> SearchResponse:
        """处理搜索请求"""
        import time
        start_time = time.time()

        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 处理搜索请求")
        logger.info(f"  查询: {request.query}")
        logger.info(f"  模型: {request.model}")
        logger.info(f"  策略: {request.strategy}")
        logger.info(f"  TopK: {request.topK}")
        logger.info(f"  最小相似度: {request.minSimilarity}")
        logger.info(f"{'='*60}")

        # 执行向量检索 - 检索更多chunk以便聚合
        vector_results = await self.vector_manager.search(
            query=request.query,
            top_k=request.topK * 3  # 检索3倍数量，用于聚合后筛选
        )

        # 【新增】按文件聚合结果
        file_results = {}  # {file_id: {metadata, chunks, max_similarity}}

        for result in vector_results:
            metadata = result["metadata"]
            file_id = metadata.get("file_id", "unknown")

            if file_id not in file_results:
                file_results[file_id] = {
                    "metadata": metadata,
                    "chunks": [],
                    "max_similarity": result["similarity"]
                }

            file_results[file_id]["chunks"].append({
                "content": result["content"],
                "similarity": result["similarity"],
                "chunk_id": metadata.get("chunk_id", 0)
            })

            # 更新最高相似度
            if result["similarity"] > file_results[file_id]["max_similarity"]:
                file_results[file_id]["max_similarity"] = result["similarity"]

        # 【新增】按最高相似度排序文件
        sorted_files = sorted(
            file_results.items(),
            key=lambda x: x[1]["max_similarity"],
            reverse=True
        )

        # 【调试】打印相似度信息
        if sorted_files:
            logger.info(f"\n📊 相似度分布:")
            for i, (file_id, file_data) in enumerate(sorted_files[:5], 1):  # 只显示前5个
                logger.info(f"  [{i}] {file_data['metadata'].get('file_name', 'unknown')}: {file_data['max_similarity']:.6f}")

        # 【新增】根据相似度阈值过滤
        filtered_files = [
            (file_id, file_data)
            for file_id, file_data in sorted_files
            if file_data["max_similarity"] >= request.minSimilarity
        ]

        # 【新增】只保留 topK 个文件
        final_files = filtered_files[:request.topK]

        logger.info(f"  原始检索: {len(vector_results)} 个chunk")
        logger.info(f"  聚合去重: {len(sorted_files)} 个文件")
        logger.info(f"  相似度过滤(>={request.minSimilarity}): {len(filtered_files)} 个文件")
        logger.info(f"  最终返回(topK={request.topK}): {len(final_files)} 个文件")

        # 格式化为前端需要的格式
        search_results = []
        for idx, (file_id, file_data) in enumerate(final_files):
            metadata = file_data["metadata"]
            chunks = file_data["chunks"]

            # 确定文件类型
            file_name = metadata.get("file_name", "")
            image_type = metadata.get("image_type", "")

            # 根据检测的图片类型设置显示类型
            if image_type:
                file_type_map = {
                    ImageType.CAD: "CAD图纸",
                    ImageType.FLOOR_PLAN: "平面布置图",
                    ImageType.ARCHITECTURE: "架构图",
                    ImageType.TECHNICAL_DOC: "技术文档"
                }
                file_type = file_type_map.get(image_type, "图片")
                thumbnail_type = "image"
            elif file_name.lower().endswith('.pdf'):
                file_type = "PDF"
                thumbnail_type = "pdf"
            elif any(ext in file_name.lower() for ext in ['.dwg', '.dxf']):
                file_type = "CAD"
                thumbnail_type = "cad"
            elif any(ext in file_name.lower() for ext in ['.png', '.jpg', '.jpeg']):
                file_type = "图片"
                thumbnail_type = "image"
            else:
                file_type = "其他"
                thumbnail_type = "image"

            # 【新增】合并多个chunk的内容作为snippet
            # 选择相似度最高的chunk作为主要snippet
            best_chunk = max(chunks, key=lambda c: c["similarity"])
            snippet = best_chunk["content"][:200]

            # 如果有多个chunk，添加提示
            if len(chunks) > 1:
                snippet += f"... (共{len(chunks)}个相关片段)"

            # 提取页码信息
            page_info = metadata.get("page", "N/A")

            search_result = SearchResult(
                id=file_id,
                fileName=file_name,
                filePath=metadata.get("file_path", f"/files/{file_id}"),
                fileType=file_type,
                similarity=file_data["max_similarity"],
                page=str(page_info) if page_info else None,
                date=metadata.get("upload_date", datetime.now().isoformat())[:10],
                snippet=snippet,
                citationNumber=idx + 1,
                thumbnailType=thumbnail_type,
                thumbnailUrl=f"/api/thumbnail/{file_id}",
                previewUrl=f"/api/preview/{file_id}",
                version=metadata.get("version", "v1.0"),
                structuredData=self._extract_structured_data(metadata)
            )

            search_results.append(search_result)

        query_time = time.time() - start_time

        print(f"\n✓ 搜索完成")
        logger.info(f"  返回 {len(search_results)} 个文档")
        logger.info(f"  耗时: {query_time:.2f}秒")

        return SearchResponse(
            results=search_results,
            totalCount=len(search_results),
            queryTime=round(query_time * 1000),  # 转换为毫秒
            model=request.model,
            strategy=request.strategy
        )

    async def handle_upload(
        self,
        file: UploadFile,
        image_type: Optional[str] = None
    ) -> UploadResponse:
        """
        处理文件上传

        Args:
            file: 上传的文件
            image_type: 用户指定的图片类型（可选）
                       支持: cad, floor_plan, architecture, technical_doc
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📤 处理文件上传: {file.filename}")
        if image_type:
            logger.info(f"   用户指定类型: {image_type}")
        logger.info(f"{'='*60}")

        try:
            # 生成文件ID
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix.lower()

            # 保存上传的文件
            file_path = self.upload_dir / f"{file_id}{file_extension}"
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)

            logger.info(f"✓ 文件已保存: {file_path}")

            detected_image_type = None  # 记录检测到的图片类型

            # 根据文件类型处理
            if file_extension == '.pdf':
                # PDF 文件：使用快速模式提取
                extraction_result = await self.pdf_service.extract_fast(
                    str(file_path),
                    original_filename=file.filename
                )

                content_text = extraction_result["markdown"]
                file_type = "PDF"

                # 提取页面信息
                page_count = extraction_result["metadata"]["total_pages"]

                # 生成PDF首页缩略图
                self._generate_pdf_thumbnail(file_path, file_id)

                # 【新增】分析PDF中的图片页面
                pdf_image_analysis = await self._analyze_pdf_images(file_path, extraction_result)
                if pdf_image_analysis:
                    content_text += "\n\n" + pdf_image_analysis
                    logger.info("✓ PDF图片页面已整合到内容中")

            elif file_extension in ['.png', '.jpg', '.jpeg', '.dwg', '.dxf']:
                # 【新增】智能检测图片类型
                detected_image_type = await self._detect_image_type(file_path, image_type)

                # 根据检测的类型生成合适的问题
                question_map = {
                    ImageType.CAD: "请详细描述这张CAD图纸的内容，包括所有可见的技术信息、尺寸标注、零部件结构等。",
                    ImageType.FLOOR_PLAN: "请详细描述这张平面布置图，包括房间布局、尺寸、家具摆放、动线等信息。",
                    ImageType.ARCHITECTURE: "请详细描述这张架构图/流程图，包括所有组件、模块、关系和流程。",
                    ImageType.TECHNICAL_DOC: "请详细描述这份技术文档，包括所有可见的参数、表格数据、工艺信息等。"
                }

                question = question_map.get(detected_image_type, "请详细描述这张图的所有内容。")

                # 图像/CAD 文件：使用 VLM 分析
                analysis_result = await self.vlm_analyzer.analyze_image(
                    str(file_path),
                    question=question,
                    image_type=detected_image_type
                )

                # 【优化】将结构化信息转换为自然语言
                natural_language_info = self._format_extracted_info_to_natural_language(
                    analysis_result.extracted_info
                )
                content_text = f"{analysis_result.answer}\n\n{natural_language_info}"

                # 【新增】根据检测类型设置文件类型
                file_type_map = {
                    ImageType.CAD: "CAD图纸",
                    ImageType.FLOOR_PLAN: "平面布置图",
                    ImageType.ARCHITECTURE: "架构图",
                    ImageType.TECHNICAL_DOC: "技术文档"
                }
                file_type = file_type_map.get(detected_image_type, "图片")
                page_count = 1

            else:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_extension}")

            # 添加到向量库
            metadata = {
                "file_path": str(file_path),
                "file_extension": file_extension,
                "page_count": page_count,
                "version": "v1.0"
            }

            # 如果有检测到的图片类型，添加到元数据
            if detected_image_type:
                metadata["image_type"] = detected_image_type

            # 【新增】如果有分析结果，存储结构化信息到元数据
            if 'analysis_result' in locals():
                # ⚠️ ChromaDB 不支持嵌套字典，需要序列化
                # 将复杂的 extracted_info 转为 JSON 字符串
                metadata["extracted_info_json"] = json.dumps(analysis_result.extracted_info, ensure_ascii=False)

                # 【新增】提取关键字段到元数据顶层（便于过滤）
                extracted_info = analysis_result.extracted_info
                if "rooms" in extracted_info:
                    metadata["room_count"] = len(extracted_info["rooms"])
                    # 统计卧室数量
                    bedrooms = [r for r in extracted_info["rooms"] if "卧" in r.get("name", "")]
                    metadata["bedroom_count"] = len(bedrooms)

                if "total_dimensions" in extracted_info:
                    total_dims = extracted_info["total_dimensions"]
                    metadata["total_area"] = float(total_dims.get("total_area", 0))
                    metadata["total_length"] = float(total_dims.get("length", 0))
                    metadata["total_width"] = float(total_dims.get("width", 0))

            chunk_count = await self.vector_manager.add_document(
                file_id=file_id,
                file_name=file.filename,
                file_type=file_type,
                content=content_text,
                metadata=metadata
            )

            print(f"\n✓ 文件上传并索引完成")
            logger.info(f"  文件ID: {file_id}")
            logger.info(f"  文件类型: {file_type}")
            if detected_image_type:
                logger.info(f"  检测类型: {detected_image_type}")
            logger.info(f"  分块数: {chunk_count}")

            return UploadResponse(
                success=True,
                fileId=file_id,
                fileName=file.filename,
                message=f"文件上传成功，已分割为 {chunk_count} 个文本块并建立索引",
                detectedImageType=detected_image_type
            )

        except Exception as e:
            logger.error(f"❌ 文件上传失败: {e}")
            import traceback
            traceback.print_exc()

            return UploadResponse(
                success=False,
                fileId="",
                fileName=file.filename,
                message=f"文件上传失败: {str(e)}"
            )

    async def handle_follow_up_question(
        self,
        request: FollowUpQuestionRequest
    ) -> FollowUpQuestionResponse:
        """处理追问"""

        # 检索相关文档片段
        results = await self.vector_manager.search(
            query=request.question,
            top_k=3
        )

        # 过滤出指定文档的结果
        doc_results = [r for r in results if r["metadata"].get("file_id") == request.documentId]

        if not doc_results:
            # 如果没有找到指定文档，使用所有结果
            doc_results = results

        # 构建上下文
        context = "\n\n".join([r["content"] for r in doc_results[:3]])

        # 使用 LLM 生成回答
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model_name=self.vlm_model_name,
                api_key=self.vlm_api_key,
                base_url=self.vlm_model_url,
                temperature=0.3
            )

            prompt = f"""基于以下文档内容回答问题：

文档内容：
{context}

问题：{request.question}

请给出准确、详细的回答，并指出回答依据的内容来自哪些部分。"""

            response = await llm.ainvoke(prompt)
            answer = response.content

            # 提取引用
            citations = [i + 1 for i in range(len(doc_results))]

            logger.info(f"✓ 回答生成完成")

            return FollowUpQuestionResponse(
                answer=answer,
                citations=citations,
                confidence=0.85
            )

        except Exception as e:
            logger.error(f"❌ 回答生成失败: {e}")
            return FollowUpQuestionResponse(
                answer="抱歉，无法生成回答。",
                citations=[],
                confidence=0.0
            )

    def _extract_structured_data(self, metadata: Dict[str, Any]) -> List[Dict[str, str]]:
        """从元数据提取结构化数据"""
        structured_data = []

        if "page_count" in metadata:
            structured_data.append({
                "label": "页数",
                "value": str(metadata["page_count"])
            })

        if "version" in metadata:
            structured_data.append({
                "label": "版本",
                "value": metadata["version"]
            })

        if "upload_date" in metadata:
            structured_data.append({
                "label": "上传日期",
                "value": metadata["upload_date"][:10]
            })

        return structured_data

    async def handle_intelligent_qa(
        self,
        request: IntelligentQARequest
    ) -> IntelligentQAResponse:
        """
        智能问答 - 直接回答用户问题

        根据问题类型选择不同的处理策略：
        1. 精确查询：从元数据直接提取答案（如："有几个卧室"）
        2. 过滤查询：先过滤再检索（如："找3个卧室的户型"）
        3. 一般查询：向量检索 + LLM生成答案
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 智能问答")
        logger.info(f"  问题: {request.question}")
        logger.info(f"{'='*60}")

        # 1. 分类问题类型
        query_type = self._classify_question(request.question)
        logger.info(f"  问题类型: {query_type}")

        # 2. 根据问题类型处理
        if query_type == "exact_query":
            # 精确查询：从元数据直接提取
            answer, sources, confidence = await self._handle_exact_query(request.question, request.top_k)

        elif query_type == "filter_query":
            # 过滤查询：智能过滤 + 检索
            answer, sources, confidence = await self._handle_filter_query(request.question, request.top_k)

        else:
            # 一般查询：向量检索 + LLM
            answer, sources, confidence = await self._handle_general_query(request.question, request.top_k)

        logger.info(f"✓ 答案已生成")
        logger.info(f"  置信度: {confidence:.2f}")
        logger.info(f"  来源数: {len(sources)}")

        return IntelligentQAResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            query_type=query_type
        )

    def _classify_question(self, question: str) -> str:
        """分类问题类型"""
        question_lower = question.lower()

        # 精确查询关键词
        exact_keywords = ["几个", "多少个", "有多少", "面积", "尺寸", "长度", "宽度", "多大", "多长"]
        if any(kw in question for kw in exact_keywords):
            return "exact_query"

        # 过滤查询关键词
        filter_keywords = ["找", "查找", "筛选", "符合", "满足", "大于", "小于", "至少"]
        if any(kw in question for kw in filter_keywords):
            return "filter_query"

        return "general_query"

    async def _handle_exact_query(
        self,
        question: str,
        top_k: int
    ) -> tuple[str, List[Dict[str, Any]], float]:
        """处理精确查询 - 从元数据直接提取答案"""

        # 向量检索找到最相关的文档
        vector_results = await self.vector_manager.search(
            query=question,
            top_k=top_k
        )

        if not vector_results:
            return "抱歉，没有找到相关信息。", [], 0.0

        top_result = vector_results[0]
        metadata = top_result["metadata"]

        # 从 JSON 字符串解析 extracted_info
        extracted_info = {}
        if "extracted_info_json" in metadata:
            try:
                extracted_info = json.loads(metadata["extracted_info_json"])
            except:
                pass

        # 根据问题提取答案
        answer_parts = []

        # 处理卧室相关问题
        if "卧室" in question or "房间" in question:
            if "rooms" in extracted_info:
                rooms = extracted_info["rooms"]
                bedrooms = [r for r in rooms if "卧" in r.get("name", "")]

                if bedrooms:
                    answer_parts.append(f"这张{metadata.get('file_type', '图纸')}有{len(bedrooms)}个卧室：")
                    for i, room in enumerate(bedrooms, 1):
                        room_text = f"{i}. {room['name']}"
                        if "dimensions" in room and "area" in room["dimensions"]:
                            room_text += f" - {room['dimensions']['area']}平方米"
                        if "position" in room:
                            room_text += f"（{room['position']}）"
                        answer_parts.append(room_text)
                else:
                    answer_parts.append("未找到卧室信息。")

        # 处理面积相关问题
        elif "面积" in question or "多大" in question:
            if "total_area" in metadata:
                total_area = metadata["total_area"]
                answer_parts.append(f"总面积为 {total_area} 平方米")
            elif "total_dimensions" in extracted_info:
                total_area = extracted_info["total_dimensions"].get("total_area")
                answer_parts.append(f"总面积为 {total_area} 平方米")
            else:
                answer_parts.append("未找到面积信息。")

        # 处理尺寸相关问题
        elif "尺寸" in question or "长度" in question or "宽度" in question:
            if "total_dimensions" in extracted_info:
                dims = extracted_info["total_dimensions"]
                answer_parts.append(
                    f"建筑尺寸：长 {dims.get('length')} 米，宽 {dims.get('width')} 米，"
                    f"总面积 {dims.get('total_area')} 平方米"
                )
            else:
                answer_parts.append("未找到尺寸信息。")

        # 默认回答
        if not answer_parts:
            answer_parts.append("根据文档内容：")
            answer_parts.append(top_result["content"][:300])

        # 添加来源
        answer_parts.append(f"\n📄 来源：{metadata.get('file_name', '未知文件')}")

        answer = "\n".join(answer_parts)

        # 构建来源信息
        sources = [{
            "file_id": metadata.get("file_id"),
            "file_name": metadata.get("file_name"),
            "file_type": metadata.get("file_type"),
            "similarity": top_result["similarity"]
        }]

        confidence = top_result["similarity"]

        return answer, sources, confidence

    async def _handle_filter_query(
        self,
        question: str,
        top_k: int
    ) -> tuple[str, List[Dict[str, Any]], float]:
        """处理过滤查询 - 智能过滤 + 检索"""

        # 解析过滤条件
        filters = self._parse_filter_conditions(question)
        logger.info(f"  解析的过滤条件: {filters}")

        # TODO: 实现带过滤的检索（需要 ChromaDB 支持元数据过滤）
        # 暂时使用普通检索后过滤
        vector_results = await self.vector_manager.search(
            query=question,
            top_k=top_k * 3  # 检索更多结果用于过滤
        )

        # 应用过滤条件
        filtered_results = []
        for result in vector_results:
            metadata = result["metadata"]

            # 检查是否符合过滤条件
            if self._match_filters(metadata, filters):
                filtered_results.append(result)

            if len(filtered_results) >= top_k:
                break

        if not filtered_results:
            return f"没有找到符合条件的结果。", [], 0.0

        # 生成答案
        answer_parts = [f"找到 {len(filtered_results)} 个符合条件的结果：\n"]

        for i, result in enumerate(filtered_results, 1):
            metadata = result["metadata"]

            # 解析 extracted_info
            extracted_info = {}
            if "extracted_info_json" in metadata:
                try:
                    extracted_info = json.loads(metadata["extracted_info_json"])
                except:
                    pass

            answer_parts.append(f"\n{i}. {metadata.get('file_name')}")

            # 显示关键信息
            if "total_area" in metadata:
                answer_parts.append(f"   - 总面积：{metadata['total_area']}平方米")

            if "bedroom_count" in metadata:
                answer_parts.append(f"   - 卧室数：{metadata['bedroom_count']}个")

            if "room_count" in metadata:
                answer_parts.append(f"   - 房间数：{metadata['room_count']}个")

        answer = "\n".join(answer_parts)

        # 构建来源信息
        sources = [{
            "file_id": r["metadata"].get("file_id"),
            "file_name": r["metadata"].get("file_name"),
            "file_type": r["metadata"].get("file_type"),
            "similarity": r["similarity"]
        } for r in filtered_results]

        confidence = filtered_results[0]["similarity"] if filtered_results else 0.0

        return answer, sources, confidence

    def _parse_filter_conditions(self, question: str) -> Dict[str, Any]:
        """解析过滤条件"""
        filters = {}

        # 解析数字条件
        import re

        # 卧室数量
        bedroom_match = re.search(r'(\d+)\s*个?\s*卧室', question)
        if bedroom_match:
            filters["bedroom_count"] = int(bedroom_match.group(1))

        # 房间数量
        room_match = re.search(r'(\d+)\s*个?\s*房间', question)
        if room_match:
            filters["room_count"] = int(room_match.group(1))

        # 面积范围
        area_match = re.search(r'(\d+)\s*[以上大于].*?平', question)
        if area_match:
            filters["total_area_gte"] = int(area_match.group(1))

        area_match2 = re.search(r'[小少于].*?(\d+)\s*平', question)
        if area_match2:
            filters["total_area_lte"] = int(area_match2.group(1))

        # 图纸类型
        if "平面图" in question or "户型" in question:
            filters["image_type"] = ImageType.FLOOR_PLAN

        return filters

    def _match_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filters.items():
            if key == "bedroom_count":
                if metadata.get("bedroom_count", 0) != value:
                    return False

            elif key == "room_count":
                if metadata.get("room_count", 0) != value:
                    return False

            elif key == "total_area_gte":
                if metadata.get("total_area", 0) < value:
                    return False

            elif key == "total_area_lte":
                if metadata.get("total_area", float('inf')) > value:
                    return False

            elif key == "image_type":
                if metadata.get("image_type") != value:
                    return False

        return True

    async def _handle_general_query(
        self,
        question: str,
        top_k: int
    ) -> tuple[str, List[Dict[str, Any]], float]:
        """处理一般查询 - 向量检索 + LLM"""

        # 向量检索
        vector_results = await self.vector_manager.search(
            query=question,
            top_k=top_k
        )

        if not vector_results:
            return "抱歉，没有找到相关信息。", [], 0.0

        # 构建上下文
        context_parts = []
        for i, result in enumerate(vector_results, 1):
            metadata = result["metadata"]
            context_parts.append(f"[文档{i}] {metadata.get('file_name')}:")
            context_parts.append(result["content"][:500])
            context_parts.append("")

        context = "\n".join(context_parts)

        # 使用 LLM 生成答案（如果配置了）
        if self.vlm_api_key:
            try:
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(
                    model_name=self.vlm_model_name,
                    api_key=self.vlm_api_key,
                    base_url=self.vlm_model_url,
                    temperature=0.3
                )

                prompt = f"""基于以下文档内容回答问题。

文档内容：
{context}

问题：{question}

请给出准确、详细的回答。"""

                response = await llm.ainvoke(prompt)
                answer = response.content

                # 添加来源
                sources_text = "\n\n📄 参考来源：\n"
                for i, result in enumerate(vector_results, 1):
                    sources_text += f"{i}. {result['metadata'].get('file_name')}\n"

                answer += sources_text

            except Exception as e:
                logger.error(f"LLM生成答案失败: {e}")
                answer = f"根据检索到的内容：\n\n{vector_results[0]['content'][:500]}\n\n来源：{vector_results[0]['metadata'].get('file_name')}"
        else:
            # 没有配置LLM，返回最相关的内容
            answer = f"根据检索到的内容：\n\n{vector_results[0]['content'][:500]}\n\n来源：{vector_results[0]['metadata'].get('file_name')}"

        # 构建来源信息
        sources = [{
            "file_id": r["metadata"].get("file_id"),
            "file_name": r["metadata"].get("file_name"),
            "file_type": r["metadata"].get("file_type"),
            "similarity": r["similarity"]
        } for r in vector_results]

        confidence = vector_results[0]["similarity"]

        return answer, sources, confidence


# ============ 请求日志中间件 ============

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """记录所有API请求的中间件"""

    async def dispatch(self, request: Request, call_next):
        # 记录请求信息
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 获取客户端信息
        client_host = request.client.host if request.client else "unknown"

        # 记录请求开始
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"[{request_id}] 📥 收到请求")
        logger.info(f"[{request_id}]   方法: {request.method}")
        logger.info(f"[{request_id}]   路径: {request.url.path}")
        logger.info(f"[{request_id}]   客户端: {client_host}")
        logger.info(f"[{request_id}]   User-Agent: {request.headers.get('user-agent', 'N/A')}")

        # 如果是 POST 请求，记录 Content-Type
        if request.method == "POST":
            content_type = request.headers.get('content-type', 'N/A')
            logger.info(f"[{request_id}]   Content-Type: {content_type}")

        logger.info(f"{'='*80}")

        # 处理请求
        try:
            response = await call_next(request)

            # 计算耗时
            process_time = time.time() - start_time

            # 记录响应
            logger.info(f"")
            logger.info(f"{'='*80}")
            logger.info(f"[{request_id}] 📤 返回响应")
            logger.info(f"[{request_id}]   状态码: {response.status_code}")
            logger.info(f"[{request_id}]   耗时: {process_time:.3f}秒")
            logger.info(f"{'='*80}")
            logger.info(f"")

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except Exception as e:
            # 记录错误
            process_time = time.time() - start_time
            logger.error(f"")
            logger.error(f"{'='*80}")
            logger.error(f"[{request_id}] ❌ 请求处理失败")
            logger.error(f"[{request_id}]   错误: {str(e)}")
            logger.error(f"[{request_id}]   耗时: {process_time:.3f}秒")
            logger.error(f"{'='*80}")
            logger.error(f"", exc_info=True)
            raise


# ============ FastAPI 应用 ============

app = FastAPI(
    title="多模态 RAG API",
    description="支持 PDF、CAD、图像的多模态文档检索与问答系统",
    version="1.0.0"
)

# 添加请求日志中间件
app.add_middleware(RequestLoggerMiddleware)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
service = MultimodalRAGService()


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "多模态 RAG API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """搜索接口"""
    try:
        log_request(f"\n{'='*80}")
        log_request(f"🔍 API收到搜索请求")
        log_request(f"  查询: {request.query}")
        log_request(f"  模型: {request.model}")
        log_request(f"  策略: {request.strategy}")
        log_request(f"  TopK: {request.topK}")
        print(f"{'='*80}\n")
        sys.stdout.flush()

        result = await service.handle_search(request)

        log_request(f"\n{'='*80}")
        log_request(f"✓ API搜索完成，返回 {result.totalCount} 个结果")
        print(f"{'='*80}\n")
        sys.stdout.flush()

        return result
    except Exception as e:
        print(f"\n❌ 搜索失败: {e}\n")
        sys.stdout.flush()
        logger.error(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    image_type: Optional[str] = None
):
    """
    文件上传接口

    Args:
        file: 上传的文件
        image_type: 可选的图片类型指定
                   支持: cad, floor_plan, architecture, technical_doc
    """
    try:
        log_request(f"\n{'='*80}")
        log_request(f"📤 API收到文件上传请求")
        log_request(f"  文件名: {file.filename}")
        log_request(f"  Content-Type: {file.content_type}")
        if image_type:
            log_request(f"  指定类型: {image_type}")
        print(f"{'='*80}\n")
        sys.stdout.flush()

        result = await service.handle_upload(file, image_type)

        log_request(f"\n{'='*80}")
        print(f"{'✓' if result.success else '❌'} 文件上传{'成功' if result.success else '失败'}")
        log_request(f"  消息: {result.message}")
        if result.detectedImageType:
            log_request(f"  检测类型: {result.detectedImageType}")
        print(f"{'='*80}\n")
        sys.stdout.flush()

        return result
    except Exception as e:
        print(f"\n❌ 上传失败: {e}\n")
        sys.stdout.flush()
        logger.error(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question", response_model=FollowUpQuestionResponse)
async def follow_up_question(request: FollowUpQuestionRequest):
    """追问接口"""
    try:
        return await service.handle_follow_up_question(request)
    except Exception as e:
        logger.error(f"❌ 追问失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=IntelligentQAResponse)
async def intelligent_qa(request: IntelligentQARequest):
    """
    智能问答接口 - 直接回答用户问题

    支持三种查询类型：
    1. 精确查询：从元数据直接提取答案（如："有几个卧室？"）
    2. 过滤查询：智能过滤 + 检索（如："找3个卧室的户型"）
    3. 一般查询：向量检索 + LLM生成答案
    """
    try:
        log_request(f"\n{'='*80}")
        log_request(f"🤖 API收到智能问答请求")
        log_request(f"  问题: {request.question}")
        log_request(f"  TopK: {request.top_k}")
        print(f"{'='*80}\n")
        sys.stdout.flush()

        result = await service.handle_intelligent_qa(request)

        log_request(f"\n{'='*80}")
        log_request(f"✓ 答案已生成")
        log_request(f"  问题类型: {result.query_type}")
        log_request(f"  置信度: {result.confidence:.2f}")
        log_request(f"  来源数: {len(result.sources)}")
        print(f"{'='*80}\n")
        sys.stdout.flush()

        return result
    except Exception as e:
        print(f"\n❌ 智能问答失败: {e}\n")
        sys.stdout.flush()
        logger.error(f"❌ 智能问答失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preview/{file_id}")
async def get_preview(file_id: str):
    """获取文档预览"""
    # 预览和缩略图暂时一样，返回原图
    return await get_thumbnail(file_id)


@app.get("/thumbnail/{file_id}")
async def get_thumbnail(file_id: str):
    """获取文档缩略图"""
    try:
        # 查找文件
        for ext in ['.png', '.jpg', '.jpeg', '.pdf', '.dwg', '.dxf']:
            file_path = service.upload_dir / f"{file_id}{ext}"
            if file_path.exists():
                # 对于图片，直接返回原图
                if ext in ['.png', '.jpg', '.jpeg']:
                    return FileResponse(file_path, media_type=f"image/{ext[1:]}")
                # 对于PDF，返回缩略图
                elif ext == '.pdf':
                    thumbnail_path = service.preview_dir / f"{file_id}_thumb.png"
                    if thumbnail_path.exists():
                        return FileResponse(thumbnail_path, media_type="image/png")
                    else:
                        # 如果缩略图不存在，尝试生成
                        thumb_path = service._generate_pdf_thumbnail(file_path, file_id)
                        if thumb_path and thumb_path.exists():
                            return FileResponse(thumb_path, media_type="image/png")
                        else:
                            raise HTTPException(status_code=500, detail="PDF缩略图生成失败")
                else:
                    raise HTTPException(status_code=501, detail="该文件类型暂不支持缩略图")

        raise HTTPException(status_code=404, detail=f"文件不存在: {file_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缩略图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{document_id}")
async def download_document(document_id: str):
    """下载文档"""
    # TODO: 实现文档下载
    raise HTTPException(status_code=501, detail="下载功能暂未实现")


# ============ 启动服务 ============

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 启动多模态 RAG 服务")
    print("="*60 + "\n")

    # 配置 uvicorn 日志
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(message)s"
    log_config["formatters"]["access"]["fmt"] = '%(client_addr)s - "%(request_line)s" %(status_code)s'

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        log_config=log_config,
        access_log=True
    )
