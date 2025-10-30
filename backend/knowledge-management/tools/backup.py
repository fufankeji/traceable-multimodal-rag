"""
数据库备份和恢复工具
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
from database.sql_db import SessionLocal, SQLDBManager
from database.milvus_db import milvus_manager
import asyncio

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        self.backup_dir = BACKUP_DIR
    
    def backup_sql(self, backup_name: str = None) -> Path:
        """备份SQL数据库"""
        if not backup_name:
            backup_name = f"sql_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        db = SessionLocal()
        try:
            sql_manager = SQLDBManager(db)
            
            # 导出所有数据
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "knowledge_bases": []
            }
            
            # 获取所有知识库
            kbs = sql_manager.list_knowledge_bases()
            
            for kb in kbs:
                kb_data = {
                    "name": kb.name,
                    "file_count": kb.file_count,
                    "created_at": kb.created_at.isoformat(),
                    "files": []
                }
                
                # 获取知识库的所有文件
                files = sql_manager.get_files_by_knowledge_base(kb.name)
                
                for file in files:
                    file_data = {
                        "file_id": file.file_id,
                        "filename": file.filename,
                        "chunk_count": file.chunk_count,
                        "metadata": file.metadata,
                        "created_at": file.created_at.isoformat(),
                        "chunks": []
                    }
                    
                    # 获取文件的所有chunks
                    chunks = sql_manager.get_chunks_by_file(file.file_id)
                    
                    for chunk in chunks:
                        chunk_data = {
                            "chunk_id": chunk.chunk_id,
                            "text": chunk.text,
                            "page_start": chunk.page_start,
                            "page_end": chunk.page_end,
                            "text_length": chunk.text_length,
                            "metadata": chunk.metadata,
                            "created_at": chunk.created_at.isoformat()
                        }
                        file_data["chunks"].append(chunk_data)
                    
                    kb_data["files"].append(file_data)
                
                backup_data["knowledge_bases"].append(kb_data)
            
            # 保存到文件
            backup_file = self.backup_dir / f"{backup_name}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ SQL数据库备份成功: {backup_file}")
            return backup_file
            
        finally:
            db.close()
    
    def restore_sql(self, backup_file: Path):
        """恢复SQL数据库"""
        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_file}")
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        db = SessionLocal()
        try:
            sql_manager = SQLDBManager(db)
            
            print(f"开始恢复备份: {backup_file}")
            
            for kb_data in backup_data["knowledge_bases"]:
                # 创建知识库
                kb = sql_manager.create_knowledge_base(kb_data["name"])
                print(f"  恢复知识库: {kb_data['name']}")
                
                for file_data in kb_data["files"]:
                    # 创建文件
                    file = sql_manager.create_file(
                        file_id=file_data["file_id"],
                        filename=file_data["filename"],
                        knowledge_base_name=kb_data["name"],
                        metadata=file_data["metadata"]
                    )
                    print(f"    恢复文件: {file_data['filename']}")
                    
                    for chunk_data in file_data["chunks"]:
                        # 创建chunk（注意：这里没有恢复向量，只恢复元数据）
                        sql_manager.create_chunk(
                            file_id=file_data["file_id"],
                            text=chunk_data["text"],
                            page_start=chunk_data["page_start"],
                            page_end=chunk_data["page_end"],
                            text_length=chunk_data["text_length"],
                            metadata=chunk_data["metadata"]
                        )
            
            print("✅ SQL数据库恢复成功")
            
        finally:
            db.close()
    
    def backup_milvus_collections(self) -> Dict[str, Path]:
        """导出Milvus collection信息（不包括向量数据）"""
        collections = milvus_manager.list_collections()
        backup_info = {}
        
        for collection_name in collections:
            if not collection_name.startswith("kb_"):
                continue
            
            try:
                collection = milvus_manager.get_collection(
                    collection_name.replace("kb_", "")
                )
                
                backup_info[collection_name] = {
                    "name": collection_name,
                    "schema": str(collection.schema),
                    "num_entities": collection.num_entities
                }
            except Exception as e:
                print(f"警告: 无法获取collection信息 {collection_name}: {e}")
        
        # 保存collection信息
        backup_name = f"milvus_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_file = self.backup_dir / backup_name
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Milvus collection信息备份成功: {backup_file}")
        return backup_file
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.json"):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def delete_backup(self, backup_filename: str):
        """删除备份"""
        backup_file = self.backup_dir / backup_filename
        if backup_file.exists():
            backup_file.unlink()
            print(f"✅ 备份已删除: {backup_filename}")
        else:
            print(f"❌ 备份不存在: {backup_filename}")

def main():
    """命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG知识库备份工具")
    parser.add_argument("action", choices=["backup", "restore", "list"], help="操作类型")
    parser.add_argument("--file", help="备份文件名（用于restore）")
    parser.add_argument("--name", help="备份名称（用于backup）")
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.action == "backup":
        print("开始备份...")
        sql_backup = manager.backup_sql(args.name)
        milvus_backup = manager.backup_milvus_collections()
        print(f"\n备份完成!")
        print(f"SQL备份: {sql_backup}")
        print(f"Milvus信息: {milvus_backup}")
    
    elif args.action == "restore":
        if not args.file:
            print("错误: 请指定备份文件 --file")
            return
        
        backup_file = BACKUP_DIR / args.file
        print(f"开始恢复: {backup_file}")
        manager.restore_sql(backup_file)
        print("\n恢复完成!")
        print("注意: 向量数据需要重新生成，请重新上传文件或使用重新索引功能")
    
    elif args.action == "list":
        backups = manager.list_backups()
        print(f"\n找到 {len(backups)} 个备份:")
        for backup in backups:
            print(f"  - {backup['filename']}")
            print(f"    大小: {backup['size']/1024:.2f} KB")
            print(f"    创建时间: {backup['created']}")
            print()

if __name__ == "__main__":
    main()