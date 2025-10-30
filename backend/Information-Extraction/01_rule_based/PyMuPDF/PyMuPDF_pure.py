"""
PyMuPDF纯净版 - 仅使用库的原生能力
不添加任何额外的后处理逻辑
"""
import fitz  # PyMuPDF
import os
from pathlib import Path

def pdf_to_markdown_pure(pdf_path, output_dir="output_pymupdf", images_folder="images", enable_visualization=False):
    """
    使用PyMuPDF的原生能力转换PDF
    不做任何额外处理
    
    参数:
    - enable_visualization: 是否启用可视化调试（在页面上绘制检测结果）
    """
    Path(output_dir).mkdir(exist_ok=True,parents=True)
    images_dir = Path(output_dir) / images_folder
    images_dir.mkdir(exist_ok=True,parents=True)
    
    # 可视化输出目录
    if enable_visualization:
        viz_dir = Path(output_dir) / "visualization"
        viz_dir.mkdir(exist_ok=True,parents=True)
    
    doc = fitz.open(pdf_path)
    pdf_name = Path(pdf_path).stem
    markdown_content = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"处理第 {page_num + 1}/{len(doc)} 页")
        
        # === 1. 提取文本 - 使用PyMuPDF默认方法 ===
        text = page.get_text()
        if text:
            markdown_content.append(text)
            # markdown_content.append("\n\n")
        
        # === 2. 提取表格 - 使用PyMuPDF原生能力 ===
        try:
            tables = page.find_tables()
            if tables:
                # 处理TableFinder对象
                if hasattr(tables, 'tables'):
                    table_list = tables.tables
                elif isinstance(tables, list):
                    table_list = tables
                else:
                    table_list = [tables]
                
                for table in table_list:
                    if hasattr(table, 'extract'):
                        table_data = table.extract()
                        if table_data:
                            md_table = table_to_markdown(table_data)
                            if md_table:
                                markdown_content.append(md_table)
                                # markdown_content.append("\n\n")
        except Exception as e:
            print(f"  表格提取失败: {e}")
        
        # === 3. 提取图片 - 使用PyMuPDF原生能力 ===
        try:
            text_dict = page.get_text("dict")
            img_count = 0
            
            for block in text_dict.get("blocks", []):
                if block.get("type") == 1:  # 图片块
                    try:
                        bbox = block.get("bbox")
                        if bbox:
                            rect = fitz.Rect(bbox)
                            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect)
                            
                            if pix.width > 10 and pix.height > 10:
                                img_filename = f"page_{page_num + 1}_img_{img_count + 1}.png"
                                img_path = images_dir / img_filename
                                pix.save(str(img_path))
                                
                                # markdown_content.append(f"![image]({images_folder}/{img_filename})\n\n")
                                markdown_content.append(f"![image]({images_folder}/{img_filename})\n")
                                img_count += 1
                            
                            pix = None
                    except Exception as e:
                        print(f"  图片块提取失败: {e}")
        except Exception as e:
            print(f"  图片提取失败: {e}")
        
        # === 4. 保存整页截图 ===
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_filename = f"page_{page_num + 1}_full.png"
            img_path = images_dir / img_filename
            pix.save(str(img_path))
            pix = None
            
            # markdown_content.append(f"![page_{page_num + 1}]({images_folder}/{img_filename})\n\n")
            markdown_content.append(f"![page_{page_num + 1}]({images_folder}/{img_filename})\n")
        except Exception as e:
            print(f"  整页截图失败: {e}")
        
        # === 5. 可视化调试（如果启用）===
        if enable_visualization:
            try:
                print(f"  生成可视化调试图...")
                
                # 创建一个临时文档用于绘制
                viz_page = page
                
                # 绘制文本块边界（蓝色）
                text_dict = page.get_text("dict")
                for block in text_dict.get("blocks", []):
                    if "lines" in block:  # 文本块
                        rect = fitz.Rect(block["bbox"])
                        viz_page.draw_rect(rect, color=(0, 0, 1), width=1)
                
                # 绘制表格边界（红色）
                try:
                    tables = page.find_tables()
                    if tables and hasattr(tables, 'tables'):
                        for table in tables.tables:
                            if hasattr(table, 'bbox'):
                                rect = fitz.Rect(table.bbox)
                                viz_page.draw_rect(rect, color=(1, 0, 0), width=2)
                except:
                    pass
                
                # 绘制图片块边界（橙色）
                for block in text_dict.get("blocks", []):
                    if block.get("type") == 1:  # 图片块
                        rect = fitz.Rect(block["bbox"])
                        viz_page.draw_rect(rect, color=(1, 0.5, 0), width=2)
                
                # 渲染带标注的页面
                viz_pix = viz_page.get_pixmap(matrix=fitz.Matrix(2, 2))
                viz_filename = f"page_{page_num + 1}_visualization.png"
                viz_path = viz_dir / viz_filename
                viz_pix.save(str(viz_path))
                viz_pix = None
                
                print(f"  ✓ 可视化保存: {viz_filename}")
                
            except Exception as e:
                print(f"  可视化生成失败: {e}")
    
    # 保存Markdown文件
    md_path = Path(output_dir) / f"{pdf_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))
    
    doc.close()
    print(f"完成！输出: {md_path}")
    return str(md_path)

def table_to_markdown(table):
    """
    将表格转换为Markdown格式
    最小化处理，只做必要的格式转换
    """
    if not table or not any(table):
        return ""
    
    lines = []
    
    # 表头
    header = table[0]
    header_cells = [str(cell) if cell else "" for cell in header]
    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")
    
    # 数据行
    for row in table[1:]:
        cells = [str(cell) if cell else "" for cell in row]
        # 补齐列数
        while len(cells) < len(header_cells):
            cells.append("")
        lines.append("| " + " | ".join(cells[:len(header_cells)]) + " |")
    
    return "\n".join(lines)

def performance_test(pdf_path):
    """性能测试"""
    import time
    
    print("=== PyMuPDF 性能测试 ===\n")
    
    start_time = time.time()
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"总页数: {total_pages}")
    
    # 文本提取
    text_start = time.time()
    total_text_length = 0
    for page in doc:
        text = page.get_text()
        if text:
            total_text_length += len(text)
    text_time = time.time() - text_start
    print(f"文本提取: {text_time:.2f}秒, {total_text_length}字符")
    
    # 表格提取
    table_start = time.time()
    total_tables = 0
    for page in doc:
        try:
            tables = page.find_tables()
            if tables:
                if hasattr(tables, 'tables'):
                    total_tables += len(tables.tables) if tables.tables else 0
                elif isinstance(tables, list):
                    total_tables += len(tables)
                else:
                    total_tables += 1
        except:
            pass
    table_time = time.time() - table_start
    print(f"表格提取: {table_time:.2f}秒, {total_tables}个表格")
    
    # 图片检测
    image_start = time.time()
    total_images = 0
    for page in doc:
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") == 1:
                total_images += 1
    image_time = time.time() - image_start
    print(f"图片检测: {image_time:.2f}秒, {total_images}个图片")
    
    doc.close()
    
    total_time = time.time() - start_time
    print(f"\n总耗时: {total_time:.2f}秒")
    print(f"平均每页: {total_time/total_pages:.2f}秒")

if __name__ == "__main__":
    pdf_path = "/home/data/nongwa/workspace/data/test.pdf"
    output_dir = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/PyMuPDF/output/test-Visualization/test.md"
    
    if os.path.exists(pdf_path):
        # 性能测试
        performance_test(pdf_path)
        
        print("\n" + "="*60)
        print("开始转换...")
        print("="*60 + "\n")
        
        # 完整转换（可选：启用可视化）
        # 设置 enable_visualization=True 启用可视化调试
        pdf_to_markdown_pure(
            pdf_path, 
            output_dir,
            enable_visualization=True  # 改为True启用可视化
        )
    else:
        print(f"文件不存在: {pdf_path}")
