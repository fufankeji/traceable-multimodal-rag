"""
测试脚本 - 简化版VLM图像分析器

使用示例：
python test_vlm_analyzer.py
"""

import asyncio
from pathlib import Path
from simple_vlm_analyzer import (
    SimpleVLMAnalyzer,
    ImageType,
    analyze_cad_drawing,
    analyze_architecture_diagram,
    analyze_technical_document
)


async def test_cad_analysis():
    """测试CAD图纸分析"""
    print("\n" + "🔧"*30)
    print("测试场景1: CAD工程制造图纸分析")
    print("🔧"*30)

    # 创建分析器
    analyzer = SimpleVLMAnalyzer()

    # 示例1: 本地CAD图纸文件
    image_path = "/home/MuyuWorkSpace/01_TrafficProject/pc_multimodal_rag/backend/data/house.png"
    question = "这张图纸的主要尺寸是多少？材料是什么？"

    # 示例2: 使用便捷函数
    # result = await analyze_cad_drawing(
    #     image_source=image_path,
    #     question=question
    # )

    # analyzer.print_result(result)

    print("\n💡 提示: 请将上面的注释代码取消注释，并替换为实际的CAD图纸路径")
    print("   支持的问题示例:")
    print("   - 这张图纸的主要尺寸是多少？")
    print("   - 图纸中标注的公差范围是什么？")
    print("   - 这个零件使用什么材料？")
    print("   - 图纸包含哪些视图？")


async def test_architecture_analysis():
    """测试架构图分析"""
    print("\n" + "📐"*30)
    print("测试场景2: 研发架构图/流程图分析")
    print("📐"*30)

    analyzer = SimpleVLMAnalyzer()

    # 示例1: 系统架构图
    # image_path = "/path/to/your/architecture_diagram.png"
    # question = "请说明这个系统的整体架构和各模块之间的调用关系"

    # 示例2: 流程图
    # image_path = "/path/to/your/flowchart.png"
    # question = "这个业务流程有哪些关键步骤？"

    # result = await analyzer.analyze_image(
    #     image_source=image_path,
    #     question=question,
    #     image_type=ImageType.ARCHITECTURE
    # )

    # analyzer.print_result(result)

    print("\n💡 提示: 请将上面的注释代码取消注释，并替换为实际的架构图路径")
    print("   支持的问题示例:")
    print("   - 这个系统分为哪几层？")
    print("   - 各个模块之间是如何通信的？")
    print("   - 数据流向是怎样的？")
    print("   - 使用了哪些技术栈？")


async def test_technical_doc_analysis():
    """测试技术文档分析"""
    print("\n" + "📄"*30)
    print("测试场景3: 工业技术档案/工艺文件分析")
    print("📄"*30)

    analyzer = SimpleVLMAnalyzer()

    # 示例1: 工艺卡片
    # image_path = "/path/to/your/process_card.png"
    # question = "这份工艺卡片的加工步骤是什么？有哪些质量要求？"

    # 示例2: 检验报告
    # image_path = "/path/to/your/inspection_report.png"
    # question = "检验报告中的关键参数和检验结果是什么？"

    # result = await analyze_technical_document(
    #     image_source=image_path,
    #     question=question
    # )

    # analyzer.print_result(result)

    print("\n💡 提示: 请将上面的注释代码取消注释，并替换为实际的文档图片路径")
    print("   支持的问题示例:")
    print("   - 这份文档的版本号是多少？")
    print("   - 工艺流程包含哪些步骤？")
    print("   - 关键参数和数值是什么？")
    print("   - 表格中记录了哪些数据？")


async def test_with_url():
    """测试从URL加载图片"""
    print("\n" + "🌐"*30)
    print("测试场景4: 从URL加载图片")
    print("🌐"*30)

    analyzer = SimpleVLMAnalyzer()

    # 示例: 从URL加载图片
    # image_url = "https://example.com/your-diagram.png"
    # question = "请分析这张图片的内容"

    # result = await analyzer.analyze_image(
    #     image_source=image_url,
    #     question=question,
    #     image_type=ImageType.ARCHITECTURE  # 根据实际图片类型选择
    # )

    # analyzer.print_result(result)

    print("\n💡 提示: 支持从HTTP/HTTPS URL直接加载图片")
    print("   只需将image_source参数设置为图片的URL即可")


async def demo_complete_workflow():
    """完整工作流演示"""
    print("\n" + "="*60)
    print("🎯 完整工作流演示")
    print("="*60)

    # 如果你有真实的图片文件，可以这样使用：

    # 1. 初始化分析器
    analyzer = SimpleVLMAnalyzer(
        model_url="https://aizex.top/v1",
        api_key="sk-Y4o8DF6Iq2l8OcieaS1gXfgIzFkfymV4oF01ofphYB5FxnFT",
        model_name="gpt-4o"
    )

    # 2. 分析CAD图纸
    # cad_result = await analyzer.analyze_image(
    #     image_source="/path/to/cad_drawing.png",
    #     question="这张图纸的主要尺寸和材料要求是什么？",
    #     image_type=ImageType.CAD
    # )
    # analyzer.print_result(cad_result)

    # 3. 分析架构图
    # arch_result = await analyzer.analyze_image(
    #     image_source="/path/to/architecture.png",
    #     question="请说明系统的整体架构和各模块的作用",
    #     image_type=ImageType.ARCHITECTURE
    # )
    # analyzer.print_result(arch_result)

    # 4. 分析技术文档
    # doc_result = await analyzer.analyze_image(
    #     image_source="/path/to/technical_doc.png",
    #     question="这份文档的关键参数和工艺要求是什么？",
    #     image_type=ImageType.TECHNICAL_DOC
    # )
    # analyzer.print_result(doc_result)

    print("\n✅ 工作流说明:")
    print("   1. 创建 SimpleVLMAnalyzer 实例")
    print("   2. 调用 analyze_image() 方法")
    print("   3. 传入图片路径/URL、用户问题、图像类型")
    print("   4. 获取 AnalysisResult 结果")
    print("   5. 使用 print_result() 打印结果")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 简化版VLM图像分析器 - 测试套件")
    print("="*60)
    print("\n支持三种场景:")
    print("  1. CAD工程制造图纸解读 (结构、尺寸、参数)")
    print("  2. 研发架构图理解 (架构、流程图语义)")
    print("  3. 工业技术档案识别 (工艺文件、设计版本)")
    print("\n支持的图片来源:")
    print("  ✓ 本地文件路径")
    print("  ✓ HTTP/HTTPS URL")
    print("  ✓ PIL Image对象")

    # 运行各项测试
    await test_cad_analysis()
    # await test_architecture_analysis()
    # await test_technical_doc_analysis()
    # await test_with_url()
    # await demo_complete_workflow()

    print("\n" + "="*60)
    print("💡 使用提示")
    print("="*60)
    print("""
1. 修改上面的测试函数，取消注释并替换为实际图片路径
2. 根据图片类型选择合适的 ImageType:
   - ImageType.CAD: CAD工程图纸
   - ImageType.ARCHITECTURE: 架构图/流程图
   - ImageType.TECHNICAL_DOC: 技术文档/工艺文件

3. 自定义配置:
   analyzer = SimpleVLMAnalyzer(
       model_url="your_api_url",
       api_key="your_api_key",
       model_name="your_model_name"
   )

4. 快速使用便捷函数:
   result = await analyze_cad_drawing(image_path, question)
   result = await analyze_architecture_diagram(image_path, question)
   result = await analyze_technical_document(image_path, question)
""")


if __name__ == "__main__":
    asyncio.run(main())
