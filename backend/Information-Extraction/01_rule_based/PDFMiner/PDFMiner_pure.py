"""
PDFMiner纯净版 - 仅使用库的原生能力
不添加任何额外的后处理逻辑

注意：PDFMiner主要用于文本提取，图片和页面渲染能力有限
- 文本提取：PDFMiner原生能力 ✓
- 图片提取：PDFMiner原生能力 ✓（但需要手动处理）
- 表格检测：PDFMiner无原生支持 ✗
- 页面截图：需要辅助库（pdf2image或fitz）
"""
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTFigure, LTImage
from pdfminer.pdfpage import PDFPage
from PIL import Image, ImageDraw, ImageFont
import io
import os
from pathlib import Path

# 用于页面截图和可视化的辅助库
try:
    import fitz  # PyMuPDF，用于页面截图和可视化
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("警告：未安装PyMuPDF，无法生成整页截图和可视化")

def pdf_to_markdown_pure(pdf_path, output_dir="output_pdfminer", images_folder="images", enable_visualization=False, filter_nested_boxes=False):
    """
    使用PDFMiner的原生能力转换PDF
    不做任何额外处理
    
    参数:
    - enable_visualization: 是否启用可视化调试（需要PyMuPDF辅助）
    - filter_nested_boxes: 是否过滤嵌套文本框（False=测试原始性能，True=处理嵌套问题）
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
    
    # 统计总页数
    with open(pdf_path, 'rb') as fp:
        total_pages = len(list(PDFPage.get_pages(fp)))
    
    # 打开PyMuPDF文档（用于截图和可视化）
    doc = None
    if HAS_PYMUPDF:
        doc = fitz.open(pdf_path)
    
    # 逐页处理
    page_num = 0
    for page_layout in extract_pages(pdf_path, laparams=LAParams()):
        page_num += 1
        print(f"处理第 {page_num}/{total_pages} 页")
        
        # === 1. 提取文本 - 使用PDFMiner默认方法 ===
        if not filter_nested_boxes:
            # 方式1：使用 extract_text API（PDFMiner原始能力，不处理嵌套）
            with open(pdf_path, 'rb') as fp:
                text = extract_text(fp, page_numbers=[page_num - 1])
                if text:
                    markdown_content.append(text)
        else:
            # 方式2：手动提取并过滤嵌套框
            text = extract_text_filter_nested(page_layout)
            if text:
                markdown_content.append(text)
        
        # === 2. 提取图片 - 使用PDFMiner原生能力 ===
        image_count = 0
        
        def extract_images_from_layout(layout_obj):
            """递归提取图片"""
            nonlocal image_count
            
            if isinstance(layout_obj, LTFigure):
                # 图片容器
                try:
                    for item in layout_obj:
                        if isinstance(item, LTImage):
                            image_count += 1
                            img_filename = f"page_{page_num}_img_{image_count}.png"
                            success = extract_image(item, images_dir / img_filename)
                            if success:
                                markdown_content.append(f"![image]({images_folder}/{img_filename})\n")
                except Exception as e:
                    print(f"  图片提取失败: {e}")
            
            # 递归处理子元素
            if hasattr(layout_obj, '__iter__'):
                for child in layout_obj:
                    extract_images_from_layout(child)
        
        extract_images_from_layout(page_layout)
        
        # === 3. 提取表格 ===
        # PDFMiner没有原生的表格检测能力
        
        # === 4. 保存整页截图 ===
        if HAS_PYMUPDF and doc:
            try:
                page = doc[page_num - 1]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_filename = f"page_{page_num}_full.png"
                img_path = images_dir / img_filename
                pix.save(str(img_path))
                pix = None
                
                markdown_content.append(f"![page_{page_num}]({images_folder}/{img_filename})\n")
            except Exception as e:
                print(f"  整页截图失败: {e}")
        
        # === 5. 可视化调试（借助PyMuPDF，展示PDFMiner检测到的内容）===
        if enable_visualization and HAS_PYMUPDF and doc:
            try:
                print(f"  生成可视化调试图...")
                visualize_page_layout(page_layout, doc, page_num, viz_dir, filter_nested_boxes)
            except Exception as e:
                print(f"  可视化生成失败: {e}")
                import traceback
                traceback.print_exc()
    
    # 关闭文档
    if doc:
        doc.close()
    
    # 保存Markdown文件
    md_path = Path(output_dir) / f"{pdf_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("".join(markdown_content))
    
    print(f"完成！输出: {md_path}")
    return str(md_path)

def extract_text_filter_nested(page_layout):
    """
    手动提取文本，过滤掉嵌套的文本框
    只保留最外层的文本框，避免重复
    """
    # 收集所有文本框
    all_textboxes = []
    
    def collect_textboxes(layout_obj):
        if hasattr(layout_obj, '__class__') and 'LTTextBox' in layout_obj.__class__.__name__:
            all_textboxes.append(layout_obj)
        
        if hasattr(layout_obj, '__iter__'):
            for child in layout_obj:
                collect_textboxes(child)
    
    collect_textboxes(page_layout)
    
    # 过滤嵌套框：如果一个框被包含在另一个框内，则过滤掉
    def is_contained(box1, box2):
        """检查box1是否被包含在box2内"""
        return (box2.x0 <= box1.x0 and box2.y0 <= box1.y0 and 
                box2.x1 >= box1.x1 and box2.y1 >= box1.y1)
    
    filtered_boxes = []
    for i, box in enumerate(all_textboxes):
        is_nested = False
        for j, other_box in enumerate(all_textboxes):
            if i != j and is_contained(box, other_box):
                is_nested = True
                break
        if not is_nested:
            filtered_boxes.append(box)
    
    # 按照阅读顺序排序（从上到下，从左到右）
    filtered_boxes.sort(key=lambda box: (-box.y1, box.x0))
    
    # 提取文本
    text_parts = []
    for box in filtered_boxes:
        text = box.get_text()
        if text.strip():
            text_parts.append(text)
    
    return ''.join(text_parts)

def visualize_page_layout(page_layout, doc, page_num, viz_dir, filter_nested_boxes=False):
    """
    可视化PDFMiner检测到的页面布局
    展示所有文本对象，帮助诊断问题
    """
    page = doc[page_num - 1]
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
    page_height = page_layout.height
    
    # 收集所有检测到的对象
    all_objects = []
    
    def collect_objects(layout_obj, depth=0):
        """收集所有布局对象"""
        obj_info = {
            'type': type(layout_obj).__name__,
            'bbox': getattr(layout_obj, 'bbox', None),
            'depth': depth
        }
        
        if isinstance(layout_obj, LTTextContainer):
            obj_info['text'] = layout_obj.get_text()
            obj_info['text_preview'] = obj_info['text'][:50].replace('\n', ' ')
        
        if obj_info['bbox']:
            all_objects.append(obj_info)
        
        # 递归处理子元素
        if hasattr(layout_obj, '__iter__'):
            for child in layout_obj:
                collect_objects(child, depth + 1)
    
    collect_objects(page_layout)
    
    # 定义颜色
    colors = {
        'LTTextBox': (255, 0, 0),       # 红色
        'LTTextLine': (0, 255, 0),       # 绿色
        'LTChar': (0, 0, 255),           # 蓝色
        'LTFigure': (255, 165, 0),       # 橙色
    }
    
    # 只收集顶层文本容器（LTTextBox），避免父子容器重复
    # LTTextBox是容器，包含LTTextLine，我们只需要最外层的容器
    text_containers = [obj for obj in all_objects if 'LTTextBox' in obj['type']]
    
    # 识别嵌套框
    nested_info = []
    if filter_nested_boxes:
        for i, obj1 in enumerate(text_containers):
            bbox1 = obj1['bbox']
            for j, obj2 in enumerate(text_containers):
                if i != j:
                    bbox2 = obj2['bbox']
                    # 检查obj1是否被包含在obj2中
                    if (bbox2[0] <= bbox1[0] and bbox2[1] <= bbox1[1] and 
                        bbox2[2] >= bbox1[2] and bbox2[3] >= bbox1[3]):
                        nested_info.append((i, j))  # i被包含在j中
    
    print(f"  检测到 {len(text_containers)} 个文本容器")
    if nested_info:
        print(f"  检测到 {len(nested_info)} 个嵌套关系")
        if filter_nested_boxes:
            print(f"  已启用嵌套过滤，嵌套框将被标记")
    
    # 检测重复文本
    text_map = {}
    for idx, obj in enumerate(text_containers):
        if 'text' in obj:
            text_key = obj['text'].strip()
            if text_key:
                if text_key not in text_map:
                    text_map[text_key] = []
                text_map[text_key].append(idx)
    
    duplicates = {k: v for k, v in text_map.items() if len(v) > 1}
    if duplicates:
        print(f"  警告：PDFMiner检测到 {len(duplicates)} 组重复文本对象")
    
    # 绘制对象
    nested_set = set([i for i, j in nested_info])  # 被嵌套的框
    parent_set = set([j for i, j in nested_info])   # 父框
    
    for idx, obj in enumerate(text_containers):
        bbox = obj['bbox']
        obj_type = obj['type']
        
        # 转换坐标
        x0 = bbox[0] * scale
        y0 = (page_height - bbox[3]) * scale
        x1 = bbox[2] * scale
        y1 = (page_height - bbox[1]) * scale
        
        # 选择颜色和标签
        color = colors.get(obj_type, (128, 128, 128))
        label = f"#{idx}"
        width = 2
        
        # 检查是否重复
        is_duplicate = False
        if 'text' in obj and obj['text'].strip() in duplicates:
            is_duplicate = True
            color = (255, 140, 0)  # 深橙色标记重复
            label += "*重复"
            width = 4
        
        # 标记嵌套关系
        if filter_nested_boxes:
            if idx in nested_set:
                color = (147, 112, 219)  # 紫色标记被嵌套的框
                label += "[嵌套]"
                width = 3
            elif idx in parent_set:
                color = (0, 128, 128)  # 青色标记父框
                label += "[父框]"
                width = 3
        
        # 绘制边界框
        draw.rectangle([x0, y0, x1, y1], outline=color, width=width)
        
        # 绘制对象编号和标签
        draw.text((x0, y0 - 20), label, fill=color, font=small_font)
    
    # 绘制图例
    legend_y = 10
    legend_items = [
        ("红色: TextBox", (255, 0, 0)),
        ("橙色: 重复文本*", (255, 140, 0)),
    ]
    if filter_nested_boxes:
        legend_items.extend([
            ("紫色: 嵌套框", (147, 112, 219)),
            ("青色: 父框", (0, 128, 128)),
        ])
    
    for legend_text, legend_color in legend_items:
        draw.rectangle([10, legend_y, 30, legend_y + 15], outline=legend_color, width=3)
        draw.text((35, legend_y), legend_text, fill=(0, 0, 0), font=small_font)
        legend_y += 25
    
    # 保存可视化图片
    viz_filename = f"page_{page_num}_visualization.png"
    viz_path = viz_dir / viz_filename
    img.save(str(viz_path))
    print(f"  ✓ 可视化保存: {viz_filename}")
    
    # 保存对象详情
    detail_filename = f"page_{page_num}_objects.txt"
    detail_path = viz_dir / detail_filename
    with open(detail_path, 'w', encoding='utf-8') as f:
        f.write(f"PDFMiner 第 {page_num} 页检测结果\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"共检测到 {len(text_containers)} 个文本容器\n")
        if filter_nested_boxes:
            f.write(f"启用嵌套过滤模式\n")
        f.write("\n")
        
        for idx, obj in enumerate(text_containers):
            f.write(f"对象 #{idx} - {obj['type']}\n")
            f.write(f"位置: {obj['bbox']}\n")
            if 'text_preview' in obj:
                f.write(f"文本预览: {obj['text_preview']}\n")
            
            # 标记嵌套关系
            if filter_nested_boxes:
                if idx in nested_set:
                    parent_idx = [j for i, j in nested_info if i == idx]
                    f.write(f"[嵌套] 此框被包含在对象 {parent_idx} 中\n")
                if idx in parent_set:
                    children_idx = [i for i, j in nested_info if j == idx]
                    f.write(f"[父框] 此框包含对象 {children_idx}\n")
            
            f.write("-" * 80 + "\n\n")
        
        if nested_info and filter_nested_boxes:
            f.write("\n" + "=" * 80 + "\n")
            f.write("嵌套关系分析\n")
            f.write("=" * 80 + "\n\n")
            f.write("嵌套框可能导致文本重复提取。建议使用 filter_nested_boxes=True 过滤。\n\n")
            for child_idx, parent_idx in nested_info:
                f.write(f"对象 #{child_idx} 被嵌套在对象 #{parent_idx} 中\n")
                f.write(f"  子框位置: {text_containers[child_idx]['bbox']}\n")
                f.write(f"  父框位置: {text_containers[parent_idx]['bbox']}\n")
                f.write("\n")
        
        if duplicates:
            f.write("\n" + "=" * 80 + "\n")
            f.write("重复文本检测结果\n")
            f.write("=" * 80 + "\n\n")
            f.write("注意：如果出现重复，说明PDFMiner在同一页检测到了多个相同内容的文本对象。\n")
            f.write("这可能是PDF文档本身的问题（如多层文本），也可能是PDFMiner的检测特性。\n\n")
            
            for text, indices in list(duplicates.items())[:5]:  # 只显示前5组
                f.write(f"重复内容: {text[:100]}...\n")
                f.write(f"出现次数: {len(indices)}\n")
                f.write(f"对象编号: {indices}\n")
                for idx in indices:
                    f.write(f"  #{idx}: {text_containers[idx]['bbox']}\n")
                f.write("\n")
    
    print(f"  ✓ 对象详情保存: {detail_filename}")
    pix = None

def extract_image(lt_image, output_path):
    """
    从LTImage对象提取图片
    PDFMiner原生能力
    """
    try:
        if hasattr(lt_image, 'stream'):
            stream = lt_image.stream
            rawdata = stream.get_rawdata()
            
            # JPEG格式直接保存
            if stream.get('Filter') == '/DCTDecode':
                with open(output_path, 'wb') as f:
                    f.write(rawdata)
                return True
            
            # 其他格式用PIL处理
            try:
                image = Image.open(io.BytesIO(rawdata))
                image.save(output_path)
                return True
            except:
                try:
                    data = stream.get_data()
                    width = stream.get('Width', 0)
                    height = stream.get('Height', 0)
                    
                    if width > 0 and height > 0:
                        image = Image.frombytes('RGB', (width, height), data)
                        image.save(output_path)
                        return True
                except Exception as e:
                    print(f"    图片解码失败: {e}")
                    return False
        return False
    except Exception as e:
        print(f"    图片提取异常: {e}")
        return False

def performance_test(pdf_path):
    """性能测试"""
    import time
    
    print("=== PDFMiner 性能测试 ===\n")
    
    start_time = time.time()
    
    # 统计页数
    with open(pdf_path, 'rb') as fp:
        total_pages = len(list(PDFPage.get_pages(fp)))
    print(f"总页数: {total_pages}")
    
    # 文本提取
    text_start = time.time()
    with open(pdf_path, 'rb') as fp:
        text = extract_text(fp)
        total_text_length = len(text) if text else 0
    text_time = time.time() - text_start
    print(f"文本提取: {text_time:.2f}秒, {total_text_length}字符")
    
    # 表格提取
    print(f"表格提取: 不支持（PDFMiner无原生表格检测能力）")
    
    # 图片检测
    image_start = time.time()
    total_images = 0
    for page_layout in extract_pages(pdf_path):
        def count_images(layout_obj):
            nonlocal total_images
            if isinstance(layout_obj, (LTFigure, LTImage)):
                total_images += 1
            if hasattr(layout_obj, '__iter__'):
                for child in layout_obj:
                    count_images(child)
        count_images(page_layout)
    image_time = time.time() - image_start
    print(f"图片检测: {image_time:.2f}秒, {total_images}个图片")
    
    total_time = time.time() - start_time
    print(f"\n总耗时: {total_time:.2f}秒")
    print(f"平均每页: {total_time/total_pages:.2f}秒")

if __name__ == "__main__":
    pdf_path = "/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf"
    output_dir = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/PDFMiner/output/阿里开发手册-泰山版"
    
    if os.path.exists(pdf_path):
        # 性能测试
        performance_test(pdf_path)
        
        print("\n" + "="*60)
        print("测试1: PDFMiner原始能力（不处理嵌套）")
        print("="*60 + "\n")
        
        # 测试1：原始能力
        # pdf_to_markdown_pure(
        #     pdf_path, 
        #     output_dir + "_original",
        #     enable_visualization=True,
        #     filter_nested_boxes=False  # 不过滤嵌套，测试原始性能
        # )
        
        # print("\n" + "="*60)
        # print("测试2: 启用嵌套过滤")
        # print("="*60 + "\n")
        
        # 测试2：启用嵌套过滤
        # pdf_to_markdown_pure(
        #     pdf_path, 
        #     output_dir + "_filtered",
        #     enable_visualization=True,
        #     filter_nested_boxes=True  # 启用过滤，对比效果
        # )
        
        print("\n" + "="*60)
        print("完成！请对比两个输出目录的结果：")
        print(f"  原始版本: {output_dir}_original")
        print(f"  过滤版本: {output_dir}_filtered")
        print("="*60)
    else:
        print(f"文件不存在: {pdf_path}")