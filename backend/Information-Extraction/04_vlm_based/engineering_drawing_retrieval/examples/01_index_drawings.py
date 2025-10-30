"""
示例1: 建立工程图纸索引
演示如何将PDF中的工程图纸批量索引到向量数据库
"""
import asyncio
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from core.vlm_analyzer import EngineeringDrawingAnalyzer
from core.image_preprocessor import ImagePreprocessor
from core.vector_store import EngineeringDrawingVectorStore
import fitz  # PyMuPDF


class DrawingIndexer:
    """工程图纸索引器"""

    def __init__(self):
        self.analyzer = EngineeringDrawingAnalyzer()
        self.preprocessor = ImagePreprocessor()
        self.vector_store = EngineeringDrawingVectorStore()

    async def index_pdf(
        self,
        pdf_path: str,
        output_dir: str = "output/extracted_images",
        auto_classify: bool = True
    ):
        """
        从PDF提取并索引所有页面

        Args:
            pdf_path: PDF文件路径
            output_dir: 图像输出目录
            auto_classify: 是否自动分类图像类型
        """
        print(f"开始处理PDF: {pdf_path}")
        print("=" * 60)

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 打开PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"总页数: {total_pages}\n")

        indexed_count = 0
        failed_count = 0

        for page_num in range(total_pages):
            page = doc[page_num]
            print(f"处理第 {page_num + 1}/{total_pages} 页...")

            # 保存页面为图像
            image_path = output_path / f"page_{page_num + 1}.png"
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                pix.save(str(image_path))
                pix = None
            except Exception as e:
                print(f"  ✗ 图像保存失败: {e}")
                failed_count += 1
                continue

            # 图像质量检测
            quality = self.preprocessor.detect_image_quality(str(image_path))
            print(f"  图像质量: {quality['resolution']}, 清晰度: {quality['blur_score']:.1f}")

            if not quality["is_high_quality"]:
                print(f"  ⚠ 图像质量较低，跳过")
                continue

            # OCR提取小字标注
            ocr_text = ""
            if self.preprocessor.config.enable_ocr:
                ocr_text = self.preprocessor.extract_text_summary(str(image_path))
                if ocr_text:
                    print(f"  OCR提取: {len(ocr_text)} 字符")

            # 自动分类图像类型
            image_type = "engineering_drawing"
            if auto_classify:
                try:
                    image_type = await self.analyzer.classify_image_type(str(image_path))
                    print(f"  图像类型: {image_type}")
                except Exception as e:
                    print(f"  ⚠ 类型分类失败: {e}")

            # VLM分析
            try:
                result = await self.analyzer.analyze_image(
                    str(image_path),
                    image_type=image_type
                )
                print(f"  ✓ VLM分析完成")
                print(f"  描述摘要: {result.description[:100]}...")

                # 添加到向量库
                metadata = {
                    "image_type": result.image_type,
                    "page_number": page_num + 1,
                    "source_pdf": Path(pdf_path).name,
                    "structured_data": result.structured_data,
                    "ocr_text": ocr_text,
                    "quality": quality
                }

                doc_id = await self.vector_store.add_drawing(
                    image_path=str(image_path),
                    description=result.description,
                    metadata=metadata
                )

                print(f"  ✓ 已索引 (ID: {doc_id[:8]}...)")
                indexed_count += 1

            except Exception as e:
                print(f"  ✗ 索引失败: {e}")
                failed_count += 1

            print()

        doc.close()

        # 统计信息
        print("=" * 60)
        print(f"索引完成!")
        print(f"  成功: {indexed_count} 页")
        print(f"  失败: {failed_count} 页")
        print(f"  总计: {total_pages} 页")

        # 向量库统计
        try:
            stats = self.vector_store.get_collection_stats()
            print(f"\n向量库统计: {stats}")
        except:
            pass

    async def index_images(
        self,
        image_paths: list,
        auto_classify: bool = True,
        max_concurrent: int = 3
    ):
        """
        批量索引图像文件

        Args:
            image_paths: 图像路径列表
            auto_classify: 是否自动分类
            max_concurrent: 最大并发数
        """
        print(f"开始批量索引 {len(image_paths)} 张图像")
        print("=" * 60)

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_one(image_path):
            async with semaphore:
                try:
                    print(f"\n处理: {Path(image_path).name}")

                    # 自动分类
                    image_type = "engineering_drawing"
                    if auto_classify:
                        image_type = await self.analyzer.classify_image_type(image_path)
                        print(f"  类型: {image_type}")

                    # VLM分析
                    result = await self.analyzer.analyze_image(image_path, image_type)

                    # 索引
                    metadata = {
                        "image_type": result.image_type,
                        "source": Path(image_path).name,
                        "structured_data": result.structured_data
                    }

                    doc_id = await self.vector_store.add_drawing(
                        image_path=image_path,
                        description=result.description,
                        metadata=metadata
                    )

                    print(f"  ✓ 已索引 (ID: {doc_id[:8]}...)")
                    return True

                except Exception as e:
                    print(f"  ✗ 失败: {e}")
                    return False

        # 并发处理
        results = await asyncio.gather(*[process_one(path) for path in image_paths])

        # 统计
        success = sum(results)
        print("\n" + "=" * 60)
        print(f"索引完成: 成功 {success}/{len(image_paths)}")


async def main():
    """主函数"""
    indexer = DrawingIndexer()

    # ===== 示例1: 索引PDF文档 =====
    pdf_path = "/path/to/engineering_document.pdf"

    if Path(pdf_path).exists():
        await indexer.index_pdf(
            pdf_path=pdf_path,
            output_dir="output/drawings",
            auto_classify=True
        )
    else:
        print(f"PDF文件不存在: {pdf_path}")

    # ===== 示例2: 索引图像目录 =====
    # image_dir = Path("/path/to/drawings")
    # if image_dir.exists():
    #     image_paths = list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpg"))
    #     await indexer.index_images(image_paths, auto_classify=True)


if __name__ == "__main__":
    asyncio.run(main())
