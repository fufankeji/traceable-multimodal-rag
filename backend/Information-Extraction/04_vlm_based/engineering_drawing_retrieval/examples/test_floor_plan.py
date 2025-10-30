"""
测试室内平面图分析 - 使用优化后的 floor_plan 提示词
"""
import asyncio
import json
from pathlib import Path
import sys

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from core.vlm_analyzer import EngineeringDrawingAnalyzer


async def test_floor_plan_analysis(image_path: str):
    """
    测试室内平面图分析

    Args:
        image_path: 平面图路径
    """
    print("=" * 80)
    print("开始测试室内平面图分析")
    print("=" * 80)

    # 检查图片是否存在
    if not Path(image_path).exists():
        print(f"❌ 图片不存在: {image_path}")
        print("请将你的 CAD 平面图放在以下位置，或修改路径:")
        print(f"  {Path(image_path).absolute()}")
        return

    print(f"✅ 找到图片: {image_path}")
    print()

    # 创建分析器
    analyzer = EngineeringDrawingAnalyzer()

    # 方式1: 直接使用 floor_plan 类型
    print("方式1: 使用 floor_plan 类型分析")
    print("-" * 80)
    try:
        result = await analyzer.analyze_image(
            image_path=image_path,
            image_type="floor_plan"
        )

        print("✅ 分析成功!")
        print()
        print("📊 结构化数据:")
        print(json.dumps(result.structured_data, ensure_ascii=False, indent=2))
        print()
        print("📝 描述:")
        print(result.description)
        print()

        # 保存结果
        output_path = Path(__file__).parent / "test_floor_plan_result.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存到: {output_path}")

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)

    # 方式2: 自动识别类型
    print("方式2: 自动识别图像类型")
    print("-" * 80)
    try:
        image_type = await analyzer.classify_image_type(image_path)
        print(f"🔍 识别的图像类型: {image_type}")
        print()

        if image_type == "floor_plan":
            print("✅ 自动识别为室内平面图，继续使用 floor_plan 提示词")
        else:
            print(f"⚠️  识别为其他类型: {image_type}")
            print("   建议手动指定 image_type='floor_plan'")

    except Exception as e:
        print(f"❌ 类型识别失败: {e}")

    print("=" * 80)


async def test_custom_prompt(image_path: str):
    """
    测试自定义提示词（针对特定需求）
    """
    print()
    print("=" * 80)
    print("测试自定义提示词 - 针对性问题")
    print("=" * 80)

    if not Path(image_path).exists():
        print(f"❌ 图片不存在: {image_path}")
        return

    analyzer = EngineeringDrawingAnalyzer()

    # 自定义提示词：只关注房间和面积
    custom_prompt = """
请分析这张室内平面图，只需要回答以下问题：

1. 图中有多少个房间？分别是什么房间？
2. 每个房间的面积是多少（如果能从标注推断）？
3. 整体建筑面积大约是多少？

请以简洁的 JSON 格式输出：
```json
{
    "room_count": 5,
    "rooms": [
        {"name": "客厅", "area": 24.3, "unit": "m²"},
        {"name": "卧室1", "area": 15.8, "unit": "m²"}
    ],
    "total_area": 120.5,
    "summary": "简短总结"
}
```
"""

    try:
        result = await analyzer.analyze_image(
            image_path=image_path,
            image_type="floor_plan",
            custom_prompt=custom_prompt
        )

        print("✅ 自定义分析成功!")
        print()
        print("📊 结果:")
        print(json.dumps(result.structured_data, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"❌ 分析失败: {e}")

    print("=" * 80)


async def main():
    """主函数"""
    # 默认测试图片路径（请根据实际情况修改）
    default_image_path = "/home/MuyuWorkSpace/01_TrafficProject/pc_multimodal_rag/backend/Information-Extraction/04_vlm_based/engineering_drawing_retrieval/examples/floor_plan_sample.jpg"

    # 检查命令行参数
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = default_image_path

    print(f"使用图片路径: {image_path}")
    print()

    # 测试1: 使用优化后的 floor_plan 提示词
    await test_floor_plan_analysis(image_path)

    # 测试2: 使用自定义提示词
    # await test_custom_prompt(image_path)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  室内平面图 VLM 分析测试脚本                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

使用方法:
  1. 默认测试: python test_floor_plan.py
  2. 指定图片: python test_floor_plan.py /path/to/your/floor_plan.jpg

优化内容:
  ✓ 新增 floor_plan 图像类型
  ✓ 专门针对室内平面图的详细提示词
  ✓ 房间识别、尺寸解析、动线分析
  ✓ 家具布局、符号标注、设计评估
  ✓ 结构化 JSON 输出（包含所有关键信息）

""")
    asyncio.run(main())
