"""
PDF提取服务 - FastAPI接口版本
支持快速模式和精确模式的HTTP API调用
"""
from dataclasses import dataclass
import io
import base64
import asyncio
import json
import re
import tempfile
import shutil
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pymupdf4llm
import fitz
from PIL import Image
from pdf2image import convert_from_bytes
import uvicorn
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "04_vlm_based"))
from llm_extraction import PAGES_PER_REQUEST, CONCURRENT_REQUESTS


# ============ 数据模型 ============

class AccurateExtractionRequest(BaseModel):
    """精确模式提取请求"""
    api_key: str
    model_name: str
    model_url: str


class ExtractionResponse(BaseModel):
    """提取响应"""
    success: bool
    message: str
    filename: Optional[str] = None  # 添加文件名字段
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ExtractionResult:
    """提取结果数据类"""
    filename: str = ""  # 添加默认值
    markdown_content: str = ""
    tables: List[Dict[str, Any]] = None
    formulas: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    token_usage: Dict[str, int] = None
    time_cost: Dict[str, float] = None
    page_images: List[Image.Image] = None
    per_page_results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.formulas is None:
            self.formulas = []
        if self.metadata is None:
            self.metadata = {}
        if self.token_usage is None:
            self.token_usage = {}
        if self.time_cost is None:
            self.time_cost = {}
        if self.page_images is None:
            self.page_images = []
        if self.per_page_results is None:
            self.per_page_results = []


# ============ PDF提取服务 ============

class PDFExtractionService:
    """统一的PDF提取服务"""
    
    def __init__(self):
        self.default_pages_per_request = PAGES_PER_REQUEST  # 修改这里
        self.default_concurrent_requests = CONCURRENT_REQUESTS
        self.default_dpi = 100
    
    async def extract_fast(self, file_path: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
        """快速模式：使用PyMuPDF4LLM提取"""
        print(f"\n{'='*60}")
        print(f"快速模式提取 - 使用PyMuPDF4LLM")
        print(f"{'='*60}\n")
        
        # 获取文件名
        filename = original_filename or Path(file_path).name
        
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        temp_dir = Path(tempfile.mkdtemp())
        temp_images_dir = temp_dir / "images"
        temp_images_dir.mkdir(exist_ok=True)

        print("正在提取PDF内容和图片...")

        # 在切换工作目录之前，先获取PDF的绝对路径
        import os
        pdf_absolute_path = str(pdf_path.resolve())

        # 切换工作目录到临时目录，让pymupdf4llm将图片保存到images子目录
        original_cwd = os.getcwd()
        os.chdir(str(temp_dir))

        try:
            md_data = pymupdf4llm.to_markdown(
                pdf_absolute_path,  # 使用之前保存的绝对路径
                page_chunks=True,
                write_images=True
            )
        finally:
            os.chdir(original_cwd)
        
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        print(f"✓ 文档共 {total_pages} 页")
        
        markdown_parts = []
        
        if isinstance(md_data, list):
            for idx, page_data in enumerate(md_data):
                page_num = idx + 1
                if isinstance(page_data, dict):
                    text = page_data.get('text', '')
                else:
                    text = str(page_data)
                
                text = text.replace(str(temp_images_dir.absolute()), "images")
                markdown_parts.append(f"{{{{第{page_num}页}}}}\n{text}\n")
        else:
            text = str(md_data)
            text = text.replace(str(temp_images_dir.absolute()), "images")
            
            if "-----" in text or "---" in text:
                pages = text.split("-----") if "-----" in text else text.split("---")
                for idx, page_text in enumerate(pages):
                    if page_text.strip():
                        page_num = idx + 1
                        markdown_parts.append(f"{{{{第{page_num}页}}}}\n{page_text.strip()}\n")
            else:
                for page_num in range(1, total_pages + 1):
                    markdown_parts.append(f"{{{{第{page_num}页}}}}\n")
                markdown_parts.append(text)
        
        print("\n正在收集提取的图片...")
        images_data = []
        
        for img_file in sorted(temp_images_dir.glob("*.png")):
            try:
                img = Image.open(img_file)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                
                filename = img_file.name
                page_num = 1
                match = re.search(r'(\d+)', filename)
                if match:
                    page_num = int(match.group(1))
                
                images_data.append({
                    "filename": filename,
                    "base64": img_base64,
                    "page_num": page_num
                })
                
                print(f"  ✓ {filename}")
                
            except Exception as e:
                print(f"    ⚠️ 处理图片失败 {img_file.name}: {e}")
        
        # print("\n正在生成页面完整截图...")
        # for page_num in range(total_pages):
        #     page = doc[page_num]
        #     print(f"  处理第 {page_num + 1}/{total_pages} 页")
            
        #     try:
        #         pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        #         img_data = pix.tobytes("png")
        #         img = Image.open(io.BytesIO(img_data))
                
        #         buffer = io.BytesIO()
        #         img.save(buffer, format='PNG')
        #         buffer.seek(0)
        #         img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                
        #         filename = f"page_{page_num + 1}_full.png"
        #         images_data.append({
        #             "filename": filename,
        #             "base64": img_base64,
        #             "page_num": page_num + 1
        #         })
                
        #         # 移除了下面这一行，不再在markdown中添加截图链接
        #         markdown_parts.append(f"\n![{filename}](images/{filename})\n")
        #         pix = None
                
        #     except Exception as e:
        #         print(f"    ⚠️ 截图失败: {e}")
        
        doc.close()
        
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        
        final_markdown = "".join(markdown_parts)
        
        print(f"\n{'='*60}")
        print(f"✓ 快速提取完成")
        print(f"  - 页数: {total_pages}")
        print(f"  - 图片数: {len(images_data)}")
        print(f"  - Markdown长度: {len(final_markdown)} 字符")
        print(f"{'='*60}\n")
        
        return {
            "filename": filename,  # 添加这一行
            "markdown": final_markdown,
            "images": images_data,
            "metadata": {
                "total_pages": total_pages,
                "total_images": len(images_data)
            }
        }
    
    async def extract_accurate(
        self,
        file_path: str,
        api_key: str,
        model_name: str,
        model_url: str,
        original_filename: Optional[str] = None  # 添加原始文件名参数
    ) -> Dict[str, Any]:
        """精确模式:使用LLM提取"""
        print(f"\n{'='*60}")
        print(f"精确模式提取 - 使用LLM ({model_name})")
        print(f"{'='*60}\n")
        
        from llm_extraction import PDFMultimodalExtractor
        
        extractor = PDFMultimodalExtractor(
            model_url=model_url,
            api_key=api_key,
            model_name=model_name,
            pages_per_request=self.default_pages_per_request
        )
        
        # 临时修改文件名（用于显示和结果中）
        if original_filename:
            # 在提取前，可以将原始文件名传递给extractor
            result = await extractor.extract_from_pdf(file_path, original_filename=original_filename)
        else:
            result = await extractor.extract_from_pdf(file_path)
        
        # 直接使用大模型返回的markdown（已包含所有内容和正确的页码）
        # markdown中的 ## 第X页 是大模型输出的，{{第X页}} 是我们添加的标识符
        markdown_parts = []
        
        for page_result in result.per_page_results:
            page_num = page_result['page_num']
            page_markdown = page_result.get('markdown', '')
            
            # 添加页码标识符（用于分隔不同页面）
            markdown_parts.append(f"{{{{第{page_num}页}}}}\n{page_markdown}\n")
        
        final_markdown = "".join(markdown_parts)
        
        total_image_descriptions = sum(len(p.get('images', [])) for p in result.per_page_results)
        
        print(f"\n{'='*60}")
        print(f"✓ 精确提取完成")
        print(f"  - 页数: {result.metadata['total_pages']}")
        print(f"  - 表格数: {result.metadata['total_tables']}")
        print(f"  - 公式数: {result.metadata['total_formulas']}")
        print(f"  - 图片描述: {total_image_descriptions} 个")
        print(f"  - Token使用: {result.token_usage['total_tokens']:,}")
        print(f"  - 耗时: {result.time_cost['total_time']}秒")
        print(f"  - Markdown长度: {len(final_markdown)} 字符")
        print(f"{'='*60}\n")
        
        # 获取文件名（不包含路径）
        filename = original_filename or Path(file_path).name
        
        return {
            "filename": filename,  # 添加文件名字段
            "markdown": final_markdown,
            "images": [],  # 精确模式不返回图片base64，因为图片描述已在markdown中
            "metadata": {
                "total_pages": result.metadata['total_pages'],
                "total_tables": result.metadata['total_tables'],
                "total_formulas": result.metadata['total_formulas'],
                "total_image_descriptions": total_image_descriptions,
                "token_usage": result.token_usage,
                "time_cost": result.time_cost
            }
        }
    
    async def extract_from_pdf(self, pdf_path: str, original_filename: Optional[str] = None) -> ExtractionResult:
        """从PDF文件中提取完整信息"""
        import time
        overall_start = time.time()
        
        # 优先使用原始文件名，否则从路径提取
        filename = original_filename or Path(pdf_path).name
        print(f"filename: {filename}")
        
        print(f"开始处理PDF: {pdf_path}")
        print("="*60)
        
        # PDF转图片
        convert_start = time.time()
        images = self.pdf_to_images(pdf_path)
        self.pdf_convert_time = time.time() - convert_start
        total_pages = len(images)
        print(f"✓ PDF转换完成: {total_pages} 页 (耗时: {self.pdf_convert_time:.2f}秒)")
        
        # 批量处理页面
        per_page_results = []
        all_tables = []
        all_formulas = []
        
        for i in range(0, total_pages, self.pages_per_request):
            batch_images = images[i:i + self.pages_per_request]
            batch_page_nums = list(range(i + 1, min(i + 1 + self.pages_per_request, total_pages + 1)))
            
            image_base64_list = [self.image_to_base64(img) for img in batch_images]
            
            result = await self.call_multimodal_api(
                image_base64_list=image_base64_list,
                page_nums=batch_page_nums,
                total_pages=total_pages
            )
            
            per_page_results.extend(result['per_page_results'])
            all_tables.extend(result.get('tables', []))
            all_formulas.extend(result.get('formulas', []))
        
        # 组装最终markdown
        final_markdown = ""
        for page_result in per_page_results:
            final_markdown += page_result.get('markdown', '') + "\n\n"
        
        # 统计信息
        metadata = {
            "total_pages": total_pages,
            "total_tables": len(all_tables),
            "total_formulas": len(all_formulas),
            "model": self.model_name
        }
        
        token_usage = {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens
        }
        
        self.total_time = time.time() - overall_start
        time_cost = {
            "pdf_convert_time": round(self.pdf_convert_time, 2),
            "api_call_time": round(self.api_call_time, 2),
            "total_time": round(self.total_time, 2)
        }
        
        print("\n" + "="*60)
        print("✓ 提取完成")
        print(f"  总页数: {total_pages}")
        print(f"  表格数: {len(all_tables)}")
        print(f"  公式数: {len(all_formulas)}")
        print(f"  Token使用: {self.total_tokens:,} (提示: {self.total_prompt_tokens:,}, 完成: {self.total_completion_tokens:,})")
        print(f"  耗时: PDF转换 {self.pdf_convert_time:.2f}s + API调用 {self.api_call_time:.2f}s = 总计 {self.total_time:.2f}s")
        print("="*60 + "\n")
        
        return ExtractionResult(
            filename=filename,
            markdown_content=final_markdown,
            tables=all_tables,
            formulas=all_formulas,
            metadata=metadata,
            token_usage=token_usage,
            time_cost=time_cost,
            page_images=images,
            per_page_results=per_page_results
        )


# ============ FastAPI应用 ============

app = FastAPI(
    title="PDF提取服务API",
    description="支持快速模式和精确模式的PDF内容提取",
    version="1.0.0"
)

service = PDFExtractionService()


@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "running",
        "service": "PDF Extraction API",
        "version": "1.0.0"
    }


@app.post("/extract/fast", response_model=ExtractionResponse)
async def extract_fast(file: UploadFile = File(...)):
    """
    快速模式提取
    
    - **file**: PDF文件
    
    返回markdown内容和提取的图片（base64编码）
    """
    temp_file = None
    try:
        # 打印上传的文件名
        print(f"📥 收到文件: {file.filename}")
        
        # 保存上传的文件到临时位置
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # 执行提取
        result = await service.extract_fast(
            file_path=temp_file.name, 
            original_filename=file.filename  # 添加这一行
        )
        
        # 只返回文件名部分，不包含路径
        filename_only = Path(file.filename).name if file.filename else None
        
        return ExtractionResponse(
            success=True,
            message="快速提取成功",
            filename=filename_only,  # 只返回文件名部分
            data=result
        )
        
    except Exception as e:
        print(f"❌ 快速提取失败: {e}")
        import traceback
        traceback.print_exc()
        # 只返回文件名部分，不包含路径
        filename_only = Path(file.filename).name if file.filename else None
        
        return ExtractionResponse(
            success=False,
            message="快速提取失败",
            filename=filename_only,  # 只返回文件名部分
            error=str(e)
        )
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass


@app.post("/extract/accurate", response_model=ExtractionResponse)
async def extract_accurate(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    model_name: str = Form(...),
    model_url: str = Form(...)
):
    """精确模式提取"""
    temp_file = None
    try:
        print(f"📥 收到文件: {file.filename}")
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # 执行提取 - 传入原始文件名
        result = await service.extract_accurate(
            file_path=temp_file.name,
            api_key=api_key,
            model_name=model_name,
            model_url=model_url,
            original_filename=file.filename  # 已经有这一行了
        )
        
        # 只返回文件名部分，不包含路径
        filename_only = Path(file.filename).name if file.filename else None
        
        return ExtractionResponse(
            success=True,
            message="精确提取成功",
            filename=filename_only,  # 只返回文件名部分
            data=result
        )
        
    except Exception as e:
        print(f"❌ 精确提取失败: {e}")
        import traceback
        traceback.print_exc()
        # 只返回文件名部分，不包含路径
        filename_only = Path(file.filename).name if file.filename else None
        
        return ExtractionResponse(
            success=False,
            message="精确提取失败",
            filename=filename_only,  # 只返回文件名部分
            error=str(e)
        )
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass


@app.get("/health")
async def health_check():
    """服务健康检查"""
    return {
        "status": "healthy",
        "service": "pdf-extraction",
        "timestamp": asyncio.get_event_loop().time()
    }


# ============ 调试模式 ============

async def debug_extract(pdf_path: str, mode: str = "fast", **kwargs):
    """
    调试模式 - 可以直接调用提取功能进行测试
    
    Args:
        pdf_path: PDF文件路径
        mode: 提取模式，"fast" 或 "accurate"
        **kwargs: 其他参数，根据模式可能需要api_key, model_name, model_url
    """
    service = PDFExtractionService()
    
    try:
        if mode == "fast":
            print(f"开始快速模式提取: {pdf_path}")
            result = await service.extract_fast(pdf_path)
            print("提取完成，结果:")
            print(f"  页数: {result['metadata']['total_pages']}")
            print(f"  图片数: {result['metadata']['total_images']}")
            print(f"  Markdown长度: {len(result['markdown'])} 字符")
            return result
            
        elif mode == "accurate":
            print(f"开始精确模式提取: {pdf_path}")
            api_key = kwargs.get('api_key', '')
            model_name = kwargs.get('model_name', '')
            model_url = kwargs.get('model_url', '')
            
            if not all([api_key, model_name, model_url]):
                raise ValueError("精确模式需要提供 api_key, model_name, model_url 参数")
                
            result = await service.extract_accurate(
                file_path=pdf_path,
                api_key=api_key,
                model_name=model_name,
                model_url=model_url
            )
            print("提取完成，结果:")
            print(f"  页数: {result['metadata']['total_pages']}")
            print(f"  表格数: {result['metadata']['total_tables']}")
            print(f"  公式数: {result['metadata']['total_formulas']}")
            print(f"  Markdown长度: {len(result['markdown'])} 字符")
            return result
            
        else:
            raise ValueError(f"不支持的模式: {mode}")
            
    except Exception as e:
        print(f"提取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_debug_mode(pdf_path: str, mode: str = "fast", **kwargs):
    """运行调试模式的辅助函数"""
    import asyncio
    asyncio.run(debug_extract(pdf_path, mode, **kwargs))


# ============ 启动服务 ============

if __name__ == "__main__":
    is_debug = False
    if is_debug:
        # test_file_path  ="/home/data/nongwa/workspace/data/阿里开发手册-泰山版-17-25.pdf"
        test_file_path  ="/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"

        #qwen
        # api_key = "sk-"
        # model_name = "qwen3-vl-plus"
        # model_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        #gpt
        # model_url = "https://api.openai.com/v1"
        # api_key = "sk-"
        # model_name = "gpt-4o"

        api_key = "sk-"
        model_name = "gpt-4o"
        model_url = "https://aizex.top/v1"

        run_debug_mode(test_file_path, "accurate", api_key=api_key, model_name=model_name, model_url=model_url)
        print("请在if __name__ == '__main__':中直接调用run_debug_mode函数进行调试")
    else:
        # 启动Web服务
        print("启动PDF提取服务...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8006,
            log_level="info"
        )