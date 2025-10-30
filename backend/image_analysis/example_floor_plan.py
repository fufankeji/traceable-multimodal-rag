"""
室内平面图分析示例 - 展示各种场景下的问答
"""
import asyncio
from pathlib import Path
from simple_vlm_analyzer import SimpleVLMAnalyzer, ImageType, analyze_floor_plan


async def example_1_room_count():
    """示例1：询问房间数量"""
    print("\n" + "="*80)
    print("示例1：询问房间数量")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="/home/MuyuWorkSpace/01_TrafficProject/pc_multimodal_rag/backend/data/house.png",  # 替换为你的图片路径
        question="这张平面图有几个房间？分别是什么房间？"
    )

    print(f"\n【回答】{result.answer}")
    print(f"\n【提取的房间信息】")
    for room in result.extracted_info.get('rooms', []):
        print(f"  - {room['name']} ({room.get('position', '未知位置')})")


async def example_2_dimensions():
    """示例2：询问尺寸和面积"""
    print("\n" + "="*80)
    print("示例2：询问尺寸和面积")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question="客厅的面积是多少？整体建筑面积大约是多少？"
    )

    print(f"\n【回答】{result.answer}")
    if 'total_dimensions' in result.extracted_info:
        total = result.extracted_info['total_dimensions']
        print(f"\n【整体尺寸】{total.get('length')}m × {total.get('width')}m")
        print(f"【总面积】{total.get('total_area')} ㎡")


async def example_3_circulation():
    """示例3：询问动线"""
    print("\n" + "="*80)
    print("示例3：询问动线")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question="从主入口到卧室的路径是什么？动线设计合理吗？"
    )

    print(f"\n【回答】{result.answer}")
    if 'circulation' in result.extracted_info:
        circ = result.extracted_info['circulation']
        print(f"\n【主要动线】{circ.get('main_path', '未识别')}")
        print(f"【布局类型】{circ.get('layout_type', '未识别')}")


async def example_4_furniture():
    """示例4：询问家具布局"""
    print("\n" + "="*80)
    print("示例4：询问家具布局")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question="客厅有哪些家具？摆放位置是否合理？"
    )

    print(f"\n【回答】{result.answer}")
    for room in result.extracted_info.get('rooms', []):
        if room['name'] == '客厅':
            print(f"\n【客厅家具】{', '.join(room.get('furniture', []))}")


async def example_5_annotation_interpretation():
    """示例5：询问标注含义"""
    print("\n" + "="*80)
    print("示例5：询问标注含义")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question="图中标注的 '22720'、'8120' 这些数字是什么意思？虚线表示什么？"
    )

    print(f"\n【回答】{result.answer}")
    if 'annotations' in result.extracted_info:
        print(f"\n【标注解析】")
        for anno in result.extracted_info['annotations'][:5]:  # 显示前5个
            print(f"  - {anno.get('value')}: {anno.get('description')}")


async def example_6_design_evaluation():
    """示例6：设计评估"""
    print("\n" + "="*80)
    print("示例6：设计评估")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question="这个平面图的布局有什么优点和不足？有没有优化建议？"
    )

    print(f"\n【回答】{result.answer}")
    if 'design_notes' in result.extracted_info:
        print(f"\n【设计要点】")
        for note in result.extracted_info['design_notes']:
            print(f"  • {note}")


async def example_7_comparison():
    """示例7：条件检索"""
    print("\n" + "="*80)
    print("示例7：条件检索")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question="哪些房间的面积超过15平方米？哪些房间靠近窗户？"
    )

    print(f"\n【回答】{result.answer}")


async def example_8_structured_output():
    """示例8：结构化输出（用于数据库存储）"""
    print("\n" + "="*80)
    print("示例8：结构化输出")
    print("="*80)

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question="请提取这张平面图的完整信息，包括所有房间、尺寸、连通关系等，用于数据库存储。"
    )

    import json
    print(f"\n【结构化数据】")
    print(json.dumps(result.extracted_info, ensure_ascii=False, indent=2))

    # 保存到文件
    output_path = Path(__file__).parent / "floor_plan_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n✓ 数据已保存到: {output_path}")


async def example_9_interactive_qa():
    """示例9：交互式问答（模拟多轮对话）"""
    print("\n" + "="*80)
    print("示例9：交互式问答")
    print("="*80)

    image_path = "path/to/floor_plan.jpg"

    questions = [
        "这张图有几个卧室？",
        "主卧在哪个位置？",
        "主卧有独立卫生间吗？",
        "主卧的面积是多少？"
    ]

    analyzer = SimpleVLMAnalyzer()

    for i, question in enumerate(questions, 1):
        print(f"\n【问题{i}】{question}")
        result = await analyzer.analyze_image(
            image_source=image_path,
            question=question,
            image_type=ImageType.FLOOR_PLAN
        )
        print(f"【回答】{result.answer}")


async def example_10_batch_questions():
    """示例10：批量问题（一次性问多个问题）"""
    print("\n" + "="*80)
    print("示例10：批量问题")
    print("="*80)

    batch_question = """
请回答以下问题：
1. 这张平面图有多少个房间？
2. 整体建筑面积是多少？
3. 客厅和餐厅是开放式还是分隔式？
4. 有几个卫生间？分别在哪里？
5. 主卧是否带独立卫生间？
6. 从主入口到各个卧室的路径是什么？
"""

    result = await analyze_floor_plan(
        image_source="path/to/floor_plan.jpg",
        question=batch_question
    )

    print(f"\n【回答】")
    print(result.answer)


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              室内平面图 VLM 分析 - 场景示例                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

本脚本展示了针对室内平面图的各种问答场景：
  1. 房间数量识别
  2. 尺寸和面积查询
  3. 动线分析
  4. 家具布局
  5. 标注解析
  6. 设计评估
  7. 条件检索
  8. 结构化输出
  9. 交互式问答
  10. 批量问题

使用前请修改 image_source 路径为你的实际图片路径。
""")

    # 选择要运行的示例（取消注释）
    await example_1_room_count()
    # await example_2_dimensions()
    # await example_3_circulation()
    # await example_4_furniture()
    # await example_5_annotation_interpretation()
    # await example_6_design_evaluation()
    # await example_7_comparison()
    # await example_8_structured_output()
    # await example_9_interactive_qa()
    # await example_10_batch_questions()

    print("\n请取消注释上面的示例来运行具体场景。")


if __name__ == "__main__":
    asyncio.run(main())
