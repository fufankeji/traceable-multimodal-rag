"""
RAG知识库管理系统 - 系统测试脚本
用于快速验证系统各项功能是否正常
"""
import httpx
import asyncio
import json
import os
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

async def test_health_check():
    """测试健康检查"""
    print("\n" + "="*50)
    print_info("测试 1: 健康检查")
    print("="*50)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print_success("服务健康检查通过")
                return True
            else:
                print_error("服务健康检查失败")
                return False
    except Exception as e:
        print_error(f"无法连接到服务: {e}")
        return False

async def test_upload():
    """测试文件上传"""
    print("\n" + "="*50)
    print_info("测试 2: 文件上传")
    print("="*50)
    
    upload_data = {
        "knowledge_base_name": "测试知识库",
        "filename": "test_document.txt",
        "chunks": [
            {
                "page_start": 1,
                "page_end": 1,
                "pages": [1],
                "text": "这是一个测试文档。人工智能是计算机科学的一个分支。",
                "text_length": 28,
                "continued": False,
                "cross_page_bridge": False,
                "is_table_like": False
            },
            {
                "page_start": 2,
                "page_end": 2,
                "pages": [2],
                "text": "机器学习是人工智能的核心技术之一，包括监督学习、无监督学习和强化学习。",
                "text_length": 38,
                "continued": False,
                "cross_page_bridge": False,
                "is_table_like": False
            }
        ],
        "metadata": {
            "source": "test",
            "created_by": "test_system"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/upload",
                json=upload_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print_success("文件上传成功")
                print_info(f"文件ID: {result['file_id']}")
                print_info(f"Chunk数量: {result['chunk_count']}")
                return result['file_id'], result['knowledge_base_name']
            else:
                print_error(f"文件上传失败: {response.text}")
                return None, None
                
    except Exception as e:
        print_error(f"文件上传异常: {e}")
        return None, None

async def test_list_knowledge_bases():
    """测试列出知识库"""
    print("\n" + "="*50)
    print_info("测试 3: 列出知识库")
    print("="*50)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/knowledge-bases")
            
            if response.status_code == 200:
                result = response.json()
                print_success(f"找到 {result['total']} 个知识库")
                for kb in result['knowledge_bases']:
                    print_info(f"  - {kb['name']} ({kb['file_count']} 个文件)")
                return True
            else:
                print_error("列出知识库失败")
                return False
                
    except Exception as e:
        print_error(f"列出知识库异常: {e}")
        return False

async def test_search(kb_name):
    """测试向量检索"""
    print("\n" + "="*50)
    print_info("测试 4: 向量检索")
    print("="*50)
    
    search_data = {
        "knowledge_base_name": kb_name,
        "query": "什么是机器学习？",
        "top_k": 3,
        "similarity_threshold": 0.0
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/search",
                json=search_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print_success(f"检索成功，找到 {result['count']} 个相关结果")
                for i, res in enumerate(result['results'], 1):
                    print_info(f"  结果 {i}:")
                    print(f"    相似度: {res['similarity_score']:.4f}")
                    print(f"    文本: {res['chunk_text'][:50]}...")
                return len(result['results']) > 0
            else:
                print_error("检索失败")
                return False
                
    except Exception as e:
        print_error(f"检索异常: {e}")
        return False

async def test_list_files(kb_name):
    """测试列出文件"""
    print("\n" + "="*50)
    print_info("测试 5: 列出文件")
    print("="*50)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/knowledge-base/{kb_name}/files"
            )
            
            if response.status_code == 200:
                result = response.json()
                print_success(f"找到 {result['total']} 个文件")
                for file in result['files']:
                    print_info(f"  - {file['filename']} ({file['chunk_count']} chunks)")
                return True
            else:
                print_error("列出文件失败")
                return False
                
    except Exception as e:
        print_error(f"列出文件异常: {e}")
        return False

async def test_delete_file(file_id, kb_name):
    """测试删除文件"""
    print("\n" + "="*50)
    print_info("测试 6: 删除文件")
    print("="*50)
    
    delete_data = {
        "file_id": file_id,
        "knowledge_base_name": kb_name
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BASE_URL}/file",
                json=delete_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print_success("文件删除成功")
                    print_info(f"删除了 {result['deleted_chunks']} 个chunks")
                    return True
                else:
                    print_error(f"文件删除失败: {result['message']}")
                    return False
            else:
                print_error("文件删除失败")
                return False
                
    except Exception as e:
        print_error(f"文件删除异常: {e}")
        return False

async def test_delete_knowledge_base(kb_name):
    """测试删除知识库"""
    print("\n" + "="*50)
    print_info("测试 7: 删除知识库")
    print("="*50)
    
    delete_data = {
        "knowledge_base_name": kb_name
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BASE_URL}/knowledge-base",
                json=delete_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print_success("知识库删除成功")
                    print_info(f"删除了 {result['deleted_files']} 个文件")
                    print_info(f"删除了 {result['deleted_chunks']} 个chunks")
                    return True
                else:
                    print_error(f"知识库删除失败: {result['message']}")
                    return False
            else:
                print_error("知识库删除失败")
                return False
                
    except Exception as e:
        print_error(f"知识库删除异常: {e}")
        return False

async def main():
    """主测试流程"""
    print("\n")
    print("="*50)
    print(f"{Colors.BLUE}RAG知识库管理系统 - 系统测试{Colors.END}")
    print("="*50)
    
    results = []
    
    # 1. 健康检查
    result = await test_health_check()
    results.append(("健康检查", result))
    if not result:
        print_error("\n服务未启动或无法访问，请先启动服务")
        return
    
    # 2. 上传文件
    file_id, kb_name = await test_upload()
    results.append(("文件上传", file_id is not None))
    if not file_id:
        print_error("\n文件上传失败，无法继续后续测试")
        return
    
    # 等待一下，让数据完全写入
    await asyncio.sleep(2)
    
    # 3. 列出知识库
    result = await test_list_knowledge_bases()
    results.append(("列出知识库", result))
    
    # 4. 检索
    result = await test_search(kb_name)
    results.append(("向量检索", result))
    
    # 5. 列出文件
    result = await test_list_files(kb_name)
    results.append(("列出文件", result))
    
    # 6. 删除文件
    result = await test_delete_file(file_id, kb_name)
    results.append(("删除文件", result))
    
    # 7. 删除知识库
    result = await test_delete_knowledge_base(kb_name)
    results.append(("删除知识库", result))
    
    # 打印测试总结
    print("\n" + "="*50)
    print(f"{Colors.BLUE}测试总结{Colors.END}")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: 通过")
        else:
            print_error(f"{test_name}: 失败")
    
    print("\n" + "="*50)
    if passed == total:
        print_success(f"所有测试通过！({passed}/{total})")
    else:
        print_warning(f"部分测试失败 ({passed}/{total})")
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print_error(f"\n测试过程中发生错误: {e}")

class Config:
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./knowledge_management.db")
    
    # Milvus配置
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    
    # Embedding配置
    EMBEDDING_MODEL_URL: str = os.getenv("EMBEDDING_MODEL_URL", "http://localhost:8080/embeddings")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))
    
    # 系统配置
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "knowledge_management.log")

config = Config()