import pdfplumber
import os
import time
from typing import List, Tuple, Optional

def pdf_to_markdown(pdf_path, output_path=None, extract_tables=True, extract_images=True, 
                   images_folder="images", debug=False, padding=5):
    """
    使用pdfplumber将PDF转换为Markdown
    改进版：更好地避免文本和表格重复提取
    
    参数:
    - pdf_path: PDF文件路径
    - output_path: 输出MD文件路径
    - extract_tables: 是否提取表格
    - extract_images: 是否提取图片
    - images_folder: 图片文件夹名称
    - debug: 是否显示调试信息
    - padding: 表格边界框扩展像素数
    """
    
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '.md'
    
    # 创建图片文件夹
    if extract_images:
        output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else "."
        images_dir = os.path.join(output_dir, images_folder)
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
    
    markdown_content = []
    image_counter = 1
    total_duplicates = 0
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            if debug:
                print(f"开始处理PDF: {pdf_path}")
                print(f"总页数: {total_pages}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                if debug:
                    print(f"\n--- 处理第 {page_num} 页 ---")
                
                # 设置表格检测参数
                table_settings = {
                    "vertical_strategy": "lines",      # 或 "text" / "explicit"
                    "horizontal_strategy": "lines",    # 或 "text"
                    "intersection_x_tolerance": 5,
                    "intersection_y_tolerance": 5,
                }
                
                # 提取文本（排除表格区域）
                text, tables_found, table_bboxes = extract_text_excluding_tables(
                    page, table_settings=table_settings, padding=padding, debug=debug
                )
                
                # 验证文本和表格分离效果
                if debug and text and tables_found:
                    duplicates = validate_text_table_separation(page, text, tables_found)
                    total_duplicates += len(duplicates)
                    if duplicates:
                        print(f"  发现 {len(duplicates)} 个可能的重复内容")
                
                # 添加文本内容
                if text and text.strip():
                    markdown_content.append(text)
                    markdown_content.append("\n\n")
                
                # 提取表格
                if extract_tables:
                    table_count = process_tables(page, tables_found, markdown_content, debug)
                    if debug:
                        print(f"  处理了 {table_count} 个表格")
                
                # 提取图片
                if extract_images:
                    saved_images = extract_page_images(page, images_dir, image_counter, images_folder, debug)
                    for img_md in saved_images:
                        markdown_content.append(img_md)
                        image_counter += 1
        
        # 保存文件
        final_content = ''.join(markdown_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # 输出统计信息
        print(f"\n转换完成: {output_path}")
        print(f"处理页数: {total_pages}")
        print(f"输出文件大小: {len(final_content)} 字符")
        if extract_images and image_counter > 1:
            print(f"提取图片数量: {image_counter - 1}")
        if debug and total_duplicates > 0:
            print(f"警告：总共发现 {total_duplicates} 个可能的重复内容")
        
        return output_path
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def extract_text_excluding_tables(page, table_settings=None, padding=5, debug=False):
    """
    从页面提取正文文本，排除表格区域里的字符
    
    参数:
    - page: pdfplumber页面对象
    - table_settings: 传给find_tables的参数
    - padding: 给表格bbox四周加的边距
    - debug: 是否显示调试信息
    
    返回:
    - text: 提取的文本
    - tables: 检测到的表格对象列表
    - table_bboxes: 表格边界框列表
    """
    
    # 1) 多种方法检测表格
    tables = []
    table_bboxes = []
    
    # 方法1：使用 find_tables（推荐）
    try:
        if hasattr(page, "find_tables"):
            tables = page.find_tables(table_settings=table_settings)
            table_bboxes = [t.bbox for t in tables if getattr(t, "bbox", None)]
            if debug:
                print(f"    find_tables 检测到 {len(tables)} 个表格")
    except Exception as e:
        if debug:
            print(f"    find_tables 失败: {e}")
    
    # 方法2：如果没检测到表格，尝试 extract_tables 作为备选
    if not tables:
        try:
            extracted_tables = page.extract_tables()
            if extracted_tables:
                # extract_tables返回的是数据，我们需要估算位置
                # 这比较复杂，暂时跳过位置检测
                if debug:
                    print(f"    extract_tables 检测到 {len(extracted_tables)} 个表格（无位置信息）")
        except Exception as e:
            if debug:
                print(f"    extract_tables 失败: {e}")
    
    # 2) 基于bbox过滤字符
    if table_bboxes:
        def keep_char(obj):
            # 只过滤字符对象
            if obj.get("object_type") != "char":
                return True
            
            # 计算字符中心点
            cx = (obj["x0"] + obj["x1"]) / 2.0
            cy = (obj["top"] + obj["bottom"]) / 2.0
            
            # 检查是否在任何表格区域内
            for (x0, top, x1, bottom) in table_bboxes:
                if (x0 - padding) <= cx <= (x1 + padding) and (top - padding) <= cy <= (bottom + padding):
                    return False  # 排除表格内字符
            return True

        # 过滤页面并提取文本
        try:
            filtered_page = page.filter(keep_char)
            text = filtered_page.extract_text()
            if debug:
                chars_before = len(page.chars)
                chars_after = len(filtered_page.chars)
                print(f"    字符过滤: {chars_before} -> {chars_after} (移除 {chars_before - chars_after})")
        except Exception as e:
            if debug:
                print(f"    字符过滤失败，使用原始文本: {e}")
            text = page.extract_text()
    else:
        # 没有检测到表格，直接提取文本
        text = page.extract_text()
        if debug:
            print(f"    未检测到表格，直接提取文本")

    return text, tables, table_bboxes

def process_tables(page, tables_found, markdown_content, debug=False):
    """
    处理页面中的表格，转换为markdown格式
    """
    table_count = 0
    
    if tables_found:
        # 使用已检测到的表格对象
        for i, table in enumerate(tables_found):
            try:
                arr = table.extract()
                if arr and any(any(cell for cell in row if cell) for row in arr):
                    md_table = convert_table_to_markdown(arr)
                    if md_table:
                        markdown_content.append(md_table)
                        markdown_content.append("\n\n")
                        table_count += 1
                        if debug:
                            print(f"      表格 {i+1}: {len(arr)} 行")
            except Exception as e:
                if debug:
                    print(f"      表格 {i+1} 提取失败: {e}")
                continue
    
    # 如果上面没有成功提取到表格，尝试 extract_tables 作为备选
    if table_count == 0:
        try:
            tables = page.extract_tables()
            for i, table in enumerate(tables or []):
                if table and any(any(cell for cell in row if cell) for row in table):
                    md_table = convert_table_to_markdown(table)
                    if md_table:
                        markdown_content.append(md_table)
                        markdown_content.append("\n\n")
                        table_count += 1
                        if debug:
                            print(f"      备选表格 {i+1}: {len(table)} 行")
        except Exception as e:
            if debug:
                print(f"      备选表格提取失败: {e}")
    
    return table_count

def convert_table_to_markdown(table):
    """
    将表格数据转换为markdown表格格式
    """
    if not table or not any(table):
        return ""
    
    # 过滤空行和完全空的行
    filtered_table = []
    for row in table:
        if row and any(cell and str(cell).strip() for cell in row):
            filtered_table.append(row)
    
    if not filtered_table:
        return ""
    
    markdown_lines = []
    
    # 确定列数（取最大行的列数）
    max_cols = max(len(row) for row in filtered_table)
    
    # 处理表头
    header = filtered_table[0]
    header_cells = []
    for i in range(max_cols):
        cell = header[i] if i < len(header) else ""
        cell_text = str(cell).strip() if cell else ""
        # 清理markdown特殊字符
        cell_text = cell_text.replace("|", "&#124;").replace("\n", " ")
        header_cells.append(cell_text)
    
    markdown_lines.append("| " + " | ".join(header_cells) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    
    # 处理数据行
    for row in filtered_table[1:]:
        cells = []
        for i in range(max_cols):
            cell = row[i] if i < len(row) else ""
            cell_text = str(cell).strip() if cell else ""
            # 清理markdown特殊字符
            cell_text = cell_text.replace("|", "&#124;").replace("\n", " ")
            cells.append(cell_text)
        markdown_lines.append("| " + " | ".join(cells) + " |")
    
    return "\n".join(markdown_lines)

def validate_text_table_separation(page, text, tables):
    """
    验证文本和表格是否有重复内容
    返回重复内容列表
    """
    if not tables or not text:
        return []
    
    duplicates = []
    table_texts = set()
    
    # 收集表格中的文本
    for table in tables:
        try:
            arr = table.extract()
            if arr:
                for row in arr:
                    for cell in row:
                        if cell:
                            cell_text = str(cell).strip()
                            if len(cell_text) > 5:  # 只检查较长的文本
                                table_texts.add(cell_text)
        except Exception:
            continue
    
    # 检查表格文本是否出现在提取的文本中
    for table_text in table_texts:
        if table_text in text:
            duplicates.append(table_text)
    
    return duplicates

def extract_page_images(page, images_dir, start_counter, images_folder, debug=False):
    """
    提取页面图片并保存
    """
    saved_images = []
    counter = start_counter
    
    try:
        # 检查页面是否有图片对象
        if hasattr(page, 'images') and page.images:
            if debug:
                print(f"    检测到 {len(page.images)} 个图片对象")
            
            for i, img in enumerate(page.images):
                try:
                    # 获取图片区域
                    bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                    
                    # 检查图片大小是否合理
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    if width < 10 or height < 10:  # 跳过太小的图片
                        continue
                    
                    cropped = page.crop(bbox)
                    
                    # 转换为图像并保存
                    img_obj = cropped.to_image(resolution=150)
                    img_filename = f"image_{counter:03d}.png"
                    img_path = os.path.join(images_dir, img_filename)
                    img_obj.save(img_path)
                    
                    # 添加markdown引用
                    img_markdown = f"![image_{counter}]({images_folder}/{img_filename})\n\n"
                    saved_images.append(img_markdown)
                    counter += 1
                    
                    if debug:
                        print(f"      保存图片: {img_filename} ({width:.1f}x{height:.1f})")
                        
                except Exception as e:
                    if debug:
                        print(f"      图片 {i+1} 保存失败: {e}")
                    continue
        
        # 如果没有检测到图片，可以选择保存整页
        elif debug:
            print(f"    未检测到图片对象")
                
    except Exception as e:
        if debug:
            print(f"    图片提取失败: {e}")
    
    return saved_images

def batch_convert_pdfs(folder_path, output_folder=None, **kwargs):
    """
    批量转换PDF文件
    """
    if output_folder is None:
        output_folder = folder_path
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    success_count = 0
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(folder_path, pdf_file)
        output_path = os.path.join(output_folder, os.path.splitext(pdf_file)[0] + '.md')
        
        print(f"\n[{i}/{len(pdf_files)}] 转换: {pdf_file}")
        
        result = pdf_to_markdown(pdf_path, output_path, **kwargs)
        if result:
            success_count += 1
        
    print(f"\n批量转换完成: {success_count}/{len(pdf_files)} 个文件成功")

def test_pdfplumber_performance(pdf_path, debug=True):
    """
    测试pdfplumber的性能和功能
    """
    print("=== pdfplumber性能测试 ===")
    
    start_time = time.time()
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"PDF文件: {pdf_path}")
            print(f"总页数: {total_pages}")
            
            # 测试文本提取
            print("\n--- 文本提取测试 ---")
            text_start = time.time()
            total_text_length = 0
            pages_with_text = 0
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    total_text_length += len(text)
                    pages_with_text += 1
                if debug and i < 3:  # 只显示前3页的详情
                    print(f"页面 {i+1}: {len(text) if text else 0} 字符")
            
            text_time = time.time() - text_start
            print(f"文本提取耗时: {text_time:.2f}秒")
            print(f"有文本的页数: {pages_with_text}/{total_pages}")
            print(f"提取文本总长度: {total_text_length:,} 字符")
            
            # 测试表格提取
            print("\n--- 表格提取测试 ---")
            table_start = time.time()
            total_tables = 0
            pages_with_tables = 0
            
            for i, page in enumerate(pdf.pages):
                try:
                    tables = page.find_tables()
                    table_count = len(tables) if tables else 0
                    if table_count > 0:
                        pages_with_tables += 1
                        total_tables += table_count
                    if debug and i < 3 and table_count > 0:
                        print(f"页面 {i+1}: {table_count} 个表格")
                except Exception:
                    # 如果find_tables失败，尝试extract_tables
                    try:
                        tables = page.extract_tables()
                        table_count = len(tables) if tables else 0
                        if table_count > 0:
                            pages_with_tables += 1
                            total_tables += table_count
                    except Exception:
                        pass
            
            table_time = time.time() - table_start
            print(f"表格提取耗时: {table_time:.2f}秒")
            print(f"有表格的页数: {pages_with_tables}/{total_pages}")
            print(f"检测到表格总数: {total_tables}")
            
            # 测试图片检测
            print("\n--- 图片检测测试 ---")
            image_start = time.time()
            total_images = 0
            pages_with_images = 0
            
            for i, page in enumerate(pdf.pages):
                if hasattr(page, 'images'):
                    image_count = len(page.images)
                    if image_count > 0:
                        pages_with_images += 1
                        total_images += image_count
                    if debug and i < 3 and image_count > 0:
                        print(f"页面 {i+1}: {image_count} 个图片")
            
            image_time = time.time() - image_start
            print(f"图片检测耗时: {image_time:.2f}秒")
            print(f"有图片的页数: {pages_with_images}/{total_pages}")
            print(f"检测到图片总数: {total_images}")
    
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    total_time = time.time() - start_time
    print(f"\n=== 总结 ===")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"平均每页耗时: {total_time/total_pages:.3f}秒")

# 使用示例和主程序
if __name__ == "__main__":
    # 配置文件路径
    pdf_file = "/home/data/nongwa/workspace/data/10华夏收入混合型证券投资基金2024年年度报告.pdf"
    output_file = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/PDFPlumber/output/10华夏收入混合型证券投资基金2024年年度报告-1/10华夏收入混合型证券投资基金2024年年度报告.md"
    
    if os.path.exists(pdf_file):
        print("开始PDF转换...")
        
        # 完整转换（带调试信息）
        result = pdf_to_markdown(
            pdf_file, 
            output_file,
            extract_tables=True,
            extract_images=True,
            debug=True,  # 启用调试信息
            padding=8    # 增加表格边距
        )
        
        if result:
            print(f"\n转换成功！输出文件: {result}")
            
            # 可选：运行性能测试
            # print("\n" + "="*50)
            # test_pdfplumber_performance(pdf_file)
        else:
            print("转换失败！")
    
    else:
        print("文件不存在，显示使用示例:")
        print("\n=== 基本使用 ===")
        print("pdf_to_markdown('input.pdf')")
        print("pdf_to_markdown('input.pdf', 'output.md')")
        print("pdf_to_markdown('input.pdf', debug=True)")
        
        print("\n=== 批量转换 ===")
        print("batch_convert_pdfs('/path/to/pdf/folder')")
        print("batch_convert_pdfs('/input/folder', '/output/folder', debug=True)")
        
        print("\n=== 性能测试 ===")
        print("test_pdfplumber_performance('test.pdf')")