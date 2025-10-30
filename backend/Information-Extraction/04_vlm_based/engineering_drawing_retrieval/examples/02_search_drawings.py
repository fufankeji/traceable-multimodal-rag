"""
示例2: 检索工程图纸
演示如何使用自然语言检索工程图纸
"""
import asyncio
import sys
import json
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from retrievers.hybrid_retriever import HybridRetriever
from config import IMAGE_TYPES


async def example_basic_search():
    """示例1: 基础文本检索"""
    print("=" * 60)
    print("示例1: 基础文本检索")
    print("=" * 60)

    retriever = HybridRetriever()

    # 查询
    query = "查找所有关于轴承的工程制造图纸"
    print(f"\n查询: {query}\n")

    results = await retriever.search(query, top_k=5)

    # 输出结果
    print(retriever.format_results(results))


async def example_filtered_search():
    """示例2: 带过滤条件的检索"""
    print("\n" + "=" * 60)
    print("示例2: 带过滤条件的检索")
    print("=" * 60)

    retriever = HybridRetriever()

    # 查询CAD图纸
    query = "冷却系统设计图"
    print(f"\n查询: {query}")
    print("过滤条件: 仅CAD图纸\n")

    results = await retriever.search(
        query=query,
        top_k=5,
        image_type="cad_drawing"
    )

    print(retriever.format_results(results))


async def example_architecture_search():
    """示例3: 架构图检索"""
    print("\n" + "=" * 60)
    print("示例3: 架构图检索")
    print("=" * 60)

    retriever = HybridRetriever()

    # 查询架构图
    query = "查找微服务架构相关的系统设计图"
    print(f"\n查询: {query}\n")

    results = await retriever.search(
        query=query,
        top_k=5,
        image_type="architecture_diagram"
    )

    print(retriever.format_results(results))


async def example_complex_query():
    """示例4: 复杂查询"""
    print("\n" + "=" * 60)
    print("示例4: 复杂查询（多条件）")
    print("=" * 60)

    retriever = HybridRetriever()

    # 复杂查询
    query = """
    查找符合以下条件的图纸:
    1. 零件材料为不锈钢或铝合金
    2. 包含尺寸公差标注
    3. 有表面处理要求
    """
    print(f"\n查询: {query}\n")

    results = await retriever.search(
        query=query,
        top_k=10,
        min_score=0.75  # 高相似度阈值
    )

    # 详细输出
    if results:
        print(f"共找到 {len(results)} 条高相关度结果:\n")
        for result in results:
            print(f"【第 {result.rank} 名】 相似度: {result.score:.3f}")
            print(f"文件: {Path(result.image_path).name}")
            print(f"类型: {result.metadata.get('image_type')}")

            # 输出结构化数据
            structured = result.metadata.get("structured_data", {})
            if isinstance(structured, dict):
                if "material" in structured:
                    print(f"材料: {structured['material']}")
                if "dimensions" in structured:
                    print(f"尺寸信息: {structured['dimensions'][:3]}")
                if "surface_treatment" in structured:
                    print(f"表面处理: {structured['surface_treatment']}")

            print(f"描述: {result.description[:150]}...")
            print("-" * 60)
    else:
        print("未找到符合条件的结果")


async def example_batch_queries():
    """示例5: 批量查询"""
    print("\n" + "=" * 60)
    print("示例5: 批量查询")
    print("=" * 60)

    retriever = HybridRetriever()

    queries = [
        "齿轮传动系统",
        "液压控制回路",
        "电路原理图",
        "分布式系统架构"
    ]

    print(f"\n批量查询 {len(queries)} 个问题:\n")

    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")

        results = await retriever.search(query, top_k=3)

        if results:
            print(f"   找到 {len(results)} 条结果")
            for result in results[:2]:
                print(f"   - {Path(result.image_path).name} (得分: {result.score:.3f})")
        else:
            print("   未找到结果")

        print()


async def interactive_search():
    """示例6: 交互式检索"""
    print("\n" + "=" * 60)
    print("示例6: 交互式检索")
    print("=" * 60)

    retriever = HybridRetriever()

    print("\n可用的图像类型:")
    for key, value in IMAGE_TYPES.items():
        print(f"  - {key}: {value}")

    print("\n输入查询（输入'exit'退出）:")

    while True:
        try:
            query = input("\n> ").strip()

            if query.lower() in ["exit", "quit", "q"]:
                print("再见!")
                break

            if not query:
                continue

            # 执行查询
            results = await retriever.search(query, top_k=5)

            if results:
                print(f"\n找到 {len(results)} 条结果:")
                for result in results:
                    print(f"\n  [{result.rank}] {Path(result.image_path).name}")
                    print(f"      相似度: {result.score:.3f}")
                    print(f"      类型: {result.metadata.get('image_type')}")
                    print(f"      {result.description[:100]}...")
            else:
                print("\n未找到相关结果")

        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")


async def main():
    """主函数 - 选择运行哪个示例"""

    # 运行所有示例
    # await example_basic_search()
    # await example_filtered_search()
    # await example_architecture_search()
    # await example_complex_query()
    # await example_batch_queries()

    # 交互式检索（推荐）
    await interactive_search()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
