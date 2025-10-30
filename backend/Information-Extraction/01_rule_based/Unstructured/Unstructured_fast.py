"""
Unstructured纯净版 - 仅使用库的原生能力
不添加任何额外的后处理逻辑
"""
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_to_json
import os
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF用于整页截图

def pdf_to_markdown_pure(pdf_path, output_dir="output_unstructured", images_folder="images", enable_visualization=False):
    """
    使用Unstructured的原生能力转换PDF
    不做任何额外处理
    
    参数:
    - enable_visualization: 是否启用可视化调试（保存元素位置信息的可视化）
    """
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    images_dir = Path(output_dir) / images_folder
    images_dir.mkdir(exist_ok=True, parents=True)
    
    # 可视化输出目录
    if enable_visualization:
        viz_dir = Path(output_dir) / "visualization"
        viz_dir.mkdir(exist_ok=True, parents=True)
    
    pdf_name = Path(pdf_path).stem
    markdown_content = []
    
    print(f"开始使用Unstructured解析PDF...")
    
    # === 使用Unstructured提取所有内容 ===
    # strategy="fast" - 纯规则基础，不使用模型（快速）
    # strategy="hi_res" - 使用视觉检测模型（准确但慢，需要GPU）
    # extract_images_in_pdf=True 提取图片
    # infer_table_structure=True 识别表格结构
    elements = partition_pdf(
        filename=pdf_path,
        strategy="fast",  # 使用fast策略进行纯规则提取
        extract_images_in_pdf=True,
        infer_table_structure=True,
        extract_image_block_output_dir=str(images_dir)
    )
    
    print(f"解析完成，共提取 {len(elements)} 个元素")
    
    # 用于跟踪当前页码
    current_page = 0
    page_elements = {}
    
    # 按页组织元素
    for element in elements:
        page_num = getattr(element.metadata, 'page_number', 1)
        if page_num not in page_elements:
            page_elements[page_num] = []
        page_elements[page_num].append(element)
    
    # 打开PDF用于整页截图
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # 处理每一页
    for page_num in sorted(page_elements.keys()):
        print(f"处理第 {page_num}/{total_pages} 页")
        
        page_content = []
        
        # === 处理该页的所有元素 ===
        for element in page_elements[page_num]:
            element_type = type(element).__name__
            
            # 文本内容
            if hasattr(element, 'text'):
                text = element.text
                if text:
                    page_content.append(text)
            
            # 表格内容（Unstructured会自动转换为HTML或文本）
            if element_type == "Table":
                if hasattr(element, 'metadata') and hasattr(element.metadata, 'text_as_html'):
                    # 如果有HTML格式的表格，转换为Markdown
                    html_table = element.metadata.text_as_html
                    if html_table:
                        # 简单的HTML表格转Markdown（Unstructured原生能力）
                        md_table = html_table_to_markdown(html_table)
                        page_content.append(md_table)
                elif hasattr(element, 'text'):
                    page_content.append(element.text)
            
            # 图片元素
            if element_type == "Image":
                # 检查是否有提取的图片路径
                if hasattr(element.metadata, 'image_path'):
                    img_path = element.metadata.image_path
                    if img_path and os.path.exists(img_path):
                        # 获取相对路径
                        img_filename = Path(img_path).name
                        page_content.append(f"![image]({images_folder}/{img_filename})\n")
        
        # 添加该页内容到总内容
        if page_content:
            markdown_content.extend(page_content)
        
        # === 保存整页截图 ===
        try:
            page = doc[page_num - 1]  # page_number从1开始，索引从0开始
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_filename = f"page_{page_num}_full.png"
            img_path = images_dir / img_filename
            pix.save(str(img_path))
            pix = None
            
            markdown_content.append(f"![page_{page_num}]({images_folder}/{img_filename})\n")
        except Exception as e:
            print(f"  整页截图失败: {e}")
        
        # === 可视化调试（如果启用）===
        if enable_visualization:
            try:
                print(f"  生成可视化调试图...")
                
                page = doc[page_num - 1]
                viz_page = page
                
                # 绘制该页所有元素的边界框
                for element in page_elements[page_num]:
                    if hasattr(element.metadata, 'coordinates'):
                        coords = element.metadata.coordinates
                        if coords and hasattr(coords, 'points'):
                            points = coords.points
                            if len(points) >= 2:
                                # 计算边界框
                                x_coords = [p[0] for p in points]
                                y_coords = [p[1] for p in points]
                                
                                # 根据元素类型选择颜色
                                element_type = type(element).__name__
                                if element_type == "Title":
                                    color = (1, 0, 0)  # 红色 - 标题
                                elif element_type == "Table":
                                    color = (0, 1, 0)  # 绿色 - 表格
                                elif element_type == "Image":
                                    color = (1, 0.5, 0)  # 橙色 - 图片
                                else:
                                    color = (0, 0, 1)  # 蓝色 - 普通文本
                                
                                rect = fitz.Rect(
                                    min(x_coords), 
                                    min(y_coords), 
                                    max(x_coords), 
                                    max(y_coords)
                                )
                                viz_page.draw_rect(rect, color=color, width=2)
                
                # 渲染带标注的页面
                viz_pix = viz_page.get_pixmap(matrix=fitz.Matrix(2, 2))
                viz_filename = f"page_{page_num}_visualization.png"
                viz_path = viz_dir / viz_filename
                viz_pix.save(str(viz_path))
                viz_pix = None
                
                print(f"  ✓ 可视化保存: {viz_filename}")
                
            except Exception as e:
                print(f"  可视化生成失败: {e}")
    
    doc.close()
    
    # 保存Markdown文件
    md_path = Path(output_dir) / f"{pdf_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_content))
    
    print(f"完成！输出: {md_path}")
    return str(md_path)

def html_table_to_markdown(html_table):
    """
    直接返回Unstructured提供的HTML表格内容
    不做额外转换，保持Unstructured原生能力
    """
    # 直接返回HTML格式或原始文本
    return html_table

def performance_test(pdf_path):
    """性能测试"""
    import time
    
    print("=== Unstructured 性能测试 ===\n")
    
    start_time = time.time()
    
    # 基础解析（fast策略 - 纯规则）
    print("测试基础解析速度（fast策略 - 纯规则）...")
    basic_start = time.time()
    elements_basic = partition_pdf(
        filename=pdf_path,
        strategy="fast",
        extract_images_in_pdf=False,
        infer_table_structure=True
    )
    basic_time = time.time() - basic_start
    print(f"基础解析: {basic_time:.2f}秒, {len(elements_basic)}个元素")
    
    # 统计元素类型
    print("\n元素类型统计:")
    element_types = {}
    for element in elements_basic:
        element_type = type(element).__name__
        element_types[element_type] = element_types.get(element_type, 0) + 1
    
    for elem_type, count in sorted(element_types.items()):
        print(f"  {elem_type}: {count}")
    
    # 页数统计
    pages = set()
    for element in elements_basic:
        if hasattr(element.metadata, 'page_number'):
            pages.add(element.metadata.page_number)
    total_pages = len(pages) if pages else 0
    
    total_time = time.time() - start_time
    print(f"\n总页数: {total_pages}")
    print(f"总耗时: {total_time:.2f}秒")
    if total_pages > 0:
        print(f"平均每页: {total_time/total_pages:.2f}秒")

if __name__ == "__main__":
    pdf_path = "/home/data/nongwa/workspace/data/test.pdf"
    output_dir = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/Unstructured/output/test-Visualization"
    
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