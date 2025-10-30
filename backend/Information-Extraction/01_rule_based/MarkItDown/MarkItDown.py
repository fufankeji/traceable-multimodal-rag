"""
MarkItDown纯净版 - 仅使用库的原生能力
不添加任何额外的后处理逻辑

注意：MarkItDown是一个高级文档转换工具
- 文本提取：MarkItDown原生能力 ✓
- 图片提取：MarkItDown原生能力 ✓（自动处理）
- 表格检测：MarkItDown原生能力 ✓（依赖底层库）
- 页面截图：需要辅助库
"""
from markitdown import MarkItDown
import os
from pathlib import Path
import re

# 用于页面截图和可视化的辅助库
try:
    import fitz  # PyMuPDF，用于页面截图和分析
    from PIL import Image, ImageDraw, ImageFont
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("警告：未安装PyMuPDF，无法生成整页截图和可视化")

def pdf_to_markdown_pure(pdf_path, output_dir="output_markitdown", images_folder="images", enable_visualization=False):
    """
    使用MarkItDown的原生能力转换PDF
    不做任何额外处理
    
    参数:
    - enable_visualization: 是否启用可视化调试（需要PyMuPDF辅助）
    """
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    images_dir = Path(output_dir) / images_folder
    images_dir.mkdir(exist_ok=True, parents=True)
    
    # 可视化输出目录
    if enable_visualization:
        viz_dir = Path(output_dir) / "visualization"
        viz_dir.mkdir(exist_ok=True, parents=True)
    
    pdf_name = Path(pdf_path).stem
    
    # === 1. 使用MarkItDown转换 - 原生能力 ===
    print("使用MarkItDown转换PDF...")
    md = MarkItDown()
    result = md.convert(pdf_path)
    
    # MarkItDown返回一个包含text_content的对象
    markdown_content = result.text_content if hasattr(result, 'text_content') else str(result)
    
    print(f"MarkItDown提取完成，内容长度: {len(markdown_content)} 字符")
    
    # === 2. 处理图片引用 ===
    # MarkItDown可能会生成图片引用，我们需要确保图片路径正确
    # 注意：MarkItDown对图片的处理取决于底层库
    
    # === 3. 添加每页完整截图 ===
    if HAS_PYMUPDF:
        print("\n添加页面截图...")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # 在markdown内容后添加每页截图
        page_screenshots = []
        
        for page_num in range(total_pages):
            print(f"  处理第 {page_num + 1}/{total_pages} 页")
            page = doc[page_num]
            
            # 保存整页截图
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_filename = f"page_{page_num + 1}_full.png"
            img_path = images_dir / img_filename
            pix.save(str(img_path))
            pix = None
            
            page_screenshots.append(f"\n![page_{page_num + 1}]({images_folder}/{img_filename})\n")
            
            # === 4. 可视化调试 ===
            if enable_visualization:
                try:
                    print(f"    生成可视化调试图...")
                    visualize_page(page, doc, page_num + 1, viz_dir)
                except Exception as e:
                    print(f"    可视化生成失败: {e}")
        
        doc.close()
        
        # 将截图添加到markdown内容中
        markdown_content += "\n\n" + "="*60 + "\n"
        markdown_content += "# 页面截图\n"
        markdown_content += "="*60 + "\n"
        markdown_content += "".join(page_screenshots)
    
    # === 5. 保存Markdown文件 ===
    md_path = Path(output_dir) / f"{pdf_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print(f"\n完成！输出: {md_path}")
    return str(md_path)

def visualize_page(page, doc, page_num, viz_dir):
    """
    可视化页面布局
    展示页面的基本结构信息
    """
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    
    # 转换为PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # 缩放因子
    scale = 2
    page_height = page.rect.height
    
    # 获取页面的文本块
    text_dict = page.get_text("dict")
    text_blocks = []
    image_blocks = []
    
    for block in text_dict.get("blocks", []):
        if "lines" in block:  # 文本块
            text_blocks.append(block)
        elif block.get("type") == 1:  # 图片块
            image_blocks.append(block)
    
    print(f"    检测到 {len(text_blocks)} 个文本块, {len(image_blocks)} 个图片块")
    
    # 绘制文本块（蓝色）
    for idx, block in enumerate(text_blocks):
        bbox = block["bbox"]
        x0, y0, x1, y1 = bbox[0] * scale, bbox[1] * scale, bbox[2] * scale, bbox[3] * scale
        draw.rectangle([x0, y0, x1, y1], outline=(0, 0, 255), width=2)
        draw.text((x0, y0 - 20), f"T{idx}", fill=(0, 0, 255), font=small_font)
    
    # 绘制图片块（红色）
    for idx, block in enumerate(image_blocks):
        bbox = block["bbox"]
        x0, y0, x1, y1 = bbox[0] * scale, bbox[1] * scale, bbox[2] * scale, bbox[3] * scale
        draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=3)
        draw.text((x0, y0 - 20), f"I{idx}", fill=(255, 0, 0), font=small_font)
    
    # 绘制图例
    legend_y = 10
    draw.rectangle([10, legend_y, 30, legend_y + 15], outline=(0, 0, 255), width=3)
    draw.text((35, legend_y), "蓝色: 文本块", fill=(0, 0, 0), font=small_font)
    legend_y += 25
    draw.rectangle([10, legend_y, 30, legend_y + 15], outline=(255, 0, 0), width=3)
    draw.text((35, legend_y), "红色: 图片块", fill=(0, 0, 0), font=small_font)
    
    # 保存可视化图片
    viz_filename = f"page_{page_num}_visualization.png"
    viz_path = viz_dir / viz_filename
    img.save(str(viz_path))
    print(f"    ✓ 可视化保存: {viz_filename}")
    
    # 保存详细信息
    detail_filename = f"page_{page_num}_structure.txt"
    detail_path = viz_dir / detail_filename
    with open(detail_path, 'w', encoding='utf-8') as f:
        f.write(f"MarkItDown - 第 {page_num} 页结构分析\n")
        f.write("=" * 80 + "\n\n")
        f.write("注意：MarkItDown使用底层库提取内容，这里显示的是PDF原始结构\n\n")
        
        f.write(f"文本块数量: {len(text_blocks)}\n")
        f.write(f"图片块数量: {len(image_blocks)}\n\n")
        
        f.write("文本块详情:\n")
        f.write("-" * 80 + "\n")
        for idx, block in enumerate(text_blocks):
            f.write(f"\n文本块 T{idx}:\n")
            f.write(f"位置: {block['bbox']}\n")
            # 提取文本内容
            text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text += span.get("text", "")
            f.write(f"内容预览: {text[:100]}...\n")
        
        if image_blocks:
            f.write("\n" + "=" * 80 + "\n")
            f.write("图片块详情:\n")
            f.write("-" * 80 + "\n")
            for idx, block in enumerate(image_blocks):
                f.write(f"\n图片块 I{idx}:\n")
                f.write(f"位置: {block['bbox']}\n")
                f.write(f"尺寸: {block.get('width', 'N/A')} x {block.get('height', 'N/A')}\n")
    
    print(f"    ✓ 结构详情保存: {detail_filename}")
    pix = None

def performance_test(pdf_path):
    """性能测试"""
    import time
    
    print("=== MarkItDown 性能测试 ===\n")
    
    # 统计页数
    if HAS_PYMUPDF:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
        print(f"总页数: {total_pages}")
    
    # MarkItDown转换测试
    start_time = time.time()
    md = MarkItDown()
    result = md.convert(pdf_path)
    conversion_time = time.time() - start_time
    
    markdown_content = result.text_content if hasattr(result, 'text_content') else str(result)
    total_length = len(markdown_content)
    
    print(f"MarkItDown转换: {conversion_time:.2f}秒")
    print(f"输出内容长度: {total_length}字符")
    
    # 简单分析内容
    lines = markdown_content.split('\n')
    print(f"总行数: {len(lines)}")
    
    # 检测表格（Markdown表格格式）
    table_count = len(re.findall(r'\|.*\|', markdown_content))
    if table_count > 0:
        print(f"检测到表格行: {table_count}行")
    
    # 检测图片引用
    image_count = len(re.findall(r'!\[.*?\]\(.*?\)', markdown_content))
    if image_count > 0:
        print(f"检测到图片引用: {image_count}个")
    
    if HAS_PYMUPDF:
        print(f"平均每页: {conversion_time/total_pages:.2f}秒")

def compare_with_original(pdf_path, output_dir="output_markitdown_compare"):
    """
    对比MarkItDown的输出与PDF原始结构
    帮助理解MarkItDown如何处理PDF
    """
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    print("\n=== 对比分析 ===\n")
    
    # 1. MarkItDown提取
    md = MarkItDown()
    result = md.convert(pdf_path)
    markdown_content = result.text_content if hasattr(result, 'text_content') else str(result)
    
    # 2. 使用PyMuPDF直接提取文本对比
    if HAS_PYMUPDF:
        doc = fitz.open(pdf_path)
        pymupdf_text = ""
        for page in doc:
            pymupdf_text += page.get_text()
        doc.close()
        
        # 保存对比结果
        compare_path = Path(output_dir) / "comparison.txt"
        with open(compare_path, 'w', encoding='utf-8') as f:
            f.write("MarkItDown vs PyMuPDF 提取对比\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("MarkItDown输出长度: {} 字符\n".format(len(markdown_content)))
            f.write("PyMuPDF输出长度: {} 字符\n\n".format(len(pymupdf_text)))
            
            f.write("差异:\n")
            if len(markdown_content) > len(pymupdf_text):
                f.write("MarkItDown输出更长（可能包含了Markdown格式）\n")
            elif len(markdown_content) < len(pymupdf_text):
                f.write("PyMuPDF输出更长（MarkItDown可能做了清理）\n")
            else:
                f.write("长度相同\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("MarkItDown输出预览:\n")
            f.write("-" * 80 + "\n")
            f.write(markdown_content[:1000] + "\n...\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("PyMuPDF输出预览:\n")
            f.write("-" * 80 + "\n")
            f.write(pymupdf_text[:1000] + "\n...\n")
        
        print(f"对比结果保存至: {compare_path}")

if __name__ == "__main__":
    pdf_path = "/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"
    output_dir = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/MarkItDown/output/阿里开发手册-泰山版"
    
    if os.path.exists(pdf_path):
        # 性能测试
        performance_test(pdf_path)
        
        print("\n" + "="*60)
        print("开始转换...")
        print("="*60 + "\n")
        
        # 完整转换（启用可视化调试）
        pdf_to_markdown_pure(
            pdf_path, 
            output_dir,
            enable_visualization=True  # 启用可视化
        )
        
        # 对比分析（可选）
        print("\n" + "="*60)
        print("生成对比分析...")
        print("="*60 + "\n")
        compare_with_original(pdf_path, output_dir + "/comparison")
        
    else:
        print(f"文件不存在: {pdf_path}")