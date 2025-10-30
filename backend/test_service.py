"""
测试多模态 RAG 服务
"""
import asyncio
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_health_check():
    """测试健康检查"""
    print("\n" + "="*60)
    print("🏥 测试健康检查")
    print("="*60)

    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

    assert response.status_code == 200
    print("✓ 健康检查通过")


def test_upload(file_path: str):
    """测试文件上传"""
    print("\n" + "="*60)
    print(f"📤 测试文件上传: {file_path}")
    print("="*60)

    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/upload", files=files)

    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {result}")

    assert response.status_code == 200
    assert result['success'] == True

    print(f"✓ 文件上传成功")
    print(f"  文件ID: {result['fileId']}")
    print(f"  消息: {result['message']}")

    return result['fileId']


def test_search(query: str):
    """测试搜索"""
    print("\n" + "="*60)
    print(f"🔍 测试搜索: {query}")
    print("="*60)

    payload = {
        "query": query,
        "model": "gpt-4o",
        "strategy": "hybrid",
        "topK": 5
    }

    response = requests.post(f"{BASE_URL}/search", json=payload)
    print(f"状态码: {response.status_code}")
    result = response.json()

    print(f"\n找到 {result['totalCount']} 个结果")
    print(f"查询耗时: {result['queryTime']} ms")

    for idx, item in enumerate(result['results'], 1):
        print(f"\n结果 {idx}:")
        print(f"  文件: {item['fileName']}")
        print(f"  类型: {item['fileType']}")
        print(f"  相似度: {item['similarity']:.3f}")
        print(f"  页码: {item['page']}")
        print(f"  片段: {item['snippet'][:100]}...")

    assert response.status_code == 200
    assert result['totalCount'] > 0

    print("\n✓ 搜索测试通过")
    return result['results'][0]['id'] if result['results'] else None


def test_follow_up_question(document_id: str, question: str):
    """测试追问"""
    print("\n" + "="*60)
    print(f"💬 测试追问")
    print(f"  文档ID: {document_id}")
    print(f"  问题: {question}")
    print("="*60)

    payload = {
        "documentId": document_id,
        "question": question,
        "model": "gpt-4o"
    }

    response = requests.post(f"{BASE_URL}/question", json=payload)
    print(f"状态码: {response.status_code}")
    result = response.json()

    print(f"\n回答: {result['answer']}")
    print(f"引用: {result['citations']}")
    print(f"置信度: {result['confidence']}")

    assert response.status_code == 200

    print("\n✓ 追问测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 开始测试多模态 RAG 服务")
    print("="*60)

    try:
        # 1. 健康检查
        test_health_check()

        # 2. 上传测试文件（需要提供一个测试PDF）
        test_pdf_path = "/home/data/nongwa/workspace/data/test.pdf"  # 修改为实际路径

        if Path(test_pdf_path).exists():
            file_id = test_upload(test_pdf_path)

            # 等待索引完成
            print("\n⏳ 等待 2 秒让索引完成...")
            import time
            time.sleep(2)

            # 3. 搜索测试
            doc_id = test_search("这个文档的主要内容是什么？")

            # 4. 追问测试
            if doc_id:
                test_follow_up_question(doc_id, "请详细说明其中的关键技术点")

        else:
            print(f"\n⚠️  测试文件不存在: {test_pdf_path}")
            print("跳过上传和搜索测试")

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行所有测试
    run_all_tests()

    # 或单独运行特定测试
    # test_health_check()
    # test_search("电机支架")
