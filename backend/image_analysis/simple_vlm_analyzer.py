"""
简化版图像识别模块 - 第一步实现
功能：加载图片 + VLM识别 + 根据用户问题回复

支持三种场景：
1. CAD工程制造图纸解读（结构、尺寸、参数）
2. 研发架构图理解（架构、流程图语义）
3. 工业技术档案识别（工艺文件、设计版本）
"""

import io
import base64
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import aiohttp
import json
import requests
from urllib.parse import urlparse


# ============ 配置部分 ============
DEFAULT_MODEL_URL = "https://ai"
DEFAULT_API_KEY = "sk-Y4o8DF6Iq2l8OcieaSnFT"
DEFAULT_MODEL_NAME = "gpt-4o"


@dataclass
class AnalysisResult:
    """图像分析结果"""
    image_type: str  # cad / architecture / technical_doc
    question: str  # 用户问题
    answer: str  # VLM回答
    extracted_info: Dict[str, Any]  # 提取的结构化信息
    raw_response: str  # 原始响应
    token_usage: Dict[str, int]  # Token使用统计
    time_cost: float  # 耗时


class ImageType:
    """图像类型枚举"""
    CAD = "cad"  # CAD工程制造图纸
    FLOOR_PLAN = "floor_plan"  # 室内平面布置图/建筑平面图
    ARCHITECTURE = "architecture"  # 研发架构图/流程图
    TECHNICAL_DOC = "technical_doc"  # 工业技术档案/工艺文件


class SimpleVLMAnalyzer:
    """简化版VLM图像分析器"""

    # 针对不同图纸类型的提示词模板
    PROMPTS = {
        ImageType.CAD: """你是一位专业的CAD图纸分析专家。请仔细分析这张CAD工程制造图纸。

**用户问题：**
{question}

**分析要求：**
1. **结构识别**：识别图纸中的主要零部件结构、组成部分
2. **尺寸参数**：提取所有关键尺寸标注（长度、宽度、高度、直径、角度等）
3. **技术参数**：识别公差、表面粗糙度、材料要求等技术标注
4. **标题栏信息**：提取图纸编号、名称、比例、材料、设计者等信息
5. **视图说明**：说明包含哪些视图（主视图、俯视图、侧视图、剖视图等）

**回答方式：**
- 首先直接回答用户的问题
- 然后提供相关的详细技术信息
- 如果图纸中有关键数据，请列出来

**输出格式（JSON）：**
{{
    "answer": "直接回答用户问题的内容",
    "extracted_info": {{
        "drawing_title": "图纸名称",
        "drawing_number": "图纸编号",
        "scale": "比例",
        "material": "材料",
        "main_dimensions": {{"长": "xxx", "宽": "xxx", "高": "xxx"}},
        "key_features": ["特征1", "特征2"],
        "technical_requirements": ["要求1", "要求2"],
        "views": ["主视图", "俯视图"]
    }}
}}""",

        ImageType.FLOOR_PLAN: """你是一位专业的建筑/室内平面图分析专家。请仔细分析这张室内平面布置图。

**用户问题：**
{question}

**重要说明：**
- 这是一张室内平面布置图，包含房间、尺寸标注、家具布置、动线等信息
- 图中尺寸单位通常为毫米(mm)或米(m)，请根据数值大小推断
- 请仔细识别所有可见的房间、标注、符号和空间关系

**分析维度（根据用户问题选择性回答）：**

1. **房间/功能区识别**：
   - 识别所有房间名称（客厅、卧室、厨房、卫生间、阳台等）
   - 标注每个房间的位置（左上/右下/中央等方位）
   - 识别特殊功能区（储藏室、玄关、衣帽间等）

2. **尺寸与面积**：
   - 提取图中所有可见尺寸标注
   - 推断单位并统一换算为米(m)
   - 计算房间的长、宽、面积
   - 标注整体平面外墙尺寸

3. **符号与标注**：
   - 解释符号含义（虚线、箭头、红点/红线、轴线等）
   - 识别文字标注（房间编号、面积、备注）
   - 说明墙体类型、门窗位置和开启方向

4. **家具布局**：
   - 列出所有可见家具及其位置
   - 判断空间利用率（拥挤/适中/空旷）
   - 识别家具尺寸

5. **动线与连通性**：
   - 标出主入口、次入口位置
   - 描述主要动线路径（如："入口→玄关→客厅→..."）
   - 列出房间连通关系（哪些房间相连）
   - 判断布局类型（开放式/分隔式）

6. **设计评估**（如果问题涉及）：
   - 动线合理性、是否有绕行或死角
   - 采光/朝向分析
   - 空间优化建议

**回答方式：**
- 首先直接、简洁地回答用户的具体问题
- 然后提供相关的详细信息（如果用户问某个房间，重点描述该房间）
- 如果用户问整体布局，提供全局分析
- 如果涉及尺寸计算，请说明推理过程（如："标注22720mm = 22.72m"）

**输出格式（JSON）：**
{{
    "answer": "直接回答用户问题的核心内容（简洁明了）",
    "extracted_info": {{
        "total_dimensions": {{
            "length": 22.72,
            "width": 12.5,
            "unit": "m",
            "total_area": 284.0
        }},
        "rooms": [
            {{
                "name": "客厅",
                "position": "中央偏右",
                "dimensions": {{"length": 5.79, "width": 4.2, "area": 24.3, "unit": "m"}},
                "furniture": ["沙发", "茶几"],
                "connected_to": ["餐厅", "卧室1"],
                "windows": 2,
                "doors": 1
            }}
        ],
        "annotations": [
            {{"type": "dimension", "value": "22720", "parsed_value": 22.72, "unit": "m", "description": "外墙总长"}}
        ],
        "symbols": [
            {{"type": "door", "count": 5, "positions": ["客厅-餐厅", "卧室1入口"]}}
        ],
        "circulation": {{
            "main_entrance": "底部中央",
            "main_path": "主入口 → 玄关 → 客厅 → 餐厅",
            "layout_type": "开放式客餐厅"
        }},
        "design_notes": ["主卧带独立卫生间", "动线流畅"]
    }}
}}

**注意事项：**
- 如果标注不清晰，标注为"不可读"或给出估算值并说明
- 优先回答用户的具体问题，不要罗列所有信息
- 如果用户问"有几个卧室"，就重点回答卧室数量和位置
- 如果用户问"客厅面积"，就重点回答客厅的尺寸和面积
- 保持答案简洁、针对性强""",

        ImageType.ARCHITECTURE: """你是一位专业的系统架构和流程图分析专家。请仔细分析这张架构图/流程图。

**用户问题：**
{question}

**分析要求：**
1. **整体架构**：识别系统的整体结构和分层
2. **组件识别**：识别图中的所有模块、组件、服务
3. **关系分析**：分析组件之间的连接关系、数据流向、调用关系
4. **流程理解**：如果是流程图，说明业务流程的步骤和逻辑
5. **技术栈**：识别使用的技术、协议、接口类型
6. **关键节点**：标注关键的决策点、网关、数据库等

**回答方式：**
- 首先直接回答用户的问题
- 然后提供架构/流程的整体说明
- 列出关键组件和它们的作用

**输出格式（JSON）：**
{{
    "answer": "直接回答用户问题的内容",
    "extracted_info": {{
        "diagram_type": "架构图/流程图/时序图等",
        "main_components": ["组件1", "组件2"],
        "layers": ["层级1", "层级2"],
        "data_flow": ["流向描述1", "流向描述2"],
        "key_technologies": ["技术1", "技术2"],
        "process_steps": ["步骤1", "步骤2"]
    }}
}}""",

        ImageType.TECHNICAL_DOC: """你是一位专业的工业技术文档分析专家。请仔细分析这份工艺文件/技术档案。

**用户问题：**
{question}

**分析要求：**
1. **文档类型**：识别是工艺卡片、检验报告、设计变更单等
2. **核心内容**：提取文档的主要技术内容
3. **参数数据**：提取所有关键参数、数值、规格
4. **表格信息**：如果有表格，提取表格中的数据
5. **版本信息**：识别版本号、修订记录、审批信息
6. **工艺流程**：如果是工艺文件，说明加工步骤和工艺要求

**回答方式：**
- 首先直接回答用户的问题
- 然后提供文档的关键信息
- 如果有表格数据或参数列表，完整列出

**输出格式（JSON）：**
{{
    "answer": "直接回答用户问题的内容",
    "extracted_info": {{
        "document_type": "文档类型",
        "document_number": "文档编号",
        "version": "版本号",
        "revision_date": "修订日期",
        "key_parameters": {{"参数名": "参数值"}},
        "process_steps": ["步骤1", "步骤2"],
        "inspection_items": ["检验项1", "检验项2"],
        "tables_data": []
    }}
}}"""
    }

    def __init__(
        self,
        model_url: str = DEFAULT_MODEL_URL,
        api_key: str = DEFAULT_API_KEY,
        model_name: str = DEFAULT_MODEL_NAME
    ):
        """初始化分析器"""
        self.model_url = model_url
        self.api_key = api_key
        self.model_name = model_name

        # 检测API类型
        self.api_type = self._detect_api_type()
        print(f"✓ 初始化VLM分析器: {self.api_type} - {self.model_name}")

        # 如果使用OpenAI SDK，初始化客户端
        if self.api_type == "openai_sdk":
            from openai import AsyncOpenAI
            base_url = model_url.replace("/chat/completions", "") if "/chat/completions" in model_url else model_url
            self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            self.openai_client = None

    def _detect_api_type(self) -> str:
        """检测API类型"""
        url_lower = self.model_url.lower()

        if "dashscope" in url_lower or "aliyun" in url_lower:
            return "qwen"
        elif "anthropic" in url_lower or "claude" in url_lower:
            return "claude"
        elif "openai.com" in url_lower or "gpt" in self.model_name.lower():
            return "openai_sdk"
        else:
            return "openai_sdk"  # 默认使用OpenAI格式

    def _get_request_url(self) -> str:
        """获取完整的请求URL"""
        url = self.model_url
        if "/chat/completions" not in url and url.endswith("/v1"):
            return url + "/chat/completions"
        return url

    def load_image(self, image_source: Union[str, Path, Image.Image]) -> Image.Image:
        """
        加载图片（支持本地文件、URL、PIL Image对象）

        Args:
            image_source: 图片来源（本地路径、URL或PIL Image对象）

        Returns:
            PIL Image对象
        """
        # 如果已经是PIL Image对象
        if isinstance(image_source, Image.Image):
            print(f"✓ 接收到PIL Image对象: {image_source.size}")
            return image_source

        image_source = str(image_source)

        # 如果是URL
        if image_source.startswith(('http://', 'https://')):
            print(f"⬇ 正在从URL下载图片: {image_source}")
            response = requests.get(image_source, timeout=30)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            print(f"✓ 图片下载成功: {image.size}")
            return image

        # 否则视为本地文件路径
        image_path = Path(image_source)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        print(f"📁 正在加载本地图片: {image_path.name}")
        image = Image.open(image_path)
        print(f"✓ 图片加载成功: {image.size}")
        return image

    def image_to_base64(self, image: Image.Image, max_size: int = 2000) -> str:
        """将PIL Image转换为base64字符串"""
        # 压缩大图片
        if image.width > max_size or image.height > max_size:
            image = image.copy()  # 避免修改原图
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            print(f"  图片已压缩到: {image.size}")

        buffer = io.BytesIO()
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    async def analyze_image(
        self,
        image_source: Union[str, Path, Image.Image],
        question: str,
        image_type: str = ImageType.CAD
    ) -> AnalysisResult:
        """
        分析图像并回答问题

        Args:
            image_source: 图片来源（本地路径、URL或PIL Image对象）
            question: 用户问题
            image_type: 图像类型 (cad / architecture / technical_doc)

        Returns:
            AnalysisResult对象
        """
        import time
        start_time = time.time()

        print("\n" + "="*60)
        print(f"🔍 开始图像分析")
        print(f"   类型: {image_type}")
        print(f"   问题: {question}")
        print("="*60)

        # 1. 加载图片
        image = self.load_image(image_source)

        # 2. 转换为base64
        print("🔄 正在将图片转换为base64...")
        image_base64 = self.image_to_base64(image)
        print(f"✓ 转换完成: {len(image_base64) / 1024:.1f} KB")

        # 3. 构建提示词
        if image_type not in self.PROMPTS:
            raise ValueError(f"不支持的图像类型: {image_type}，支持的类型: {list(self.PROMPTS.keys())}")

        prompt = self.PROMPTS[image_type].format(question=question)

        # 4. 调用VLM API
        print(f"🚀 正在调用VLM模型: {self.model_name}")
        response_data = await self._call_vlm_api(image_base64, prompt)

        # 5. 解析响应
        answer = response_data.get('answer', '')
        extracted_info = response_data.get('extracted_info', {})
        raw_response = response_data.get('raw_response', '')
        token_usage = response_data.get('token_usage', {})

        time_cost = time.time() - start_time

        print("\n" + "="*60)
        print("✅ 分析完成")
        print(f"   耗时: {time_cost:.2f}秒")
        print(f"   Token: {token_usage.get('total_tokens', 0)}")
        print("="*60)

        return AnalysisResult(
            image_type=image_type,
            question=question,
            answer=answer,
            extracted_info=extracted_info,
            raw_response=raw_response,
            token_usage=token_usage,
            time_cost=time_cost
        )

    async def _call_vlm_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """调用VLM API（根据API类型自动选择调用方式）"""
        if self.api_type == "openai_sdk":
            return await self._call_openai_api(image_base64, prompt)
        elif self.api_type == "qwen":
            return await self._call_qwen_api(image_base64, prompt)
        elif self.api_type == "claude":
            return await self._call_claude_api(image_base64, prompt)
        else:
            raise ValueError(f"不支持的API类型: {self.api_type}")

    async def _call_openai_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """调用OpenAI格式的API"""
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的工业图纸和技术文档分析专家。请仔细分析图像并按照要求的JSON格式返回结果。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=4096,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # Token统计
            token_usage = {}
            if response.usage:
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                print(f"  Token使用: 输入={token_usage['prompt_tokens']}, "
                      f"输出={token_usage['completion_tokens']}, "
                      f"总计={token_usage['total_tokens']}")

            # 解析JSON响应
            parsed = self._parse_json_response(content)

            return {
                'answer': parsed.get('answer', ''),
                'extracted_info': parsed.get('extracted_info', {}),
                'raw_response': content,
                'token_usage': token_usage
            }

        except Exception as e:
            print(f"❌ API调用失败: {e}")
            raise

    async def _call_qwen_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """调用通义千问API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的工业图纸和技术文档分析专家。"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.1
        }

        request_url = self._get_request_url()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    request_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API错误 {response.status}: {error_text[:500]}")

                    result = await response.json()
                    content = result['choices'][0]['message']['content']

                    # Token统计
                    token_usage = {}
                    if 'usage' in result:
                        usage = result['usage']
                        token_usage = {
                            "prompt_tokens": usage.get('prompt_tokens', 0),
                            "completion_tokens": usage.get('completion_tokens', 0),
                            "total_tokens": usage.get('total_tokens', 0)
                        }

                    parsed = self._parse_json_response(content)

                    return {
                        'answer': parsed.get('answer', ''),
                        'extracted_info': parsed.get('extracted_info', {}),
                        'raw_response': content,
                        'token_usage': token_usage
                    }
        except Exception as e:
            print(f"❌ 通义千问API调用失败: {e}")
            raise

    async def _call_claude_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """调用Claude API"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model_name,
            "max_tokens": 4096,
            "temperature": 0.1,
            "system": "你是一位专业的工业图纸和技术文档分析专家。",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.model_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API错误 {response.status}: {error_text[:500]}")

                    result = await response.json()
                    content = result['content'][0]['text']

                    # Token统计
                    token_usage = {}
                    if 'usage' in result:
                        usage = result['usage']
                        token_usage = {
                            "prompt_tokens": usage.get('input_tokens', 0),
                            "completion_tokens": usage.get('output_tokens', 0),
                            "total_tokens": usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                        }

                    parsed = self._parse_json_response(content)

                    return {
                        'answer': parsed.get('answer', ''),
                        'extracted_info': parsed.get('extracted_info', {}),
                        'raw_response': content,
                        'token_usage': token_usage
                    }
        except Exception as e:
            print(f"❌ Claude API调用失败: {e}")
            raise

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            # 清理markdown代码块标记
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            # 尝试提取JSON部分
            first_brace = content.find('{')
            last_brace = content.rfind('}')
            if first_brace != -1 and last_brace != -1:
                content = content[first_brace:last_brace + 1]

            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败，返回原始内容: {e}")
            return {
                'answer': content,
                'extracted_info': {}
            }

    def print_result(self, result: AnalysisResult):
        """美化打印分析结果"""
        print("\n" + "="*60)
        print("📊 分析结果")
        print("="*60)
        print(f"\n【图像类型】 {result.image_type}")
        print(f"\n【用户问题】 {result.question}")
        print(f"\n【回答】\n{result.answer}")

        if result.extracted_info:
            print(f"\n【提取的结构化信息】")
            print(json.dumps(result.extracted_info, ensure_ascii=False, indent=2))

        print(f"\n【统计信息】")
        print(f"  耗时: {result.time_cost:.2f}秒")
        print(f"  Token: {result.token_usage.get('total_tokens', 0)}")
        print("="*60 + "\n")


# ============ 便捷函数 ============

async def analyze_cad_drawing(
    image_source: Union[str, Path, Image.Image],
    question: str,
    model_url: str = DEFAULT_MODEL_URL,
    api_key: str = DEFAULT_API_KEY,
    model_name: str = DEFAULT_MODEL_NAME
) -> AnalysisResult:
    """分析CAD工程制造图纸"""
    analyzer = SimpleVLMAnalyzer(model_url, api_key, model_name)
    return await analyzer.analyze_image(image_source, question, ImageType.CAD)


async def analyze_architecture_diagram(
    image_source: Union[str, Path, Image.Image],
    question: str,
    model_url: str = DEFAULT_MODEL_URL,
    api_key: str = DEFAULT_API_KEY,
    model_name: str = DEFAULT_MODEL_NAME
) -> AnalysisResult:
    """分析研发架构图/流程图"""
    analyzer = SimpleVLMAnalyzer(model_url, api_key, model_name)
    return await analyzer.analyze_image(image_source, question, ImageType.ARCHITECTURE)


async def analyze_technical_document(
    image_source: Union[str, Path, Image.Image],
    question: str,
    model_url: str = DEFAULT_MODEL_URL,
    api_key: str = DEFAULT_API_KEY,
    model_name: str = DEFAULT_MODEL_NAME
) -> AnalysisResult:
    """分析工业技术档案/工艺文件"""
    analyzer = SimpleVLMAnalyzer(model_url, api_key, model_name)
    return await analyzer.analyze_image(image_source, question, ImageType.TECHNICAL_DOC)


async def analyze_floor_plan(
    image_source: Union[str, Path, Image.Image],
    question: str,
    model_url: str = DEFAULT_MODEL_URL,
    api_key: str = DEFAULT_API_KEY,
    model_name: str = DEFAULT_MODEL_NAME
) -> AnalysisResult:
    """分析室内平面布置图/建筑平面图"""
    analyzer = SimpleVLMAnalyzer(model_url, api_key, model_name)
    return await analyzer.analyze_image(image_source, question, ImageType.FLOOR_PLAN)
