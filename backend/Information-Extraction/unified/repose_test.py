import requests
import json
import os
from pathlib import Path
import base64


input_file = '/home/data/nongwa/workspace/data/test.pdf'
output_file = os.path.join(os.path.dirname(__file__), 'output', Path(input_file).stem)
os.makedirs(output_file, exist_ok=True)


# 快速模式
with open(input_file, 'rb') as f:
    response = requests.post(
        'http://192.168.110.131:8005/extract/fast',
        files={'file': (input_file, f, 'application/pdf')}
    )
    fast_result = response.json()
    with open(os.path.join(output_file, 'fast_result.json'), 'w') as f:
        json.dump(fast_result, f, ensure_ascii=False, indent=4)
    fast_text = fast_result['data']['markdown']
    with open(os.path.join(output_file, 'fast_text.md'), 'w') as f:
        f.write(fast_text)
    
    # 保存图片
    images_dir = os.path.join(output_file, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # 遍历所有图片并保存
    for img in fast_result['data'].get('images', []):
        img_filename = img['filename']
        img_base64 = img['base64']
        
        # 解码base64数据并保存图片
        img_data = base64.b64decode(img_base64)
        with open(os.path.join(images_dir, img_filename), 'wb') as f:
            f.write(img_data)

# 精确模式
with open(input_file, 'rb') as f:
    response = requests.post(
        'http://192.168.110.131:8005/extract/accurate',
        files={'file': (input_file, f, 'application/pdf')},
        data={
            'api_key': 'sk-0fb27bf3a9a448fa9a6f02bd70e37cd8',
            'model_name': 'qwen3-vl-plus',#qwen3-vl-30b-a3b-thinking
            'model_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        }
    )
    accurate_result = response.json()
    with open(os.path.join(output_file, 'accurate_result.json'), 'w') as f:
        json.dump(accurate_result, f, ensure_ascii=False, indent=4)
    accurate_text = accurate_result['data']['markdown']
    with open(os.path.join(output_file, 'accurate_text.md'), 'w') as f:
        f.write(accurate_text)

pass