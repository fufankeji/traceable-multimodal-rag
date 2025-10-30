"""
PyMuPDF4LLM纯净版 - 仅使用库的原生能力
不添加任何额外的后处理逻辑
"""
import pymupdf4llm
import fitz  # PyMuPDF (用于提取页面截图)
import os
from pathlib import Path

def pdf_to_markdown_pure(pdf_path, output_dir="output_pymupdf4llm", images_folder="images", enable_visualization=False):
    """
    使用PyMuPDF4LLM的原生能力转换PDF
    不做任何额外处理
    
    参数:
    - pdf_path: PDF文件路径
    - output_dir: 输出目录
    - images_folder: 图片文件夹名称
    - enable_visualization: 是否启用可视化调试（在页面上绘制检测结果）
    """
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    images_dir = Path(output_dir) / images_folder
    images_dir.mkdir(exist_ok=True, parents=True)
    
    # 可视化输出目录
    if enable_visualization:
        viz_dir = Path(output_dir) / "visualization"
        viz_dir.mkdir(exist_ok=True, parents=True)
    
    pdf_name = Path(pdf_path).stem
    
    print(f"开始处理PDF: {pdf_name}")
    
    # === 使用PyMuPDF4LLM提取Markdown内容 ===
    # PyMuPDF4LLM会自动处理文本、表格等内容
    md_data = pymupdf4llm.to_markdown(
        pdf_path,
        page_chunks=True,  # 分页输出，便于处理
        write_images=True,  # 提取图片
        image_path=str(images_dir),  # 图片保存路径
        image_format="png",  # 图片格式
        dpi=150  # 图片分辨率
    )
    
    # 处理PyMuPDF4LLM返回的数据（可能是list或str）
    markdown_content = []
    
    if isinstance(md_data, list):
        # 如果是列表，遍历每页
        for page_data in md_data:
            if isinstance(page_data, dict):
                text = page_data.get('text', '')
                # 将绝对路径转换为相对路径
                text = text.replace(str(images_dir.absolute()), images_folder)
                markdown_content.append(text)
            else:
                markdown_content.append(str(page_data))
    else:
        # 如果是字符串，直接使用
        text = str(md_data)
        # 将绝对路径转换为相对路径
        text = text.replace(str(images_dir.absolute()), images_folder)
        markdown_content.append(text)
    
    print(f"\n为每页添加完整截图...")
    # 打开文档以生成整页截图和可视化
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"  处理第 {page_num + 1}/{len(doc)} 页")
        
        # 保存整页截图
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_filename = f"page_{page_num + 1}_full.png"
            img_path = images_dir / img_filename
            pix.save(str(img_path))
            pix = None
            
            # 添加到markdown内容
            markdown_content.append(f"\n---\n\n![page_{page_num + 1}]({images_folder}/{img_filename})\n\n")
        except Exception as e:
            print(f"    整页截图失败: {e}")
        
        # === 可视化调试（如果启用）===
        if enable_visualization:
            try:
                print(f"    生成可视化调试图...")
                
                # 创建可视化页面
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
                
                print(f"    ✓ 可视化保存: {viz_filename}")
                
            except Exception as e:
                print(f"    可视化生成失败: {e}")
    
    doc.close()
    
    # === 保存Markdown文件 ===
    md_path = Path(output_dir) / f"{pdf_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))
    
    print(f"\n完成！输出: {md_path}")
    return str(md_path)

def performance_test(pdf_path):
    """性能测试"""
    import time
    
    print("=== PyMuPDF4LLM 性能测试 ===\n")
    
    start_time = time.time()
    
    # 打开文档获取基本信息
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"总页数: {total_pages}")
    doc.close()
    
    # PyMuPDF4LLM转换
    conversion_start = time.time()
    md_text = pymupdf4llm.to_markdown(pdf_path, page_chunks=False, write_images=False)
    conversion_time = time.time() - conversion_start
    
    print(f"Markdown转换: {conversion_time:.2f}秒")
    print(f"输出长度: {len(md_text)}字符")
    
    total_time = time.time() - start_time
    print(f"\n总耗时: {total_time:.2f}秒")
    print(f"平均每页: {total_time/total_pages:.2f}秒")

if __name__ == "__main__":
    pdf_path = "/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"
    output_dir = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/PyMuPDF4LLM/output/阿里开发手册-泰山版"
    
    if os.path.exists(pdf_path):
        # 性能测试
        performance_test(pdf_path)
        
        print("\n" + "="*60)
        print("开始转换...")
        print("="*60 + "\n")
        
        # 完整转换
        pdf_to_markdown_pure(
            pdf_path, 
            output_dir,
            enable_visualization=True  # 改为True启用可视化
        )
    else:
        print(f"文件不存在: {pdf_path}")