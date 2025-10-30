"""
快速开始示例
完整演示：索引 -> 检索 -> 结果展示
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.vlm_analyzer import EngineeringDrawingAnalyzer
from core.vector_store import EngineeringDrawingVectorStore
from retrievers.hybrid_retriever import HybridRetriever


async def quickstart():
    """快速开始流程"""

    print("=" * 80)
    print("工程图纸语义检索系统 - 快速开始")
    print("=" * 80)

    # ========== 步骤1: 初始化组件 ==========
    print("\n【步骤1】初始化组件...")
    analyzer = EngineeringDrawingAnalyzer()
    vector_store = EngineeringDrawingVectorStore()
    retriever = HybridRetriever()
    print("✓ 组件初始化完成")

    # ========== 步骤2: 分析图像 ==========
    print("\n【步骤2】分析工程图纸...")

    # 示例图像路径（替换为你的实际路径）
    test_images = [
        "/path/to/drawing1.png",
        "/path/to/drawing2.png",
        "/path/to/architecture.png"
    ]

    # 过滤存在的文件
    existing_images = [img for img in test_images if Path(img).exists()]

    if not existing_images:
        print("⚠ 未找到示例图像，请修改 test_images 路径")
        print("\n提示: 你可以使用以下方式准备图像:")
        print("  1. 从PDF提取: 参考 examples/01_index_drawings.py")
        print("  2. 直接提供图像文件（PNG/JPG）")
        return

    print(f"找到 {len(existing_images)} 张图像\n")

    indexed_drawings = []

    for i, image_path in enumerate(existing_images, 1):
        print(f"[{i}/{len(existing_images)}] 分析: {Path(image_path).name}")

        try:
            # 自动识别类型
            image_type = await analyzer.classify_image_type(image_path)
            print(f"  类型: {image_type}")

            # VLM分析
            result = await analyzer.analyze_image(image_path, image_type)
            print(f"  ✓ 分析完成")
            print(f"  描述: {result.description[:80]}...")

            indexed_drawings.append({
                "image_path": image_path,
                "image_type": result.image_type,
                "description": result.description,
                "structured_data": result.structured_data
            })

        except Exception as e:
            print(f"  ✗ 分析失败: {e}")

        print()

    if not indexed_drawings:
        print("⚠ 没有成功分析的图像")
        return

    # ========== 步骤3: 建立索引 ==========
    print("【步骤3】建立向量索引...")

    for drawing in indexed_drawings:
        try:
            metadata = {
                "image_type": drawing["image_type"],
                "structured_data": drawing["structured_data"]
            }

            doc_id = await vector_store.add_drawing(
                image_path=drawing["image_path"],
                description=drawing["description"],
                metadata=metadata
            )

            print(f"  ✓ 已索引: {Path(drawing['image_path']).name} (ID: {doc_id[:8]}...)")

        except Exception as e:
            print(f"  ✗ 索引失败: {e}")

    print()

    # ========== 步骤4: 检索测试 ==========
    print("【步骤4】执行检索测试...\n")

    test_queries = [
        "查找所有工程制造图纸",
        "系统架构相关的设计图",
        "包含尺寸标注的CAD图"
    ]

    for query in test_queries:
        print(f"查询: {query}")
        print("-" * 60)

        try:
            results = await retriever.search(query, top_k=3)

            if results:
                for result in results:
                    print(f"  [{result.rank}] {Path(result.image_path).name}")
                    print(f"      相似度: {result.score:.3f}")
                    print(f"      类型: {result.metadata.get('image_type')}")
                    print(f"      {result.description[:80]}...")
                    print()
            else:
                print("  未找到相关结果\n")

        except Exception as e:
            print(f"  检索失败: {e}\n")

    # ========== 步骤5: 统计信息 ==========
    print("【步骤5】系统统计信息")
    print("-" * 60)

    try:
        stats = vector_store.get_collection_stats()
        print(f"向量库: {stats}")
    except Exception as e:
        print(f"统计信息获取失败: {e}")

    print("\n" + "=" * 80)
    print("快速开始完成!")
    print("=" * 80)
    print("\n下一步:")
    print("  1. 运行 examples/01_index_drawings.py 索引你的PDF文档")
    print("  2. 运行 examples/02_search_drawings.py 进行交互式检索")
    print("  3. 查看 README.md 了解更多功能")


async def simple_test():
    """
    简化版测试（不需要实际图像）
    仅测试组件是否正常初始化
    """
    print("=" * 60)
    print("组件测试")
    print("=" * 60)

    try:
        print("\n1. 测试VLM分析器...")
        analyzer = EngineeringDrawingAnalyzer()
        print("   ✓ VLM分析器初始化成功")

        print("\n2. 测试向量存储...")
        vector_store = EngineeringDrawingVectorStore()
        print("   ✓ 向量存储初始化成功")

        print("\n3. 测试检索器...")
        retriever = HybridRetriever()
        print("   ✓ 检索器初始化成功")

        print("\n4. 测试向量库连接...")
        try:
            stats = vector_store.get_collection_stats()
            print(f"   ✓ 向量库连接成功: {stats}")
        except Exception as e:
            print(f"   ⚠ 向量库连接失败: {e}")
            print("   提示: 请确保Milvus服务已启动")

        print("\n" + "=" * 60)
        print("✓ 所有组件测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="工程图纸检索系统快速开始")
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="仅测试组件，不执行完整流程"
    )

    args = parser.parse_args()

    if args.test_only:
        asyncio.run(simple_test())
    else:
        asyncio.run(quickstart())
