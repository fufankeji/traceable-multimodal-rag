import requests
import json
import os   
from pathlib import Path

def chunk_markdown_api_from_json(json_file_path, api_url="http://192.168.110.131:8001/chunk"):
    """
    从JSON文件中读取markdown内容并发送到API进行处理
    
    :param json_file_path: JSON文件路径
    :param api_url: API地址
    :return: API响应
    """
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 从JSON中提取markdown内容
    markdown_text = data.get('data', {}).get('markdown', '')
    
    # 提取完整的data字段作为metadata（包含images等所有字段）
    original_data = data.get('data', {}).copy()
    # 移除markdown字段，因为它会作为单独参数传递
    original_data.pop('markdown', None)
    
    # 构造请求数据
    request_data = {
        "markdown": markdown_text,
        "filename": data.get('filename', 'unknown'),
        "config": {
            "method": "header_recursive",
            "chunk_size": 1500,
            "chunk_overlap": 200,
            "merge_tolerance": 0.2,
            "max_page_span": 3,
            "bridge_span": 150,
            "add_bridges": True
        },
        "metadata": original_data  # 传递完整的原始data（除了markdown）
    }
    
    # 发送POST请求到API
    response = requests.post(api_url, json=request_data)
    
    # 返回API响应
    return response.json()

def main():
    # JSON文件路径
    json_file_path = "/home/data/nongwa/workspace/Information-Extraction/unified/output/test/accurate_result.json"
    
    # API地址
    api_url = "http://192.168.110.131:8001/chunk"
    
    # 调用API
    result = chunk_markdown_api_from_json(json_file_path, api_url)
    save_path = os.path.join(os.path.dirname(__file__), 'output',Path(json_file_path).parent.name, os.path.basename(json_file_path).replace('.json', '_chunk.json'))
    if not os.path.exists(os.path.dirname(save_path)):
        os.makedirs(os.path.dirname(save_path))
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"已将结果保存到 {save_path}")

    # 打印结果
    # print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()