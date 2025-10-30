"""
多模态 RAG 上传功能测试示例
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def upload_file(file_path: str, image_type: str = None):
    """
    上传文件到服务器

    Args:
        file_path: 文件路径
        image_type: 可选的图片类型（cad, floor_plan, architecture, technical_doc）
    """
    url = f"{BASE_URL}/upload"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {}

        if image_type:
            data['image_type'] = image_type

        response = requests.post(url, files=files, data=data)

    return response.json()


def example_1_auto_detect():
    """示例1: 自动检测图片类型"""
    print("\n" + "="*60)
    print("示例1: 上传图片 - 自动检测类型")
    print("="*60)

    result = upload_file("your_image.png")

    print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print(f"\n检测到的类型: {result.get('detectedImageType')}")


def example_2_cad_manual():
    """示例2: 手动指定为CAD图纸"""
    print("\n" + "="*60)
    print("示例2: 上传CAD图纸 - 手动指定类型")
    print("="*60)

    result = upload_file("cad_drawing.dwg", image_type="cad")

    print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")


def example_3_floor_plan():
    """示例3: 上传平面布置图"""
    print("\n" + "="*60)
    print("示例3: 上传平面布置图")
    print("="*60)

    result = upload_file("floor_plan.png", image_type="floor_plan")

    print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print("\n提取的信息示例:")
    print("- 房间布局")
    print("- 尺寸标注")
    print("- 家具位置")
    print("- 动线分析")


def example_4_architecture():
    """示例4: 上传架构图"""
    print("\n" + "="*60)
    print("示例4: 上传架构图")
    print("="*60)

    result = upload_file("architecture.jpg", image_type="architecture")

    print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print("\n提取的信息示例:")
    print("- 系统架构")
    print("- 组件关系")
    print("- 数据流向")
    print("- 技术栈")


def example_5_technical_doc():
    """示例5: 上传技术文档"""
    print("\n" + "="*60)
    print("示例5: 上传技术文档")
    print("="*60)

    result = upload_file("inspection_report.jpg", image_type="technical_doc")

    print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print("\n提取的信息示例:")
    print("- 参数数据")
    print("- 表格内容")
    print("- 工艺流程")
    print("- 检验项目")


def example_6_pdf_with_images():
    """示例6: 上传包含图片的PDF"""
    print("\n" + "="*60)
    print("示例6: 上传包含图片的PDF")
    print("="*60)

    result = upload_file("technical_manual.pdf")

    print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print("\n处理流程:")
    print("1. 提取PDF文本")
    print("2. 识别图片页面")
    print("3. 智能检测图片类型")
    print("4. VLM分析图片内容")
    print("5. 整合所有内容到向量库")


def search_example():
    """示例7: 搜索已上传的内容"""
    print("\n" + "="*60)
    print("示例7: 搜索已上传的内容")
    print("="*60)

    url = f"{BASE_URL}/search"
    payload = {
        "query": "客厅的面积是多少？",
        "model": "gpt-4o",
        "strategy": "hybrid",
        "topK": 5
    }

    response = requests.post(url, json=payload)
    result = response.json()

    print(f"搜索结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print(f"\n找到 {result.get('totalCount')} 个相关结果")


def batch_upload_example():
    """示例8: 批量上传不同类型的文件"""
    print("\n" + "="*60)
    print("示例8: 批量上传不同类型的文件")
    print("="*60)

    files_to_upload = [
        ("cad_1.dwg", "cad"),
        ("floor_plan_1.png", "floor_plan"),
        ("architecture_1.jpg", "architecture"),
        ("tech_doc_1.pdf", None),  # 自动检测
    ]

    results = []
    for file_path, img_type in files_to_upload:
        print(f"\n上传: {file_path}")
        try:
            result = upload_file(file_path, img_type)
            results.append(result)
            print(f"  ✓ 成功: {result.get('fileId')}")
            if result.get('detectedImageType'):
                print(f"  检测类型: {result.get('detectedImageType')}")
        except Exception as e:
            print(f"  ✗ 失败: {e}")

    print(f"\n批量上传完成: {len(results)}/{len(files_to_upload)} 成功")


def main():
    """主函数 - 运行所有示例"""
    print("\n" + "="*80)
    print("多模态 RAG 上传功能测试示例")
    print("="*80)
    print("\n注意: 请确保后端服务已启动 (python main_service.py)")
    print(f"服务地址: {BASE_URL}")

    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ 后端服务运行正常\n")
        else:
            print("⚠️ 后端服务异常\n")
            return
    except Exception as e:
        print(f"✗ 无法连接到后端服务: {e}")
        print("请先启动后端服务：python main_service.py\n")
        return

    # 显示示例（不实际执行，因为文件可能不存在）
    print("\n支持的图片类型：")
    print("  - cad: CAD工程制造图纸")
    print("  - floor_plan: 室内平面布置图")
    print("  - architecture: 架构图/流程图")
    print("  - technical_doc: 技术文档/工艺文件")

    print("\n" + "="*80)
    print("使用方法:")
    print("="*80)
    print("\n1. 自动检测类型:")
    print("   result = upload_file('your_image.png')")

    print("\n2. 手动指定类型:")
    print("   result = upload_file('floor_plan.png', image_type='floor_plan')")

    print("\n3. 查看响应:")
    print("   print(result['detectedImageType'])  # 检测到的类型")
    print("   print(result['fileId'])             # 文件ID")
    print("   print(result['message'])            # 处理消息")

    print("\n" + "="*80)
    print("完整示例代码:")
    print("="*80)
    print("""
# 导入模块
from test_upload_examples import upload_file

# 上传文件
result = upload_file('floor_plan.png', image_type='floor_plan')

# 查看结果
if result['success']:
    print(f"✓ 上传成功")
    print(f"  文件ID: {result['fileId']}")
    print(f"  检测类型: {result['detectedImageType']}")
    print(f"  消息: {result['message']}")
else:
    print(f"✗ 上传失败: {result['message']}")
    """)

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
