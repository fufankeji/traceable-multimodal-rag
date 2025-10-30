"""
实际使用示例 - 简化版VLM图像分析器

这个脚本展示了如何实际使用图像分析器
"""

import asyncio
from simple_vlm_analyzer import SimpleVLMAnalyzer, ImageType


async def example_1_analyze_local_image():
    """示例1: 分析本地图片文件"""
    print("\n" + "="*60)
    print("示例1: 分析本地CAD图纸")
    print("="*60)

    # 创建分析器实例
    analyzer = SimpleVLMAnalyzer()

    # 你的图片路径（请替换为实际路径）
    image_path = "/home/MuyuWorkSpace/01_TrafficProject/pc_multimodal_rag/backend/data/house.png"

    # 用户问题
    # question = "这张CAD图纸的主要尺寸是多少？使用的材料是什么？"
    question = "请帮我检查这图平面图中有没有尺寸标注错误（不一致 /标注重叠）？"
    try:
        # 执行分析
        result = await analyzer.analyze_image(
            image_source=image_path,
            question=question,
            image_type=ImageType.CAD
        )

        # 打印结果
        analyzer.print_result(result)

        # 你也可以直接访问结果的各个字段
        print(f"\n直接访问结果:")
        print(f"答案: {result.answer}")
        print(f"提取信息: {result.extracted_info}")
        print(f"耗时: {result.time_cost:.2f}秒")

    except FileNotFoundError:
        print(f"⚠️ 文件不存在: {image_path}")
        print("💡 请将 image_path 替换为实际的图片路径")
    except Exception as e:
        print(f"❌ 分析失败: {e}")


async def example_2_analyze_architecture():
    """示例2: 分析架构图"""
    print("\n" + "="*60)
    print("示例2: 分析系统架构图")
    print("="*60)

    analyzer = SimpleVLMAnalyzer()

    # 架构图路径
    image_path = "/path/to/your/architecture_diagram.png"

    # 用户问题
    question = "这个系统分为几层？各层的主要组件有哪些？数据流向是怎样的？"

    try:
        result = await analyzer.analyze_image(
            image_source=image_path,
            question=question,
            image_type=ImageType.ARCHITECTURE
        )

        analyzer.print_result(result)

        # 获取提取的架构信息
        arch_info = result.extracted_info
        if 'main_components' in arch_info:
            print("\n主要组件:")
            for component in arch_info['main_components']:
                print(f"  - {component}")

    except FileNotFoundError:
        print(f"⚠️ 文件不存在: {image_path}")
        print("💡 请将 image_path 替换为实际的图片路径")
    except Exception as e:
        print(f"❌ 分析失败: {e}")


async def example_3_analyze_from_url():
    """示例3: 从URL加载并分析图片"""
    print("\n" + "="*60)
    print("示例3: 从URL加载图片")
    print("="*60)

    analyzer = SimpleVLMAnalyzer()

    # 图片URL（请替换为实际URL）
    image_url = "https://example.com/technical_document.jpg"

    question = "这份技术文档的版本号和主要内容是什么？"

    try:
        result = await analyzer.analyze_image(
            image_source=image_url,
            question=question,
            image_type=ImageType.TECHNICAL_DOC
        )

        analyzer.print_result(result)

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        print("💡 请确保URL可访问，并替换为实际的图片URL")


async def example_4_batch_analysis():
    """示例4: 批量分析多张图片"""
    print("\n" + "="*60)
    print("示例4: 批量分析多张CAD图纸")
    print("="*60)

    analyzer = SimpleVLMAnalyzer()

    # 多个图纸文件
    cad_drawings = [
        {"path": "/path/to/drawing1.jpg", "question": "这个零件的主要尺寸是多少？"},
        {"path": "/path/to/drawing2.jpg", "question": "这个零件使用什么材料？"},
        {"path": "/path/to/drawing3.jpg", "question": "这个零件的公差要求是什么？"},
    ]

    results = []

    for idx, drawing in enumerate(cad_drawings, 1):
        print(f"\n>>> 正在分析第 {idx}/{len(cad_drawings)} 张图纸...")

        try:
            result = await analyzer.analyze_image(
                image_source=drawing["path"],
                question=drawing["question"],
                image_type=ImageType.CAD
            )

            results.append(result)
            print(f"✓ 第 {idx} 张分析完成")

            # 可以在这里做短暂延迟，避免API限流
            await asyncio.sleep(1)

        except FileNotFoundError:
            print(f"⚠️ 文件不存在: {drawing['path']}")
        except Exception as e:
            print(f"❌ 分析失败: {e}")

    # 汇总统计
    print("\n" + "="*60)
    print(f"批量分析完成: 成功 {len(results)}/{len(cad_drawings)} 张")
    total_tokens = sum(r.token_usage.get('total_tokens', 0) for r in results)
    total_time = sum(r.time_cost for r in results)
    print(f"总Token消耗: {total_tokens}")
    print(f"总耗时: {total_time:.2f}秒")
    print("="*60)


async def example_5_custom_config():
    """示例5: 使用自定义配置"""
    print("\n" + "="*60)
    print("示例5: 使用自定义API配置")
    print("="*60)

    # 自定义模型配置
    analyzer = SimpleVLMAnalyzer(
        model_url="https://your-api-endpoint.com/v1",  # 你的API地址
        api_key="your-api-key",  # 你的API密钥
        model_name="gpt-4o"  # 模型名称
    )

    # 也支持通义千问
    # analyzer = SimpleVLMAnalyzer(
    #     model_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    #     api_key="your-qwen-api-key",
    #     model_name="qwen-vl-plus"
    # )

    image_path = "/path/to/your/image.jpg"
    question = "请分析这张图片"

    try:
        result = await analyzer.analyze_image(
            image_source=image_path,
            question=question,
            image_type=ImageType.CAD
        )

        analyzer.print_result(result)

    except Exception as e:
        print(f"❌ 分析失败: {e}")


async def example_6_use_convenience_functions():
    """示例6: 使用便捷函数"""
    print("\n" + "="*60)
    print("示例6: 使用便捷函数快速调用")
    print("="*60)

    from simple_vlm_analyzer import (
        analyze_cad_drawing,
        analyze_architecture_diagram,
        analyze_technical_document
    )

    # 方式1: 分析CAD图纸
    # result1 = await analyze_cad_drawing(
    #     image_source="/path/to/cad.jpg",
    #     question="主要尺寸是多少？"
    # )

    # 方式2: 分析架构图
    # result2 = await analyze_architecture_diagram(
    #     image_source="/path/to/arch.png",
    #     question="系统架构是怎样的？"
    # )

    # 方式3: 分析技术文档
    # result3 = await analyze_technical_document(
    #     image_source="/path/to/doc.jpg",
    #     question="关键参数是什么？"
    # )

    print("💡 便捷函数已封装好所有配置，可以一行代码完成分析")
    print("   支持的函数:")
    print("   - analyze_cad_drawing()")
    print("   - analyze_architecture_diagram()")
    print("   - analyze_technical_document()")


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "🎯"*30)
    print("简化版VLM图像分析器 - 实际使用示例")
    print("🎯"*30)

    # 选择要运行的示例（取消注释你想运行的示例）

    await example_1_analyze_local_image()
    # await example_2_analyze_architecture()
    # await example_3_analyze_from_url()
    # await example_4_batch_analysis()
    # await example_5_custom_config()
    # await example_6_use_convenience_functions()

    print("\n" + "="*60)
    print("✅ 示例运行完成")
    print("="*60)
    print("\n💡 使用建议:")
    print("   1. 将示例中的图片路径替换为实际路径")
    print("   2. 根据图片类型选择合适的 ImageType")
    print("   3. 根据需要调整用户问题")
    print("   4. 可以自定义API配置（model_url, api_key, model_name）")
    print("\n📚 三种图像类型:")
    print("   - ImageType.CAD: CAD工程制造图纸")
    print("   - ImageType.ARCHITECTURE: 研发架构图/流程图")
    print("   - ImageType.TECHNICAL_DOC: 工业技术档案/工艺文件")


if __name__ == "__main__":
    asyncio.run(main())
