#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDFPlumber PDF到Markdown转换器
专注于高精度的表格提取和文本结构化处理
适用场景：学术论文、报告、带有复杂表格的文档
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import json

try:
    import pdfplumber
except ImportError:
    raise ImportError("请安装pdfplumber: pip install pdfplumber")


class PDFPlumberConverter:
    """基于PDFPlumber的高精度PDF转Markdown转换器"""
    
    def __init__(self, 
                 extract_tables: bool = True,
                 extract_images: bool = True,
                 min_table_confidence: float = 0.5,
                 table_settings: Optional[Dict] = None):
        """
        初始化转换器
        
        Args:
            extract_tables: 是否提取表格
            extract_images: 是否提取图片信息
            min_table_confidence: 表格识别最低置信度
            table_settings: 表格提取设置
        """
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.min_table_confidence = min_table_confidence
        
        # 默认表格设置
        self.table_settings = table_settings or {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines", 
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 3,
            "min_words_horizontal": 1,
            "intersection_tolerance": 3,
            "text_tolerance": 3,
            "text_x_tolerance": 3,
            "text_y_tolerance": 3
        }
        
        self.logger = self._setup_logger()
        
        # 文本处理配置
        self.font_size_threshold = {
            'title': 16,      # 主标题
            'heading': 14,    # 二级标题
            'subheading': 12, # 三级标题
        }
        
        # 标题关键词
        self.title_patterns = [
            r'^第[一二三四五六七八九十\d]+[章节部分]',
            r'^Chapter\s+\d+',
            r'^Section\s+\d+',
            r'^\d+[\.\s]+',
            r'^[一二三四五六七八九十]+[\.\s、]+',
            r'^（[一二三四五六七八九十]+）',
            r'^\([一二三四五六七八九十\d]+\)',
            r'^[IVXLCDM]+[\.\s]+',  # 罗马数字
        ]
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(f"{__name__}.PDFPlumberConverter")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _analyze_text_properties(self, page) -> Dict[str, Any]:
        """分析页面文本属性"""
        chars = page.chars
        if not chars:
            return {}
        
        # 统计字体大小分布
        font_sizes = [char.get('size', 12) for char in chars if char.get('size')]
        font_names = [char.get('fontname', '') for char in chars if char.get('fontname')]
        
        # 计算统计信息
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
        max_font_size = max(font_sizes) if font_sizes else 12
        min_font_size = min(font_sizes) if font_sizes else 12
        
        # 最常见的字体
        from collections import Counter
        most_common_font = Counter(font_names).most_common(1)
        main_font = most_common_font[0][0] if most_common_font else ''
        
        return {
            'avg_font_size': avg_font_size,
            'max_font_size': max_font_size,
            'min_font_size': min_font_size,
            'main_font': main_font,
            'font_sizes': font_sizes,
            'font_names': font_names
        }
    
    def _is_title_by_format(self, text: str, font_size: float, avg_font_size: float, 
                           is_bold: bool = False, is_centered: bool = False) -> Tuple[bool, int]:
        """
        根据格式判断是否为标题
        
        Returns:
            (is_title, level) - 是否为标题和标题级别(1-6)
        """
        text = text.strip()
        if not text or len(text) > 200:  # 太长不是标题
            return False, 0
        
        # 字体大小判断
        size_ratio = font_size / avg_font_size if avg_font_size > 0 else 1
        
        level = 0
        is_title = False
        
        # 基于字体大小的标题级别判断
        if size_ratio >= 1.5:  # 字体明显大于平均大小
            is_title = True
            if size_ratio >= 2.0:
                level = 1  # 一级标题
            elif size_ratio >= 1.8:
                level = 2  # 二级标题
            else:
                level = 3  # 三级标题
        
        # 格式特征加权
        if is_bold:
            is_title = True
            level = max(level, 3)
        
        if is_centered and len(text) < 100:
            is_title = True
            level = max(level, 2)
        
        # 内容模式匹配
        for pattern in self.title_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                is_title = True
                level = max(level, 2)
                break
        
        # 特殊情况：全大写短文本
        if text.isupper() and 5 < len(text) < 50:
            is_title = True
            level = max(level, 3)
        
        return is_title, max(level, 1) if is_title else 0
    
    def _extract_text_with_structure(self, page) -> List[Dict[str, Any]]:
        """提取带结构信息的文本"""
        text_elements = []
        
        # 获取文本属性分析
        text_props = self._analyze_text_properties(page)
        avg_font_size = text_props.get('avg_font_size', 12)
        
        # 按行提取文本
        try:
            # 尝试获取文本行
            lines = page.extract_text_lines()
            
            for line in lines:
                text = line.get('text', '').strip()
                if not text:
                    continue
                
                # 获取行的字体信息
                chars = line.get('chars', [])
                if chars:
                    # 计算这一行的平均字体大小
                    line_font_sizes = [c.get('size', 12) for c in chars if c.get('size')]
                    line_font_size = sum(line_font_sizes) / len(line_font_sizes) if line_font_sizes else 12
                    
                    # 检查是否加粗
                    font_names = [c.get('fontname', '') for c in chars if c.get('fontname')]
                    is_bold = any('bold' in name.lower() or 'heavy' in name.lower() for name in font_names)
                    
                    # 检查是否居中（简单判断）
                    line_bbox = line.get('bbox', [0, 0, 0, 0])
                    page_width = page.width
                    is_centered = abs((line_bbox[0] + line_bbox[2]) / 2 - page_width / 2) < page_width * 0.1
                else:
                    line_font_size = avg_font_size
                    is_bold = False
                    is_centered = False
                
                # 判断是否为标题
                is_title, title_level = self._is_title_by_format(
                    text, line_font_size, avg_font_size, is_bold, is_centered
                )
                
                text_elements.append({
                    'text': text,
                    'type': 'title' if is_title else 'paragraph',
                    'level': title_level if is_title else 0,
                    'font_size': line_font_size,
                    'is_bold': is_bold,
                    'is_centered': is_centered,
                    'bbox': line.get('bbox', [0, 0, 0, 0])
                })
        
        except Exception as e:
            self.logger.warning(f"文本行提取失败，使用简单提取: {e}")
            # 备用方法：简单文本提取
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        is_title, title_level = self._is_title_by_format(
                            line, avg_font_size, avg_font_size
                        )
                        text_elements.append({
                            'text': line,
                            'type': 'title' if is_title else 'paragraph', 
                            'level': title_level if is_title else 0,
                            'font_size': avg_font_size,
                            'is_bold': False,
                            'is_centered': False,
                            'bbox': [0, 0, 0, 0]
                        })
        
        return text_elements
    
    def _extract_tables_advanced(self, page) -> List[Dict[str, Any]]:
        """高级表格提取"""
        tables_data = []
        
        if not self.extract_tables:
            return tables_data
        
        try:
            # 使用多种策略提取表格
            strategies = [
                {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
                {"vertical_strategy": "lines", "horizontal_strategy": "text"},
                {"vertical_strategy": "text", "horizontal_strategy": "lines"},
                {"vertical_strategy": "text", "horizontal_strategy": "text"},
            ]
            
            all_tables = []
            
            for strategy in strategies:
                try:
                    settings = {**self.table_settings, **strategy}
                    tables = page.extract_tables(table_settings=settings)
                    
                    if tables:
                        for table in tables:
                            if table and len(table) > 1:  # 至少要有2行
                                # 计算表格质量分数
                                quality_score = self._calculate_table_quality(table)
                                if quality_score >= self.min_table_confidence:
                                    all_tables.append({
                                        'table': table,
                                        'quality': quality_score,
                                        'strategy': strategy
                                    })
                except Exception as e:
                    self.logger.debug(f"表格提取策略 {strategy} 失败: {e}")
                    continue
            
            # 去重并选择最佳表格
            if all_tables:
                # 按质量排序
                all_tables.sort(key=lambda x: x['quality'], reverse=True)
                
                # 简单去重（基于表格大小）
                unique_tables = []
                seen_sizes = set()
                
                for table_info in all_tables:
                    table = table_info['table']
                    table_size = (len(table), len(table[0]) if table and table[0] else 0)
                    
                    if table_size not in seen_sizes:
                        seen_sizes.add(table_size)
                        
                        # 清理表格数据
                        cleaned_table = self._clean_table_data(table)
                        
                        tables_data.append({
                            'table': cleaned_table,
                            'rows': len(cleaned_table),
                            'cols': len(cleaned_table[0]) if cleaned_table else 0,
                            'quality': table_info['quality'],
                            'strategy': table_info['strategy']
                        })
        
        except Exception as e:
            self.logger.error(f"表格提取失败: {e}")
        
        return tables_data
    
    def _calculate_table_quality(self, table: List[List[str]]) -> float:
        """计算表格质量分数"""
        if not table or not table[0]:
            return 0.0
        
        score = 0.0
        total_cells = len(table) * len(table[0])
        
        # 非空单元格比例
        non_empty_cells = 0
        for row in table:
            for cell in row:
                if cell and str(cell).strip():
                    non_empty_cells += 1
        
        non_empty_ratio = non_empty_cells / total_cells if total_cells > 0 else 0
        score += non_empty_ratio * 0.4
        
        # 表格规整性（每行列数一致）
        col_counts = [len(row) for row in table]
        if len(set(col_counts)) == 1:  # 所有行列数相同
            score += 0.3
        
        # 表格大小合理性
        if 2 <= len(table) <= 50 and 2 <= len(table[0]) <= 20:
            score += 0.2
        
        # 表头质量（第一行与其他行的差异）
        if len(table) > 1:
            first_row = table[0]
            other_rows = table[1:]
            
            # 检查第一行是否更可能是表头
            first_row_text_len = sum(len(str(cell)) for cell in first_row if cell)
            avg_other_row_len = sum(
                sum(len(str(cell)) for cell in row if cell) 
                for row in other_rows
            ) / len(other_rows) if other_rows else 0
            
            if first_row_text_len > avg_other_row_len * 0.8:
                score += 0.1
        
        return min(score, 1.0)
    
    def _clean_table_data(self, table: List[List[str]]) -> List[List[str]]:
        """清理表格数据"""
        if not table:
            return table
        
        cleaned_table = []
        for row in table:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("")
                else:
                    # 清理单元格文本
                    cell_text = str(cell).strip()
                    # 移除多余的空白字符
                    cell_text = re.sub(r'\s+', ' ', cell_text)
                    cleaned_row.append(cell_text)
            cleaned_table.append(cleaned_row)
        
        return cleaned_table
    
    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """将表格转换为Markdown格式"""
        if not table or not table[0]:
            return ""
        
        markdown_lines = []
        
        # 表头
        header_row = "| " + " | ".join(self._escape_markdown_table_cell(cell) for cell in table[0]) + " |"
        markdown_lines.append(header_row)
        
        # 分隔行
        separator = "| " + " | ".join("---" for _ in table[0]) + " |"
        markdown_lines.append(separator)
        
        # 数据行
        for row in table[1:]:
            # 确保行长度与表头一致
            while len(row) < len(table[0]):
                row.append("")
            
            data_row = "| " + " | ".join(self._escape_markdown_table_cell(cell) for cell in row[:len(table[0])]) + " |"
            markdown_lines.append(data_row)
        
        return "\n".join(markdown_lines)
    
    def _escape_markdown_table_cell(self, cell: str) -> str:
        """转义表格单元格中的Markdown特殊字符"""
        if not cell:
            return ""
        
        cell = str(cell)
        # 转义管道符和换行符
        cell = cell.replace("|", "\\|")
        cell = cell.replace("\n", "<br>")
        cell = cell.replace("\r", "")
        
        return cell
    
    def _extract_images_info(self, page, image_output_dir: Optional[str] = None, image_rel_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """提取图片信息并可选保存图片

        如果提供了 image_output_dir，会将页面渲染为PIL图像并裁切保存每个图片区域为PNG。
        返回的每个图片字典在保存成功时会包含'saved_path'字段。
        """
        images_info = []
        
        if not self.extract_images:
            return images_info

        try:
            images = page.images

            # 如果准备保存图片，先渲染整页为PIL图像以便裁切
            pil_page_img = None
            scale = 1.0
            if image_output_dir and images:
                try:
                    os.makedirs(image_output_dir, exist_ok=True)
                except Exception:
                    pass

                try:
                    page_image_obj = page.to_image(resolution=150)
                    pil_page_img = page_image_obj.original
                    # 计算缩放比例：PIL像素宽 / PDF单位宽
                    scale = pil_page_img.width / page.width if page.width else 1.0
                except Exception as e:
                    self.logger.debug(f"页面渲染为图片失败，无法保存裁切图片: {e}")
                    pil_page_img = None

            for i, img in enumerate(images):
                info = {
                    'index': i,
                    'x0': img.get('x0', 0),
                    'y0': img.get('y0', 0),
                    'x1': img.get('x1', 0),
                    'y1': img.get('y1', 0),
                    'width': img.get('width', 0),
                    'height': img.get('height', 0),
                    'object_type': img.get('object_type', 'image'),
                    'page_number': page.page_number
                }

                # 如果有渲染好的整页图片，尝试裁切并保存
                if pil_page_img and image_output_dir:
                    try:
                        x0 = img.get('x0', 0)
                        y0 = img.get('y0', 0)
                        x1 = img.get('x1', 0)
                        y1 = img.get('y1', 0)

                        left = int(x0 * scale)
                        right = int(x1 * scale)
                        # PDF坐标原点在左下，PIL在左上，需翻转y坐标
                        top = int((page.height - y1) * scale)
                        bottom = int((page.height - y0) * scale)

                        # 修正边界
                        left = max(0, left)
                        top = max(0, top)
                        right = min(pil_page_img.width, right)
                        bottom = min(pil_page_img.height, bottom)

                        if right > left and bottom > top:
                            cropped = pil_page_img.crop((left, top, right, bottom))
                            fname = f"page_{page.page_number:03d}_img_{i}.png"
                            saved_path = os.path.join(image_output_dir, fname)
                            try:
                                cropped.save(saved_path)
                                info['saved_path'] = saved_path
                                # 额外记录相对路径，便于在Markdown中引用（如果提供了image_rel_dir）
                                if image_rel_dir:
                                    info['saved_rel_path'] = os.path.join(image_rel_dir, fname)
                                else:
                                    info['saved_rel_path'] = fname
                            except Exception as e:
                                self.logger.debug(f"保存图片失败: {e}")
                    except Exception as e:
                        self.logger.debug(f"图片裁切保存失败: {e}")

                images_info.append(info)
        except Exception as e:
            self.logger.debug(f"图片信息提取失败: {e}")

        return images_info
    
    def convert_page(self, page, page_number: int, image_output_dir: Optional[str] = None, image_rel_dir: Optional[str] = None) -> Dict[str, Any]:
        """转换单个页面"""
        self.logger.debug(f"处理第 {page_number} 页")
        
        # 提取文本结构
        text_elements = self._extract_text_with_structure(page)
        
        # 提取表格
        tables = self._extract_tables_advanced(page)
        
        # 提取图片信息并可选保存
        images = self._extract_images_info(page, image_output_dir, image_rel_dir)
        
        return {
            'page_number': page_number,
            'text_elements': text_elements,
            'tables': tables,
            'images': images,
            'width': page.width,
            'height': page.height
        }
    
    def _build_markdown_from_page_data(self, page_data: Dict[str, Any]) -> str:
        """从页面数据构建Markdown"""
        markdown_lines = []
        page_number = page_data['page_number']
        
        # 页面标题
        markdown_lines.append(f"# 第 {page_number} 页\n")
        
        # 处理文本元素和表格的混合布局
        text_elements = page_data['text_elements']
        tables = page_data['tables']
        images = page_data['images']
        
        # 插入文本
        for element in text_elements:
            text = element['text']
            element_type = element['type']
            level = element['level']
            
            if element_type == 'title' and level > 0:
                # 标题
                heading_prefix = '#' * min(level + 1, 6)  # 最多6级标题
                markdown_lines.append(f"{heading_prefix} {text}\n")
            else:
                # 普通段落
                markdown_lines.append(f"{text}\n")
        
        # 添加表格
        if tables:
            markdown_lines.append("\n## 表格\n")
            for i, table_info in enumerate(tables, 1):
                markdown_lines.append(f"### 表格 {i}\n")
                
                table_md = self._table_to_markdown(table_info['table'])
                markdown_lines.append(table_md)
                markdown_lines.append(f"\n*表格质量分数: {table_info['quality']:.2f}*\n")
        
        # 添加图片信息
        if images:
            markdown_lines.append("\n## 图片\n")
            for img in images:
                # 基本描述行
                desc = (
                    f"- 图片 {img['index'] + 1}: 位置({img['x0']:.1f}, {img['y0']:.1f}) "
                    f"大小{img['width']:.1f}×{img['height']:.1f}"
                )
                markdown_lines.append(desc + "\n")

                # 如果保存了相对路径，则插入 Markdown 图片语法以便渲染
                relp = img.get('saved_rel_path') or img.get('saved_path')
                if relp:
                    # 使用相对路径显示图片（如果是绝对路径，Markdown查看器可能也能显示）
                    markdown_lines.append(f"![]({relp})\n")
        
        return ''.join(markdown_lines)
    
    def convert(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        转换PDF到Markdown
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出Markdown文件路径
            
        Returns:
            Markdown内容
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        self.logger.info(f"开始转换PDF: {pdf_path}")
        start_time = datetime.now()
        
        markdown_content = []
        
        # 添加文档元数据
        metadata = f"""---
title: {Path(pdf_path).stem}
source: {os.path.basename(pdf_path)}
converter: PDFPlumber
conversion_time: {datetime.now().isoformat()}
extract_tables: {self.extract_tables}
extract_images: {self.extract_images}
---

"""
        markdown_content.append(metadata)
        
        # 准备图片保存目录（如果指定了输出文件，则在其同目录创建 <stem>_images 文件夹）
        image_output_dir = None
        image_rel_dir = None
        if output_path:
            out_md = Path(output_path)
            image_output_dir = str(out_md.parent / f"{out_md.stem}_images")
            # 在Markdown中引用时使用相对路径（相对于输出md文件的目录）
            image_rel_dir = os.path.join(f"{out_md.stem}_images")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                self.logger.info(f"PDF共 {total_pages} 页")
                
                # 转换每一页
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_data = self.convert_page(page, page_num, image_output_dir=image_output_dir, image_rel_dir=image_rel_dir)
                        page_markdown = self._build_markdown_from_page_data(page_data)
                        markdown_content.append(page_markdown)
                        markdown_content.append("\n---\n\n")  # 页面分隔符
                        
                        if page_num % 10 == 0:
                            self.logger.info(f"已处理 {page_num}/{total_pages} 页")
                    
                    except Exception as e:
                        self.logger.error(f"处理第 {page_num} 页失败: {e}")
                        markdown_content.append(f"# 第 {page_num} 页\n\n*[页面处理失败: {e}]*\n\n---\n\n")
        
        except Exception as e:
            self.logger.error(f"PDF文件打开失败: {e}")
            raise
        
        final_content = ''.join(markdown_content)
        
        # 保存文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            self.logger.info(f"Markdown文件已保存: {output_path}")
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"转换完成，耗时: {duration:.2f}秒")
        
        return final_content


def main():
    """命令行使用示例"""
    import argparse

    parser = argparse.ArgumentParser(description="PDFPlumber PDF到Markdown转换器")
    parser.add_argument("input_pdf", nargs='?', 
                       default="/home/data/nongwa/workspace/data/阿里开发手册-泰山版.pdf",
                       help="输入PDF文件路径")
    parser.add_argument("-o", "--output", 
                       default="output/阿里开发手册-泰山版.md", 
                       help="输出Markdown文件路径")
    parser.add_argument("--no-tables", action="store_true", help="不提取表格")
    parser.add_argument("--no-images", action="store_true", help="不提取图片信息")
    parser.add_argument("--table-confidence", type=float, default=0.5, help="表格识别最低置信度")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    

    # 处理输出路径：支持传入目录或文件（相对或绝对），并为每个输出文件创建自己的目录
    # 规则：
    # - 如果用户传入的是一个目录（已存在或以/结尾），在该目录下为输入PDF的stem创建一个子目录，最终输出文件为 <dir>/<pdf_stem>/<pdf_stem>.md
    # - 如果用户传入的是一个文件路径（相对或绝对），则在该文件父目录下创建一个以该文件stem命名的子目录，最终输出文件为 <parent>/<file_stem>/<original_filename>
    input_pdf = args.input_pdf
    requested_out = args.output
    if requested_out:
        # 规范为绝对路径用于判断
        # 当用户传入看起来像目录（存在且是目录，或以路径分隔符结尾），按目录处理
        if os.path.isdir(requested_out) or requested_out.endswith(os.sep):
            base_dir = os.path.abspath(requested_out)
            final_dir = os.path.join(base_dir, Path(input_pdf).stem)
            os.makedirs(final_dir, exist_ok=True)
            final_output = os.path.join(final_dir, f"{Path(input_pdf).stem}.md")
        else:
            # 用户传入的是文件路径（可能是相对路径）
            abs_req = os.path.abspath(requested_out)
            parent = os.path.dirname(abs_req) or os.getcwd()
            file_stem = Path(abs_req).stem
            final_dir = os.path.join(parent, file_stem)
            os.makedirs(final_dir, exist_ok=True)
            # 保持用户期望的文件名（basename of requested_out）
            final_output = os.path.join(final_dir, Path(abs_req).name)

        args.output = final_output
    else:
        # 未指定输出时使用 input_pdf 同目录并创建子目录
        abs_input = os.path.abspath(input_pdf)
        parent = os.path.dirname(abs_input)
        stem = Path(abs_input).stem
        final_dir = os.path.join(parent, stem)
        os.makedirs(final_dir, exist_ok=True)
        args.output = os.path.join(final_dir, f"{stem}.md")
    # 创建转换器
    converter = PDFPlumberConverter(
        extract_tables=not args.no_tables,
        extract_images=not args.no_images,
        min_table_confidence=args.table_confidence
    )
    
    try:
        # 转换
        markdown_content = converter.convert(args.input_pdf, args.output)
        print(f"转换完成: {args.output}")
        
    except Exception as e:
        print(f"转换失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())