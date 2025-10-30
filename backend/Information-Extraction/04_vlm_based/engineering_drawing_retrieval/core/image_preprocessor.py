"""
图像预处理模块
包含OCR、去噪、增强等功能
"""
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config


class ImagePreprocessor:
    """图像预处理器"""

    def __init__(self):
        self.config = config.image
        self.ocr_engine = None

        # 懒加载OCR引擎
        if self.config.enable_ocr:
            self._init_ocr()

    def _init_ocr(self):
        """初始化OCR引擎"""
        if self.config.ocr_engine == "paddleocr":
            try:
                from paddleocr import PaddleOCR
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.config.ocr_lang,
                    show_log=False
                )
                print("✓ PaddleOCR 初始化成功")
            except ImportError:
                print("⚠ PaddleOCR未安装，OCR功能将被禁用")
                print("安装命令: pip install paddleocr paddlepaddle")
                self.config.enable_ocr = False

    def preprocess_image(
        self,
        image_path: str,
        enhance: bool = True,
        denoise: bool = False
    ) -> Image.Image:
        """
        预处理图像

        Args:
            image_path: 图像路径
            enhance: 是否增强
            denoise: 是否去噪

        Returns:
            处理后的PIL Image对象
        """
        img = Image.open(image_path)

        # 转换为RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 去噪
        if denoise:
            img = self._denoise(img)

        # 增强
        if enhance:
            img = self._enhance(img)

        return img

    def _denoise(self, img: Image.Image) -> Image.Image:
        """去噪"""
        # 使用PIL的滤镜去噪
        img = img.filter(ImageFilter.MedianFilter(size=3))
        return img

    def _enhance(self, img: Image.Image) -> Image.Image:
        """
        增强图像（适用于工程图纸）
        提高对比度和清晰度
        """
        # 增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)

        # 增强清晰度
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)

        return img

    def extract_text_ocr(self, image_path: str) -> List[Dict]:
        """
        使用OCR提取图像中的文本
        特别适合提取小字说明、标注

        Args:
            image_path: 图像路径

        Returns:
            OCR结果列表，每个元素包含 {text, bbox, confidence}
        """
        if not self.config.enable_ocr or self.ocr_engine is None:
            return []

        try:
            result = self.ocr_engine.ocr(image_path, cls=True)

            ocr_results = []
            if result and result[0]:
                for line in result[0]:
                    bbox = line[0]  # 边界框坐标
                    text = line[1][0]  # 文本内容
                    confidence = line[1][1]  # 置信度

                    ocr_results.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence
                    })

            return ocr_results

        except Exception as e:
            print(f"OCR提取失败: {e}")
            return []

    def extract_text_summary(self, image_path: str) -> str:
        """
        提取图像中所有文本的摘要

        Args:
            image_path: 图像路径

        Returns:
            文本摘要
        """
        ocr_results = self.extract_text_ocr(image_path)

        if not ocr_results:
            return ""

        # 按置信度过滤
        filtered_results = [
            r for r in ocr_results
            if r["confidence"] > 0.6
        ]

        # 拼接文本
        text_summary = " ".join([r["text"] for r in filtered_results])

        return text_summary

    def detect_image_quality(self, image_path: str) -> Dict:
        """
        检测图像质量

        Returns:
            {
                "resolution": (width, height),
                "is_high_quality": bool,
                "blur_score": float,
                "brightness": float
            }
        """
        img = Image.open(image_path)
        img_array = cv2.imread(str(image_path))

        # 分辨率
        width, height = img.size

        # 模糊度检测（Laplacian方差）
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

        # 亮度
        brightness = np.mean(img_array)

        # 判断是否高质量
        is_high_quality = (
            width >= 800 and
            height >= 600 and
            blur_score > 100 and
            50 < brightness < 200
        )

        return {
            "resolution": (width, height),
            "is_high_quality": is_high_quality,
            "blur_score": float(blur_score),
            "brightness": float(brightness)
        }

    def split_large_image(
        self,
        image_path: str,
        max_size: int = 2000,
        overlap: int = 100
    ) -> List[Image.Image]:
        """
        分割大图像（适用于超大工程图纸）

        Args:
            image_path: 图像路径
            max_size: 最大尺寸
            overlap: 重叠区域大小

        Returns:
            分割后的图像列表
        """
        img = Image.open(image_path)
        width, height = img.size

        if width <= max_size and height <= max_size:
            return [img]

        crops = []
        step = max_size - overlap

        for y in range(0, height, step):
            for x in range(0, width, step):
                box = (
                    x,
                    y,
                    min(x + max_size, width),
                    min(y + max_size, height)
                )
                crop = img.crop(box)
                crops.append(crop)

        return crops


# 便捷函数
def quick_preprocess(image_path: str) -> Image.Image:
    """快速预处理"""
    preprocessor = ImagePreprocessor()
    return preprocessor.preprocess_image(image_path)


def extract_all_text(image_path: str) -> str:
    """快速提取所有文本"""
    preprocessor = ImagePreprocessor()
    return preprocessor.extract_text_summary(image_path)


if __name__ == "__main__":
    # 测试代码
    preprocessor = ImagePreprocessor()

    test_image = "/path/to/test.jpg"
    if Path(test_image).exists():
        # 测试OCR
        text = preprocessor.extract_text_summary(test_image)
        print(f"提取的文本: {text}")

        # 测试质量检测
        quality = preprocessor.detect_image_quality(test_image)
        print(f"图像质量: {quality}")
