"""
Markdown文本切分API服务
支持两种切分方式：header_recursive（默认）和 markdown_only
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import uvicorn

# 导入已有的切分模块
from MarkdownTextSplitter import chunk_markdown_only_with_cross_page
from header_recursive import chunk_header_recursive_with_cross_page

app = FastAPI(
    title="Markdown文本切分API",
    description="提供基于标题和纯Markdown两种切分策略",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================

class ChunkingConfig(BaseModel):
    """切分配置"""
    method: Literal["header_recursive", "markdown_only"] = Field(
        default="header_recursive",
        description="切分方法：header_recursive(标题+递归) 或 markdown_only(纯Markdown)"
    )
    chunk_size: int = Field(default=1500, ge=100, le=10000, description="目标chunk大小")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="chunk重叠长度")
    merge_tolerance: float = Field(default=0.2, ge=0, le=1.0, description="合并容忍度")
    max_page_span: int = Field(default=3, ge=0, le=10, description="最大跨页数，0表示不限制")
    bridge_span: int = Field(default=150, ge=0, le=500, description="跨页桥接片段长度")
    add_bridges: bool = Field(default=True, description="是否添加跨页桥接片段")

class ChunkResult(BaseModel):
    """单个切分块"""
    page_start: int
    page_end: int
    pages: List[int]
    text: str
    text_length: int
    headers: Optional[Dict[str, str]] = None
    continued: bool
    cross_page_bridge: bool
    is_table_like: bool

class ChunkingResponse(BaseModel):
    """切分结果响应"""
    success: bool
    message: str
    filename: Optional[str] = None
    data: Dict[str, Any]
    error: Optional[str] = None

class ChunkingRequest(BaseModel):
    """切分请求"""
    markdown: str = Field(..., description="Markdown文本内容")
    filename: Optional[str] = Field(None, description="文件名（可选）")
    config: ChunkingConfig = Field(default_factory=ChunkingConfig, description="切分配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="原始元数据（可选）")

# ==================== API端点 ====================

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "Markdown文本切分API",
        "version": "1.0.0",
        "methods": ["header_recursive", "markdown_only"]
    }

@app.post("/chunk", response_model=ChunkingResponse)
async def chunk_markdown(request: ChunkingRequest):
    """
    对Markdown文本进行切分
    
    - **markdown**: Markdown文本内容（必填）
    - **config**: 切分配置（可选，使用默认值）
    - **filename**: 文件名（可选）
    - **metadata**: 原始元数据（可选）
    
    返回在原数据基础上添加chunks字段的结果
    """
    try:
        # 根据配置选择切分方法
        if request.config.method == "header_recursive":
            # 调用 header_recursive 模块
            result = chunk_header_recursive_with_cross_page(
                md_text=request.markdown,
                chunk_size=request.config.chunk_size,
                chunk_overlap=request.config.chunk_overlap,
                merge_tolerance=request.config.merge_tolerance,
                max_page_span=request.config.max_page_span,
                bridge_span=request.config.bridge_span if request.config.add_bridges else 0
            )
        else:  # markdown_only
            # 调用 MarkdownTextSplitter 模块
            result = chunk_markdown_only_with_cross_page(
                md_text=request.markdown,
                chunk_size=request.config.chunk_size,
                chunk_overlap=request.config.chunk_overlap,
                merge_tolerance=request.config.merge_tolerance,
                max_page_span=request.config.max_page_span,
                bridge_span=request.config.bridge_span if request.config.add_bridges else 0
            )
        
        # 构建返回数据 - 保留原有的metadata，并添加新字段
        response_data = {}
        
        # 如果有原始元数据，先保留它
        if request.metadata:
            response_data.update(request.metadata)
        
        # 添加或更新字段
        response_data.update({
            "markdown": request.markdown,
            "full_text": result["full_text"],
            "chunks": result["chunks"],
            "chunking_config": request.config.dict(),
            "chunk_stats": {
                "total_chunks": len(result["chunks"]),
                "bridge_chunks": sum(1 for c in result["chunks"] if c["cross_page_bridge"]),
                "cross_page_chunks": sum(1 for c in result["chunks"] if c["continued"] and not c["cross_page_bridge"]),
                "single_page_chunks": sum(1 for c in result["chunks"] if not c["continued"] and not c["cross_page_bridge"]),
                "table_chunks": sum(1 for c in result["chunks"] if c["is_table_like"]),
                "avg_chunk_length": sum(c["text_length"] for c in result["chunks"]) / len(result["chunks"]) if result["chunks"] else 0
            }
        })
        
        return ChunkingResponse(
            success=True,
            message=f"切分成功，使用方法: {request.config.method}",
            filename=request.filename,
            data=response_data,
            error=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"切分失败: {str(e)}"
        )

@app.post("/chunk/from-result", response_model=ChunkingResponse)
async def chunk_from_result(
    result: Dict[str, Any],
    config: ChunkingConfig = ChunkingConfig()
):
    """
    从accurate_result.json格式的数据进行切分
    
    接受完整的accurate_result.json格式，在data字段中添加chunks相关信息
    """
    try:
        # 提取markdown内容
        if not result.get("success"):
            raise HTTPException(status_code=400, detail="输入数据标记为失败")
        
        data = result.get("data", {})
        markdown = data.get("markdown")
        
        if not markdown:
            raise HTTPException(status_code=400, detail="未找到markdown字段")
        
        # 执行切分
        if config.method == "header_recursive":
            # 调用 header_recursive 模块
            chunk_result = chunk_header_recursive_with_cross_page(
                md_text=markdown,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                merge_tolerance=config.merge_tolerance,
                max_page_span=config.max_page_span,
                bridge_span=config.bridge_span if config.add_bridges else 0
            )
        else:  # markdown_only
            # 调用 MarkdownTextSplitter 模块
            chunk_result = chunk_markdown_only_with_cross_page(
                md_text=markdown,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                merge_tolerance=config.merge_tolerance,
                max_page_span=config.max_page_span,
                bridge_span=config.bridge_span if config.add_bridges else 0
            )
        
        # 在原data基础上添加chunks信息（保留所有原有字段如images等）
        result["data"]["chunks"] = chunk_result["chunks"]
        result["data"]["full_text"] = chunk_result["full_text"]
        result["data"]["chunking_config"] = config.dict()
        result["data"]["chunk_stats"] = {
            "total_chunks": len(chunk_result["chunks"]),
            "bridge_chunks": sum(1 for c in chunk_result["chunks"] if c["cross_page_bridge"]),
            "cross_page_chunks": sum(1 for c in chunk_result["chunks"] if c["continued"] and not c["cross_page_bridge"]),
            "single_page_chunks": sum(1 for c in chunk_result["chunks"] if not c["continued"] and not c["cross_page_bridge"]),
            "table_chunks": sum(1 for c in chunk_result["chunks"] if c["is_table_like"]),
            "avg_chunk_length": sum(c["text_length"] for c in chunk_result["chunks"]) / len(chunk_result["chunks"]) if chunk_result["chunks"] else 0
        }
        
        # 更新message
        result["message"] = f"{result.get('message', '')} - 切分完成({config.method})"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"切分失败: {str(e)}"
        )

# ==================== 启动配置 ====================

if __name__ == "__main__":
    uvicorn.run(
        "markdown_chunker_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )