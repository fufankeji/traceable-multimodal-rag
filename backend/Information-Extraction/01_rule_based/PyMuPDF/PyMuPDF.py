import fitz  # PyMuPDF
import os
import re
from pathlib import Path

def clean_text(text):
    """
    清理PyMuPDF提取的文本，解决多余空行和空格问题
    """
    if not text:
        return ""
    
    # 1. 先分行处理
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # 去除行首尾空白
        line = line.strip()
        # 跳过空行
        if line:
            # 压缩行内多个空格为单个空格
            line = re.sub(r' +', ' ', line)
            cleaned_lines.append(line)
    
    # 2. 智能合并段落（中文文本特殊处理）
    paragraphs = []
    current_para = []
    
    for i, line in enumerate(cleaned_lines):
        current_para.append(line)
        
        # 判断是否是段落结束
        # 段落结束的标志：
        # - 以中文标点结尾：。！？；
        # - 下一行是标题（较短且可能以数字、【开头）
        # - 下一行明显缩进或空行
        
        is_para_end = False
        
        if line and line[-1] in '。！？；':
            is_para_end = True
        elif i < len(cleaned_lines) - 1:
            next_line = cleaned_lines[i + 1]
            # 下一行是列表项或标题
            if next_line and (
                next_line[0].isdigit() or 
                next_line.startswith('【') or
                next_line.startswith('(') or
                len(next_line) < 20  # 可能是标题
            ):
                is_para_end = True
        
        if is_para_end or i == len(cleaned_lines) - 1:
            # 合并当前段落
            if current_para:
                # 对于中文，直接连接（不加空格）
                # 对于英文，保留空格
                para_text = smart_join(current_para)
                paragraphs.append(para_text)
                current_para = []
    
    # 3. 用双换行连接段落
    return '\n\n'.join(paragraphs)

def smart_join(lines):
    """
    智能连接文本行：中文之间不加空格，中英文之间适当加空格
    """
    if not lines:
        return ""
    
    result = lines[0]
    
    for i in range(1, len(lines)):
        prev_line = lines[i-1]
        curr_line = lines[i]
        
        if not prev_line or not curr_line:
            continue
        
        # 获取前一行的最后一个字符和当前行的第一个字符
        last_char = prev_line[-1]
        first_char = curr_line[0]
        
        # 判断是否需要添加空格
        need_space = False
        
        # 如果前一个是ASCII字母或数字，后一个也是，加空格
        if (last_char.isascii() and last_char.isalnum()) and \
           (first_char.isascii() and first_char.isalnum()):
            need_space = True
        # 如果是中文后跟英文，或英文后跟中文，不加空格
        elif is_chinese(last_char) or is_chinese(first_char):
            need_space = False
        
        if need_space:
            result += ' ' + curr_line
        else:
            result += curr_line
    
    return result

def is_chinese(char):
    """判断是否是中文字符"""
    return '\u4e00' <= char <= '\u9fff'

def pdf_to_markdown(pdf_path, output_dir="output", extract_tables=True, extract_images=True, images_folder="images"):
    """
    使用PyMuPDF将PDF转换为Markdown，改进文本清理
    """
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    images_dir = Path(output_dir) / images_folder
    images_dir.mkdir(exist_ok=True)
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    pdf_name = Path(pdf_path).stem
    
    markdown_content = []
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            print(f"处理第 {page_num + 1} 页...")
            
            # 处理单页
            page_content = process_single_page(
                page, page_num + 1, images_dir, images_folder, 
                extract_tables, extract_images
            )
            markdown_content.append(page_content)
        
        # 保存markdown文件
        md_path = Path(output_dir) / f"{pdf_name}.md"
        with open(md_path, "w", encoding="utf-8") as md_file:
            md_file.write("".join(markdown_content))
        
        doc.close()
        
        print(f"转换完成！")
        print(f"Markdown文件：{md_path}")
        print(f"图片目录：{images_dir}")
        
        return str(md_path)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        doc.close()
        return None

def process_single_page(page, page_num, images_dir, images_folder, extract_tables, extract_images):
    """
    独立处理单个页面
    """
    page_markdown = []
    
    # 1. 提取文本（使用清理后的文本）
    raw_text = page.get_text()
    cleaned_text = clean_text(raw_text)  # 关键改进！
    
    if cleaned_text.strip():
        page_markdown.append(cleaned_text)
        page_markdown.append("\n\n")
    
    # 2. 处理表格
    if extract_tables:
        try:
            tf = page.find_tables()
            if tf is not None:
                tables_found = []
                if isinstance(tf, (list, tuple)):
                    tables_found = list(tf)
                elif hasattr(tf, "tables") and tf.tables is not None:
                    try:
                        tables_found = list(tf.tables)
                    except:
                        tables_found = [tf.tables] if tf.tables else []
                
                for table_idx, table in enumerate(tables_found):
                    try:
                        table_data = table.extract() if hasattr(table, 'extract') else None
                        if table_data:
                            page_markdown.append(convert_table_to_markdown(table_data))
                            page_markdown.append("\n\n")
                    except Exception as e:
                        print(f"    表格 {table_idx + 1} 提取失败: {e}")
        except Exception as e:
            print(f"  - 表格检测出错: {e}")
    
    # 3. 处理图片
    if extract_images:
        page_images = extract_page_images(page, page_num, images_dir, images_folder)
        for img_md in page_images:
            page_markdown.append(img_md)
    
    return "".join(page_markdown)

def convert_table_to_markdown(table):
    """转换表格为markdown格式"""
    if not table or not any(table):
        return ""
    
    filtered_table = [row for row in table if row and any(cell for cell in row if cell)]
    if not filtered_table:
        return ""
    
    markdown_lines = []
    
    # 表头
    header = filtered_table[0]
    header_cells = [str(cell).strip() if cell is not None else "" for cell in header]
    markdown_lines.append("| " + " | ".join(header_cells) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")
    
    # 数据行
    for row in filtered_table[1:]:
        cells = [str(cell).strip() if cell is not None else "" for cell in row]
        while len(cells) < len(header_cells):
            cells.append("")
        markdown_lines.append("| " + " | ".join(cells[:len(header_cells)]) + " |")
    
    return "\n".join(markdown_lines)

def extract_page_images(page, page_num, images_dir, images_folder):
    """提取页面图片"""
    saved_images = []
    
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
                            img_filename = f"page_{page_num}_img_{img_count + 1}.png"
                            img_path = images_dir / img_filename
                            pix.save(str(img_path))
                            
                            saved_images.append(f"![图片]({images_folder}/{img_filename})\n\n")
                            img_count += 1
                        
                        pix = None
                except Exception as e:
                    continue
        
        # 保存完整页面截图
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_filename = f"page_{page_num}_full.png"
            img_path = images_dir / img_filename
            pix.save(str(img_path))
            pix = None
            
            saved_images.append(f"![第 {page_num} 页完整截图]({images_folder}/{img_filename})\n\n")
        except:
            pass
        
    except Exception as e:
        print(f"  - 图片提取失败: {e}")
    
    return saved_images

def test_text_cleaning():
    """测试文本清理效果"""
    pdf_path = "/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"
    
    doc = fitz.open(pdf_path)
    page = doc[1]  # 第2页
    
    print("=" * 60)
    print("原始文本（前500字符）:")
    print("=" * 60)
    raw_text = page.get_text()
    print(repr(raw_text[:500]))
    
    print("\n" + "=" * 60)
    print("清理后文本（前500字符）:")
    print("=" * 60)
    cleaned = clean_text(raw_text)
    print(repr(cleaned[:500]))
    
    print("\n" + "=" * 60)
    print("效果对比:")
    print("=" * 60)
    print(f"原始长度: {len(raw_text)} 字符")
    print(f"清理后长度: {len(cleaned)} 字符")
    print(f"原始行数: {raw_text.count(chr(10))} 行")
    print(f"清理后段落数: {cleaned.count(chr(10)*2) + 1} 段")
    
    doc.close()

def main():
    """使用示例"""
    pdf_path = "/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"
    output_dir = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/PyMuPDF/output/阿里开发手册-泰山版-fixed"
    
    if os.path.exists(pdf_path):
        # 先测试清理效果
        print("测试文本清理效果...\n")
        test_text_cleaning()
        
        print("\n" + "=" * 60)
        print("开始完整转换...")
        print("=" * 60 + "\n")
        
        # 完整转换
        pdf_to_markdown(pdf_path, output_dir)
    else:
        print(f"PDF文件不存在：{pdf_path}")

if __name__ == "__main__":
    main()