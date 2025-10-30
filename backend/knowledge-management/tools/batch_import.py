"""
批量导入工具
用于批量上传JSON格式的文档到知识库
"""
import asyncio
import httpx
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import argparse

class BatchImporter:
    """批量导入器"""
    
    def __init__(self, api_url: str = "http://localhost:8000/api/v1"):
        self.api_url = api_url
        self.results = []
    
    async def import_file(self, file_path: Path, knowledge_base_name: str) -> Dict:
        """导入单个文件"""
        try:
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取需要的数据
            if "data" in data and "chunks" in data["data"]:
                # 格式1: 类似你提供的JSON格式
                filename = data.get("filename", file_path.name)
                chunks = data["data"]["chunks"]
                metadata = data["data"].get("metadata", {})
            elif "chunks" in data:
                # 格式2: 简化格式
                filename = data.get("filename", file_path.name)
                chunks = data["chunks"]
                metadata = data.get("metadata", {})
            else:
                raise ValueError("不支持的JSON格式")
            
            # 构建上传请求
            upload_data = {
                "knowledge_base_name": knowledge_base_name,
                "filename": filename,
                "chunks": chunks,
                "metadata": metadata
            }
            
            # 发送请求
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.api_url}/upload",
                    json=upload_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "file": str(file_path),
                        "filename": filename,
                        "file_id": result["file_id"],
                        "chunk_count": result["chunk_count"]
                    }
                else:
                    return {
                        "success": False,
                        "file": str(file_path),
                        "error": response.text
                    }
        
        except Exception as e:
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }
    
    async def import_directory(
        self,
        directory: Path,
        knowledge_base_name: str,
        recursive: bool = False,
        max_concurrent: int = 3
    ) -> List[Dict]:
        """批量导入目录中的所有JSON文件"""
        
        # 获取所有JSON文件
        if recursive:
            json_files = list(directory.rglob("*.json"))
        else:
            json_files = list(directory.glob("*.json"))
        
        print(f"找到 {len(json_files)} 个JSON文件")
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def import_with_semaphore(file_path):
            async with semaphore:
                print(f"正在导入: {file_path.name}")
                result = await self.import_file(file_path, knowledge_base_name)
                
                if result["success"]:
                    print(f"  ✅ 成功: {result['filename']} ({result['chunk_count']} chunks)")
                else:
                    print(f"  ❌ 失败: {file_path.name} - {result['error']}")
                
                return result
        
        # 并发导入
        tasks = [import_with_semaphore(f) for f in json_files]
        self.results = await asyncio.gather(*tasks)
        
        return self.results
    
    def generate_report(self) -> Dict:
        """生成导入报告"""
        total = len(self.results)
        success = sum(1 for r in self.results if r["success"])
        failed = total - success
        
        total_chunks = sum(r.get("chunk_count", 0) for r in self.results if r["success"])
        
        report = {
            "summary": {
                "total_files": total,
                "successful": success,
                "failed": failed,
                "success_rate": f"{success/total*100:.2f}%" if total > 0 else "0%",
                "total_chunks": total_chunks
            },
            "failed_files": [
                {
                    "file": r["file"],
                    "error": r.get("error", "未知错误")
                }
                for r in self.results if not r["success"]
            ],
            "successful_files": [
                {
                    "file": r["file"],
                    "filename": r["filename"],
                    "file_id": r["file_id"],
                    "chunk_count": r["chunk_count"]
                }
                for r in self.results if r["success"]
            ]
        }
        
        return report
    
    def save_report(self, output_file: Path):
        """保存报告到文件"""
        report = self.generate_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n报告已保存到: {output_file}")

async def main():
    """命令行工具"""
    parser = argparse.ArgumentParser(description="RAG知识库批量导入工具")
    parser.add_argument("directory", type=Path, help="包含JSON文件的目录")
    parser.add_argument("knowledge_base", help="目标知识库名称")
    parser.add_argument("--recursive", "-r", action="store_true", help="递归搜索子目录")
    parser.add_argument("--concurrent", "-c", type=int, default=3, help="最大并发数（默认3）")
    parser.add_argument("--api-url", default="http://localhost:8000/api/v1", help="API地址")
    parser.add_argument("--report", type=Path, help="报告输出文件路径")
    
    args = parser.parse_args()
    
    if not args.directory.exists():
        print(f"错误: 目录不存在 {args.directory}")
        return
    
    print("="*60)
    print("RAG知识库批量导入工具")
    print("="*60)
    print(f"源目录: {args.directory}")
    print(f"知识库: {args.knowledge_base}")
    print(f"递归搜索: {'是' if args.recursive else '否'}")
    print(f"最大并发: {args.concurrent}")
    print("="*60)
    print()
    
    # 创建导入器
    importer = BatchImporter(args.api_url)
    
    # 开始导入
    start_time = datetime.now()
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    await importer.import_directory(
        directory=args.directory,
        knowledge_base_name=args.knowledge_base,
        recursive=args.recursive,
        max_concurrent=args.concurrent
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 生成报告
    print()
    print("="*60)
    print("导入完成!")
    print("="*60)
    
    report = importer.generate_report()
    
    print(f"\n总文件数: {report['summary']['total_files']}")
    print(f"成功: {report['summary']['successful']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"成功率: {report['summary']['success_rate']}")
    print(f"总Chunks: {report['summary']['total_chunks']}")
    print(f"总耗时: {duration:.2f}秒")
    
    if report['failed_files']:
        print(f"\n失败的文件:")
        for failed in report['failed_files'][:10]:  # 只显示前10个
            print(f"  - {failed['file']}")
            print(f"    错误: {failed['error']}")
    
    # 保存报告
    if args.report:
        importer.save_report(args.report)
    else:
        report_file = Path(f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        importer.save_report(report_file)

if __name__ == "__main__":
    asyncio.run(main())