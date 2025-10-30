import asyncio
import aiohttp
import base64
from pathlib import Path
from PIL import Image
import io

# ============ 配置 ============
API_KEY = "sk-Y4o8DF6Iq2l8OcieaS1gXfgIzFkfymV4oF01ofphYB5FxnFT"
MODEL_NAME = "gpt-4o"
MODEL_URL = "https://aizex.top/v1"

# 通义千问配置（备选）
# API_KEY = "sk-0fb27bf3a9a448fa9a6f02bd70e37cd8"
# MODEL_NAME = "qwen-vl-plus"
# MODEL_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def image_to_base64(image_path: str, max_size: int = 2000) -> str:
    """将本地图片转为base64"""
    img = Image.open(image_path)
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


async def ask_image_gpt(image_input: str, question: str, is_url: bool = True) -> str:
    """
    GPT系列图片问答
    
    Args:
        image_input: 图片URL或本地路径
        question: 问题
        is_url: True表示image_input是URL，False表示是本地路径
    """
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=API_KEY, base_url=MODEL_URL)
    
    # 构建图片内容
    if is_url:
        image_content = {"type": "image_url", "image_url": {"url": image_input}}
    else:
        base64_image = image_to_base64(image_input)
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        }
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                image_content
            ]
        }
    ]
    
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=1000,
        temperature=0.7
    )
    
    answer = response.choices[0].message.content
    
    # 打印token使用情况
    if response.usage:
        print(f"Token使用: 输入={response.usage.prompt_tokens}, "
              f"输出={response.usage.completion_tokens}, "
              f"总计={response.usage.total_tokens}")
    
    return answer


async def ask_image_qwen(image_input: str, question: str, is_url: bool = True) -> str:
    """
    通义千问图片问答
    
    Args:
        image_input: 图片URL或本地路径
        question: 问题
        is_url: True表示image_input是URL，False表示是本地路径
    """
    # 构建图片内容
    if is_url:
        image_content = {
            "type": "image_url",
            "image_url": {"url": image_input}
        }
    else:
        base64_image = image_to_base64(image_input)
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    image_content
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    url = MODEL_URL.rstrip('/') + '/chat/completions'
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API错误 {response.status}: {error_text}")
            
            result = await response.json()
            answer = result['choices'][0]['message']['content']
            
            # 打印token使用情况
            if 'usage' in result:
                usage = result['usage']
                print(f"Token使用: 输入={usage.get('prompt_tokens', 0)}, "
                      f"输出={usage.get('completion_tokens', 0)}, "
                      f"总计={usage.get('total_tokens', 0)}")
            
            return answer


async def ask_image(image_input: str, question: str, is_url: bool = True, 
                   api_type: str = "gpt") -> str:
    """
    通用图片问答接口
    
    Args:
        image_input: 图片URL或本地路径
        question: 问题
        is_url: True表示URL，False表示本地路径
        api_type: "gpt" 或 "qwen"
    
    Returns:
        模型的回答
    """
    if api_type == "gpt":
        return await ask_image_gpt(image_input, question, is_url)
    elif api_type == "qwen":
        return await ask_image_qwen(image_input, question, is_url)
    else:
        raise ValueError(f"不支持的API类型: {api_type}")


# ============ 使用示例 ============

async def example_url():
    """示例1: 使用图片URL"""
    print("=" * 60)
    print("示例1: 图片URL问答")
    print("=" * 60)
    
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    question = "这张图片里有什么？请详细描述。"
    
    answer = await ask_image(image_url, question, is_url=True, api_type="gpt")
    
    print(f"\n问题: {question}")
    print(f"\n回答:\n{answer}\n")


async def example_local_file():
    """示例2: 使用本地图片"""
    print("=" * 60)
    print("示例2: 本地图片问答")
    print("=" * 60)
    
    # 替换为你的本地图片路径
    image_path = "/home/MuyuWorkSpace/01_TrafficProject/pc_multimodal_rag/backend/data/test_image.jpg"
    question = "图片中有哪些元素？"
    
    if not Path(image_path).exists():
        print(f"⚠️  图片不存在: {image_path}")
        print("请修改 image_path 为实际的图片路径")
        return
    
    answer = await ask_image(image_path, question, is_url=False, api_type="gpt")
    
    print(f"\n问题: {question}")
    print(f"\n回答:\n{answer}\n")


async def example_multiple_questions():
    """示例3: 对同一图片问多个问题"""
    print("=" * 60)
    print("示例3: 多轮问答")
    print("=" * 60)
    
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    
    questions = [
        "这是什么类型的景观？",
        "天气看起来怎么样？",
        "图片的主要颜色是什么？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n问题{i}: {question}")
        answer = await ask_image(image_url, question, is_url=True, api_type="gpt")
        print(f"回答: {answer}\n")
        await asyncio.sleep(1)  # 避免请求过快


async def main():
    """主函数 - 运行所有示例"""
    # 示例1: URL图片
    await example_url()
    
    # 示例2: 本地图片（如果存在）
    # await example_local_file()
    
    # 示例3: 多轮问答
    # await example_multiple_questions()


if __name__ == "__main__":
    # 快速测试：直接问一个问题
    async def quick_test():
        image_url = "https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202510141027702.png"
        answer = await ask_image(image_url, "描述这张图片", is_url=True, api_type="gpt")
        print(f"回答: {answer}")
    
    asyncio.run(quick_test())
    
    # 运行完整示例
    # asyncio.run(main())

