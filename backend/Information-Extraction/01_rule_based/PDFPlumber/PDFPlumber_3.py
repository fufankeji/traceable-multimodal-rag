# -*- coding: utf-8 -*-
"""
pdfplumber -> Markdown (minimal processing)
- 正常抽取 text 与表格；
- 可选：基于“去符号后”的文本匹配，把正文中的表格文本原位替换成 Markdown 表格，减少“同页重复”。

依赖：
    pip install pdfplumber
"""

import os
import unicodedata
import pdfplumber


# =========================
# 基础：表格 -> Markdown
# =========================
def convert_table_to_markdown(table):
    """
    将pdfplumber提取的表格(二维数组)转换为markdown表格
    """
    if not table or not any(table):
        return ""

    # 过滤空行
    filtered_table = [row for row in table if row and any(cell for cell in row if cell)]
    if not filtered_table:
        return ""

    markdown_lines = []

    # 第一行作为表头
    header = filtered_table[0]
    header_cells = [str(cell) if cell else "" for cell in header]
    markdown_lines.append("| " + " | ".join(header_cells) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")

    # 数据行
    for row in filtered_table[1:]:
        cells = [str(cell) if cell else "" for cell in row]
        # 保持列数一致
        while len(cells) < len(header_cells):
            cells.append("")
        markdown_lines.append("| " + " | ".join(cells[:len(header_cells)]) + " |")

    return "\n".join(markdown_lines)


# ======================================
# 可选：排除表格区域后的文本（备用）
# ======================================
def extract_text_excluding_tables(page, table_settings=None, padding=6):
    """
    从页面提取正文文本，但排除“检测到的表格区域”里的字符。
    - table_settings: 传给 find_tables 的参数
    - padding: 给表格 bbox 四周加边距，避免边界字符溢出
    """
    tables = []
    table_bboxes = []
    if hasattr(page, "find_tables"):
        # 先 lines 策略
        try:
            tables = page.find_tables(table_settings=table_settings)
            table_bboxes = [t.bbox for t in tables if getattr(t, "bbox", None)]
        except Exception:
            pass
        # 再 text 策略兜底
        if not table_bboxes:
            try:
                alt = dict(table_settings or {})
                alt["vertical_strategy"] = "text"
                alt["horizontal_strategy"] = "text"
                tables2 = page.find_tables(table_settings=alt)
                bboxes2 = [t.bbox for t in tables2 if getattr(t, "bbox", None)]
                if bboxes2:
                    tables = tables2
                    table_bboxes = bboxes2
            except Exception:
                pass

    # 用“矩形相交”判定字符是否位于表格内
    def intersects(char, bbox, pad):
        x0, top, x1, bottom = bbox
        return not (char["x1"] < x0 - pad or
                    char["x0"] > x1 + pad or
                    char["bottom"] < top - pad or
                    char["top"] > bottom + pad)

    if table_bboxes:
        def keep(obj):
            if obj.get("object_type") != "char":
                return True
            for bb in table_bboxes:
                if intersects(obj, bb, padding):
                    return False
            return True
        filtered_page = page.filter(keep)
        text = filtered_page.extract_text()
    else:
        text = page.extract_text()

    return text, tables, table_bboxes


# ======================================
# 文本去符号匹配 & 原位替换（核心）
# ======================================
def _normalize_for_match(s):
    """
    规范化：仅保留 Unicode 'L*'（字母类）和 'N*'（数字类）字符；小写化。
    返回：(规范化后的字符串, 规范化字符到原串索引的映射列表)
    """
    if not s:
        return "", []
    kept, idx_map = [], []
    for i, ch in enumerate(s):
        cat = unicodedata.category(ch)
        if cat and cat[0] in ('L', 'N'):
            kept.append(ch.lower())
            idx_map.append(i)
    return ''.join(kept), idx_map


def _table_to_plain_string(table):
    """
    将二维表（list[list]）拼成纯文本，仅用于匹配比较，不用于输出
    """
    rows = []
    for row in table or []:
        if row:
            rows.append(' '.join('' if (c is None) else str(c) for c in row))
    return '\n'.join(rows)


def _replace_tables_in_text_by_match(original_text, tables, md_tables, min_norm_len=20):
    """
    在 original_text 中，用对应 md_tables 替换与 tables 文本等价（去符号后）的区域。
    - tables: [二维数组]
    - md_tables: [与 tables 一一对应的 Markdown 字符串]
    返回：(替换后的文本, 命中的表格索引集合)
    """
    norm_text, idx_map = _normalize_for_match(original_text or "")
    if not norm_text:
        return original_text, set()

    replacements = []  # (start, end, md, i)
    matched_idx = set()

    for i, tbl in enumerate(tables):
        plain = _table_to_plain_string(tbl)
        norm_plain, _ = _normalize_for_match(plain)
        if not norm_plain or len(norm_plain) < min_norm_len:
            continue
        pos = norm_text.find(norm_plain)
        if pos == -1:
            continue
        start = idx_map[pos]
        end = idx_map[pos + len(norm_plain) - 1] + 1  # 原串切片右开区间
        replacements.append((start, end, (md_tables[i] + "\n\n"), i))

    if not replacements:
        return original_text, matched_idx

    # 去重叠：按起点排序后过滤重叠区间
    replacements.sort(key=lambda x: (x[0], x[1]))
    pruned = []
    last_end = -1
    for s, e, md, i in replacements:
        if s >= last_end:
            pruned.append((s, e, md, i))
            last_end = e

    # 逆序应用替换，避免偏移
    text = original_text
    for s, e, md, i in sorted(pruned, key=lambda x: x[0], reverse=True):
        text = text[:s] + md + text[e:]
        matched_idx.add(i)

    return text, matched_idx


# =========================
# 图片提取（保持原生能力）
# =========================
def extract_page_images(page, images_dir, start_counter, images_folder):
    """
    使用pdfplumber提取页面图片；若无图片对象，退而保存整页截图
    """
    saved_images = []
    counter = start_counter

    try:
        # 方法1: 提取页面中的图片对象
        if hasattr(page, 'images'):
            for img in page.images:
                try:
                    bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                    cropped = page.crop(bbox)
                    img_obj = cropped.to_image(resolution=150)
                    img_filename = f"image_{counter:03d}.png"
                    img_path = os.path.join(images_dir, img_filename)
                    img_obj.save(img_path)

                    img_markdown = f"![image_{counter}]({images_folder}/{img_filename})\n\n"
                    saved_images.append(img_markdown)
                    counter += 1
                except Exception:
                    continue

        # 方法2: 如果没有检测到图片对象，保存整页
        if not saved_images:
            try:
                page_img = page.to_image(resolution=150)
                img_filename = f"page_{page.page_number}.png"
                img_path = os.path.join(images_dir, img_filename)
                page_img.save(img_path)

                img_markdown = f"![page_{page.page_number}]({images_folder}/{img_filename})\n\n"
                saved_images.append(img_markdown)
            except Exception:
                pass

    except Exception:
        pass

    return saved_images


# =========================
# 主流程
# =========================
def pdf_to_markdown(
    pdf_path,
    output_path=None,
    extract_tables=True,
    extract_images=True,
    images_folder="images",
    # —— 新增两个开关 —— #
    dedupe_by_text_match=False,         # 基于去符号匹配做“原位替换去重”
    use_extract_tables_fallback=False   # 当 find_tables 没结果时，是否回退到 page.extract_tables()
):
    """
    使用 pdfplumber 将PDF转换为Markdown（最少修饰）

    参数:
    - pdf_path: PDF文件路径
    - output_path: 输出MD文件路径
    - extract_tables: 是否提取表格
    - extract_images: 是否提取图片
    - images_folder: 图片文件夹名称
    - dedupe_by_text_match: 是否开启“去符号匹配 + 原位替换”的去重策略
    - use_extract_tables_fallback: find_tables 无表格时是否回退 extract_tables（默认否，避免重复）
    """
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '.md'

    # 创建图片文件夹（使用绝对路径更稳；Markdown 里仍保持相对路径）
    if extract_images:
        output_dir = os.path.dirname(os.path.abspath(output_path)) if output_path else os.getcwd()
        images_dir = os.path.join(output_dir, images_folder)
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

    markdown_content = []
    image_counter = 1

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                table_settings = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_x_tolerance": 5,
                    "intersection_y_tolerance": 5,
                }

                # —— 表格：优先 find_tables -> t.extract()
                tables_found = []
                if extract_tables and hasattr(page, "find_tables"):
                    try:
                        tables_found = page.find_tables(table_settings=table_settings) or []
                    except Exception:
                        tables_found = []

                    # 兜底再试 text 策略（可选）
                    if not tables_found:
                        try:
                            alt = dict(table_settings)
                            alt["vertical_strategy"] = "text"
                            alt["horizontal_strategy"] = "text"
                            tables_found = page.find_tables(table_settings=alt) or []
                        except Exception:
                            tables_found = []

                arr_list, md_list = [], []
                if extract_tables and tables_found:
                    for t in tables_found:
                        try:
                            arr = t.extract()
                            if arr:
                                arr_list.append(arr)
                                md_list.append(convert_table_to_markdown(arr))
                        except Exception:
                            continue
                elif extract_tables and use_extract_tables_fallback:
                    # 可选回退：需要“尽可能不漏表”时开启；默认关闭以减少重复风险
                    try:
                        for tb in (page.extract_tables() or []):
                            if tb:
                                arr_list.append(tb)
                                md_list.append(convert_table_to_markdown(tb))
                    except Exception:
                        pass

                # —— 文本：按需选择 “带表格的原文” 或 “排除表格区域的正文”
                if dedupe_by_text_match:
                    # 为了做匹配替换，使用 page.extract_text() 的“原始文本”（可能包含表格里的文字）
                    text = page.extract_text()
                else:
                    # 若不做匹配去重，则可使用“排除表格区域”的正文（减少表格文字混入）
                    text, _, _ = extract_text_excluding_tables(page, table_settings=table_settings, padding=6)

                # —— 去重策略：用表格MD替换正文中对应区域；未命中的表格再单独追加
                if dedupe_by_text_match and extract_tables and arr_list:
                    replaced_text, hit_idx = _replace_tables_in_text_by_match(
                        text or "", arr_list, md_list, min_norm_len=20
                    )
                    if replaced_text:
                        markdown_content.append(replaced_text)
                        markdown_content.append("\n\n")
                    # 追加未命中的表格
                    for j, md in enumerate(md_list):
                        if j not in hit_idx:
                            markdown_content.append(md)
                            markdown_content.append("\n\n")
                else:
                    # 原始顺序：先文本，后表格
                    if text:
                        markdown_content.append(text)
                        markdown_content.append("\n\n")
                    for md in md_list:
                        markdown_content.append(md)
                        markdown_content.append("\n\n")

                # —— 图片
                if extract_images:
                    saved_images = extract_page_images(page, images_dir, image_counter, images_folder)
                    for img_md in saved_images:
                        markdown_content.append(img_md)
                        image_counter += 1

        # 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(markdown_content))

        print(f"转换完成: {output_path}")
        if extract_images and image_counter > 1:
            print(f"提取图片数量: {image_counter - 1}")
        return output_path

    except Exception as e:
        print(f"错误: {str(e)}")
        return None


# =========================
# 批量 & 性能测试（可选）
# =========================
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

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        output_path = os.path.join(output_folder, os.path.splitext(pdf_file)[0] + '.md')

        print(f"转换: {pdf_file}")
        pdf_to_markdown(pdf_path, output_path, **kwargs)


def test_pdfplumber_performance(pdf_path):
    """
    简易性能测试（文本/表格/图片检测耗时）
    """
    import time

    print("=== pdfplumber性能测试 ===")

    start_time = time.time()

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"总页数: {total_pages}")

        # 文本
        text_start = time.time()
        total_text_length = 0
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                total_text_length += len(text)
        text_time = time.time() - text_start
        print(f"文本提取耗时: {text_time:.2f}秒")
        print(f"提取文本总长度: {total_text_length} 字符")

        # 表格
        table_start = time.time()
        total_tables = 0
        for page in pdf.pages:
            try:
                ts = page.extract_tables() or []
                total_tables += len(ts)
            except Exception:
                pass
        table_time = time.time() - table_start
        print(f"表格提取耗时: {table_time:.2f}秒")
        print(f"检测到表格数量: {total_tables}")

        # 图片
        image_start = time.time()
        total_images = 0
        for page in pdf.pages:
            if hasattr(page, 'images'):
                total_images += len(page.images)
        image_time = time.time() - image_start
        print(f"图片检测耗时: {image_time:.2f}秒")
        print(f"检测到图片数量: {total_images}")

    total_time = time.time() - start_time
    print(f"总耗时: {total_time:.2f}秒")
    if total_pages:
        print(f"平均每页耗时: {total_time/total_pages:.2f}秒")


# =========================
# 示例
# =========================
if __name__ == "__main__":
    # 替换为实际文件与输出路径
    pdf_file = "/home/data/nongwa/workspace/data/10华夏收入混合型证券投资基金2024年年度报告.pdf"
    output_file = "/home/data/nongwa/workspace/Information-Extraction/01_rule_based/PDFPlumber/output/10华夏收入混合型证券投资基金2024年年度报告/10华夏收入混合型证券投资基金2024年年度报告.md"

    if os.path.exists(pdf_file):
        # 开启“去符号匹配 + 原位替换”的去重策略；默认不回退 extract_tables
        pdf_to_markdown(
            pdf_file,
            output_file,
            extract_tables=True,
            extract_images=True,
            images_folder="images",
            dedupe_by_text_match=True,       # ← 打开去重策略
            use_extract_tables_fallback=False
        )

        # 性能测试（可选）
        # test_pdfplumber_performance(pdf_file)

    else:
        print("请将PDF文件路径替换为实际路径")
        print("示例用法:")
        print("pdf_to_markdown('文件.pdf', '输出.md', dedupe_by_text_match=True)")
        print("batch_convert_pdfs('目录', dedupe_by_text_match=True)")
        print("test_pdfplumber_performance('文件.pdf')")
