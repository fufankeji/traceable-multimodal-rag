import fitz
import sys

def diagnose_pdf(pdf_path):
    """全面诊断PDF文件"""
    print(f"诊断PDF文件: {pdf_path}\n")
    
    try:
        doc = fitz.open(pdf_path)
        print(f"✓ PDF打开成功")
        print(f"总页数: {len(doc)}")
        print(f"是否加密: {doc.is_encrypted}")
        print(f"PDF版本: {doc.metadata.get('format', 'Unknown')}")
        print(f"元数据: {doc.metadata}\n")
        
        # 测试前5页
        for page_num in range(min(5, len(doc))):
            page = doc[page_num]
            print("=" * 60)
            print(f"第 {page_num + 1} 页诊断")
            print("=" * 60)
            
            # 基本信息
            rect = page.rect
            print(f"页面尺寸: {rect.width} x {rect.height}")
            
            # 方法1: 默认get_text()
            text1 = page.get_text()
            print(f"\n方法1 get_text(): {len(text1)} 字符")
            if text1:
                print(f"前200字符:\n{text1[:200]}")
            else:
                print("⚠ 无文本内容")
            
            # 方法2: get_text("text")
            text2 = page.get_text("text")
            print(f"\n方法2 get_text('text'): {len(text2)} 字符")
            if text2 and text2 != text1:
                print(f"前200字符:\n{text2[:200]}")
            
            # 方法3: get_text("dict")
            text_dict = page.get_text("dict")
            blocks = text_dict.get("blocks", [])
            print(f"\n方法3 get_text('dict'): {len(blocks)} 个块")
            
            text_blocks = [b for b in blocks if "lines" in b]
            image_blocks = [b for b in blocks if b.get("type") == 1]
            
            print(f"  - 文本块: {len(text_blocks)}")
            print(f"  - 图片块: {len(image_blocks)}")
            
            if text_blocks:
                print("\n前3个文本块详情:")
                for i, block in enumerate(text_blocks[:3]):
                    print(f"\n  块 {i+1}:")
                    print(f"    bbox: {block['bbox']}")
                    print(f"    行数: {len(block.get('lines', []))}")
                    
                    # 提取块中的文本
                    block_text = []
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                        if line_text.strip():
                            block_text.append(line_text.strip())
                    
                    if block_text:
                        print(f"    内容: {' '.join(block_text[:3])}")  # 显示前3行
            
            # 方法4: get_text("blocks")
            text_blocks_raw = page.get_text("blocks")
            print(f"\n方法4 get_text('blocks'): {len(text_blocks_raw)} 个块")
            if text_blocks_raw:
                print("前3个块:")
                for i, block in enumerate(text_blocks_raw[:3]):
                    # block格式: (x0, y0, x1, y1, "text", block_no, block_type)
                    print(f"  块 {i+1}: {block[4][:100] if len(block[4]) > 100 else block[4]}")
            
            # 检查是否有表格
            try:
                tables = page.find_tables()
                if tables and hasattr(tables, 'tables'):
                    table_count = len(tables.tables)
                elif isinstance(tables, list):
                    table_count = len(tables)
                else:
                    table_count = 0
                print(f"\n表格检测: {table_count} 个表格")
            except Exception as e:
                print(f"\n表格检测失败: {e}")
            
            # 检查是否是扫描页
            if not text1 and image_blocks:
                print("\n⚠ 警告: 此页可能是扫描件（有图片但无文本）")
                print("需要使用OCR技术提取文字")
            
            print()
        
        doc.close()
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 修改为你的PDF路径
    pdf_path = "/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"
    
    diagnose_pdf(pdf_path)