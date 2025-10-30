"""
PDFPlumber纯净版 - 仅使用库的原生能力
不添加任何额外的后处理逻辑
"""
import pdfplumber
import os
from pathlib import Path

def pdf_to_markdown_pure(pdf_path, output_dir="output_pdfplumber", images_folder="images", enable_visualization=False):
    """
    使用PDFPlumber的原生能力转换PDF
    不做任何额外处理
    
    参数:
    - enable_visualization: 是否启用可视化调试（绘制文本框、表格边界等）
    """
    Path(output_dir).mkdir(exist_ok=True,parents=True)
    images_dir = Path(output_dir) / images_folder
    images_dir.mkdir(exist_ok=True,parents=True)
    
    # 可视化输出目录
    if enable_visualization:
        viz_dir = Path(output_dir) / "visualization"
        viz_dir.mkdir(exist_ok=True,parents=True)
    
    pdf_name = Path(pdf_path).stem
    markdown_content = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"处理第 {page_num}/{len(pdf.pages)} 页")
            
            # === 1. 提取文本 - 使用PDFPlumber默认方法 ===
            text = page.extract_text()
            if text:
                markdown_content.append(text)
                # markdown_content.append("\n\n")
            
            # === 2. 提取表格 - 使用PDFPlumber默认方法 ===
            tables = page.extract_tables()
            if tables:
                for table_idx, table in enumerate(tables):
                    if table:
                        md_table = table_to_markdown(table)
                        if md_table:
                            markdown_content.append(md_table)
                            # markdown_content.append("\n\n")
            
            # === 3. 提取图片 - 使用PDFPlumber原生能力 ===
            if hasattr(page, 'images'):
                for img_idx, img in enumerate(page.images):
                    try:
                        # 获取页面边界
                        page_bbox = (0, 0, page.width, page.height)
                        
                        # 裁剪图片区域 - 修正边界框以避免超出页面
                        bbox = (
                            max(img['x0'], 0),
                            max(img['top'], 0),
                            min(img['x1'], page.width),
                            min(img['bottom'], page.height)
                        )
                        
                        # 检查边界框是否有效（宽度和高度都大于0）
                        if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                            cropped = page.crop(bbox)
                            img_obj = cropped.to_image(resolution=150)
                            
                            img_filename = f"page_{page_num}_img_{img_idx + 1}.png"
                            img_path = images_dir / img_filename
                            img_obj.save(str(img_path))
                            
                            markdown_content.append(f"![image]({images_folder}/{img_filename})\n\n")
                    except Exception as e:
                        print(f"  图片 {img_idx + 1} 提取失败: {e}")
            
            # === 4. 保存整页截图 ===
            try:
                page_img = page.to_image(resolution=150)
                img_filename = f"page_{page_num}_full.png"
                img_path = images_dir / img_filename
                page_img.save(str(img_path))
                markdown_content.append(f"![page_{page_num}]({images_folder}/{img_filename})\n\n")
            except Exception as e:
                print(f"  整页截图失败: {e}")
            
            # === 5. 可视化调试（如果启用）===
            if enable_visualization:
                try:
                    print(f"  生成可视化调试图...")
                    viz_img = page.to_image(resolution=150)
                    
                    # 绘制所有字符的边界框（浅蓝色）
                    if page.chars:
                        viz_img.draw_rects(page.chars, stroke="lightblue", stroke_width=1)
                    
                    # 绘制表格边界（红色）
                    if tables:
                        for table in tables:
                            if table:
                                # 绘制表格单元格
                                for row in table:
                                    for cell in row:
                                        if cell:
                                            viz_img.draw_rect(cell, stroke="red", stroke_width=2)
                    
                    # 绘制所有线条（绿色）
                    if hasattr(page, 'lines') and page.lines:
                        viz_img.draw_lines(page.lines, stroke="green", stroke_width=1)
                    
                    # 绘制图片边界（橙色）
                    if hasattr(page, 'images') and page.images:
                        viz_img.draw_rects(page.images, stroke="orange", stroke_width=2)
                    
                    # 保存可视化结果
                    viz_filename = f"page_{page_num}_visualization.png"
                    viz_path = viz_dir / viz_filename
                    viz_img.save(str(viz_path))
                    print(f"  ✓ 可视化保存: {viz_filename}")
                    
                except Exception as e:
                    print(f"  可视化生成失败: {e}")
    
    # 保存Markdown文件
    md_path = Path(output_dir) / f"{pdf_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))
    
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
    
    print("=== PDFPlumber 性能测试 ===\n")
    
    start_time = time.time()
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"总页数: {total_pages}")
        
        # 文本提取
        text_start = time.time()
        total_text_length = 0
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                total_text_length += len(text)
        text_time = time.time() - text_start
        print(f"文本提取: {text_time:.2f}秒, {total_text_length}字符")
        
        # 表格提取
        table_start = time.time()
        total_tables = 0
        for page in pdf.pages:
            tables = page.extract_tables()
            total_tables += len(tables) if tables else 0
        table_time = time.time() - table_start
        print(f"表格提取: {table_time:.2f}秒, {total_tables}个表格")
        
        # 图片检测
        image_start = time.time()
        total_images = 0
        for page in pdf.pages:
            if hasattr(page, 'images'):
                total_images += len(page.images)
        image_time = time.time() - image_start
        print(f"图片检测: {image_time:.2f}秒, {total_images}个图片")
    
    total_time = time.time() - start_time
    print(f"\n总耗时: {total_time:.2f}秒")
    print(f"平均每页: {total_time/total_pages:.2f}秒")

if __name__ == "__main__":
    pdf_path = "/home/data/nongwa/workspace/data/test.pdf"
    output_dir = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/PDFPlumber/output/test-Visualization/test.md"
    
    if os.path.exists(pdf_path):
        # 性能测试
        # performance_test(pdf_path)
        
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
