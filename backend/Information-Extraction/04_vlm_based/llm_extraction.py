import io
import base64
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from pdf2image import convert_from_bytes
from PIL import Image
import aiohttp
import json
from pathlib import Path
import os
from urllib.parse import urlparse

# ============ 配置部分 ============
# MODEL_URL = "https://api.openai.com/v1"
# API_KEY = "GrkewjMOK7Ixw9NUwYvT3BlbkFJwPXGXk5-H6I0pnzU41XL0XNyTCWeqJPcs7g_ezt6Q2lLf9MF5N2NoUCxETfiFlGRtn9Gde_OAA"
# MODEL_NAME = "gpt-4o"

API_KEY = "sk-Y4o8DF6Iq2l8OcieaS1gXfgIzFkfymV4oF01ofphYB5FxnFT"
MODEL_NAME = "gpt-4o"
MODEL_URL = "https://aizex.top/v1"

# API_KEY = "sk-0fb27bf3a9a448fa9a6f02bd70e37cd8"
# MODEL_NAME = "qwen3-vl-plus"
# MODEL_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 批处理配置
PAGES_PER_REQUEST = 1
CONCURRENT_REQUESTS = 1

@dataclass
class ExtractionResult:
    """提取结果数据类"""
    markdown_content: str
    tables: List[Dict[str, Any]]
    formulas: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    token_usage: Dict[str, int]
    time_cost: Dict[str, float]
    page_images: List[Image.Image]  # 保存每页的图片
    per_page_results: List[Dict[str, Any]]  # 保存每页的识别结果


class PDFMultimodalExtractor:
    """PDF多模态信息抽取器"""
    
    def __init__(
        self, 
        model_url: str = MODEL_URL, 
        api_key: str = API_KEY, 
        model_name: str = MODEL_NAME,
        pages_per_request: int = PAGES_PER_REQUEST
    ):
        self.model_url = model_url
        self.api_key = api_key
        self.model_name = model_name
        self.dpi = 100
        self.pages_per_request = pages_per_request
        
        # 检测API类型
        self.api_type = self._detect_api_type()
        print(f"✓ 检测到API类型: {self.api_type}")
        
        # 如果使用OpenAI SDK，初始化客户端
        if self.api_type == "openai_sdk":
            from openai import AsyncOpenAI
            if "/chat/completions" in model_url:
                base_url = model_url.replace("/chat/completions", "")
            else:
                base_url = model_url
            self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            print(f"  使用OpenAI SDK (base_url: {base_url})")
        else:
            self.openai_client = None
            print(f"  使用HTTP客户端 (url: {model_url})")
        
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        
        self.pdf_convert_time = 0
        self.api_call_time = 0
        self.total_time = 0
    
    def _detect_api_type(self) -> str:
        """检测API类型：openai_sdk, qwen, claude"""
        url_lower = self.model_url.lower()
        
        # 通义千问/DashScope
        if "dashscope" in url_lower or "aliyun" in url_lower:
            return "qwen"
        
        # Claude API
        if "anthropic" in url_lower or "claude" in url_lower:
            return "claude"
        
        # OpenAI官方或使用OpenAI SDK
        if any(x in url_lower for x in ["openai.com", "api.openai.com", "oai.azure.com"]):
            return "openai_sdk"
        
        # 如果模型名包含gpt，使用OpenAI SDK（兼容第三方代理）
        if "gpt" in self.model_name.lower():
            return "openai_sdk"
        
        # 默认使用Claude格式
        return "claude"

    def _get_request_url(self) -> str:
        """返回实际要POST的完整URL"""
        url = self.model_url
        lower = url.lower()

        # 已包含完整端点，直接返回
        if any(x in lower for x in ["/chat/completions", "/v1/completions", "completions"]):
            return url

        # DashScope兼容模式URL
        if "dashscope" in lower and "compatible-mode" in lower:
            if not url.endswith("/chat/completions"):
                return url.rstrip('/') + '/chat/completions'
            return url

        # 类似 https://host/.../v1 格式，补上 chat/completions
        parsed = urlparse(url)
        path = parsed.path or ""
        if path.rstrip('/') == '/v1':
            return url.rstrip('/') + '/chat/completions'

        return url
        
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """将PDF转换为图片列表"""
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        images = convert_from_bytes(pdf_content, dpi=self.dpi)
        return images
    
    def image_to_base64(self, image: Image.Image, max_size: int = 2000) -> str:
        """将PIL Image转换为base64字符串，并压缩图片"""
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    async def call_multimodal_api_openai_sdk(
        self,
        image_base64_list: List[str],
        page_nums: List[int],
        total_pages: int
    ) -> Dict[str, Any]:
        """使用OpenAI官方SDK调用API（适用于GPT系列）"""
        import time
        start_time = time.time()
        
        page_range = f"{page_nums[0]}-{page_nums[-1]}" if len(page_nums) > 1 else str(page_nums[0])
        
        prompt = self._get_extraction_prompt(page_range, total_pages)
        
        # 构建消息内容 - OpenAI格式
        content_items = [{"type": "text", "text": prompt}]
        
        for img_base64 in image_base64_list:
            content_items.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
        
        messages = [
            {
                "role": "system", 
                "content": "你是一个专业的PDF文档信息提取助手。你必须严格按照用户要求的JSON格式返回结果，不要添加任何解释性文字或markdown代码块标记。直接返回可解析的JSON对象。"
            },
            {"role": "user", "content": content_items}
        ]
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=4096,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # 提取Token使用信息
            if response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                
                self.total_prompt_tokens += prompt_tokens
                self.total_completion_tokens += completion_tokens
                self.total_tokens += total_tokens
                
                print(f"  第{page_range}页 Token: 输入={prompt_tokens}, 输出={completion_tokens}, 总计={total_tokens}")
            
            content = response.choices[0].message.content
            
            api_time = time.time() - start_time
            print(f"  第{page_range}页 耗时: {api_time:.2f}秒")
            
            return self._parse_response_content(content, page_nums)
            
        except Exception as e:
            print(f"❌ OpenAI SDK调用失败: {type(e).__name__}: {e}")
            raise
    
    async def call_multimodal_api_qwen(
        self,
        image_base64_list: List[str],
        page_nums: List[int],
        total_pages: int
    ) -> Dict[str, Any]:
        """调用通义千问API（DashScope兼容模式）"""
        import time
        start_time = time.time()
        
        page_range = f"{page_nums[0]}-{page_nums[-1]}" if len(page_nums) > 1 else str(page_nums[0])
        
        prompt = self._get_extraction_prompt(page_range, total_pages)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建消息内容 - 通义千问格式
        content_items = [{"type": "text", "text": prompt}]
        
        # 关键修复：通义千问使用 image_url 类型，而不是 image 类型
        for img_base64 in image_base64_list:
            content_items.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的PDF文档信息提取助手。你必须严格按照用户要求的JSON格式返回结果，不要添加任何解释性文字或markdown代码块标记。"
                },
                {"role": "user", "content": content_items}
            ],
            "max_tokens": 4096,
            "temperature": 0.1
        }
        
        payload_size = len(json.dumps(payload))
        print(f"  请求体大小: {payload_size / 1024 / 1024:.2f} MB")

        request_url = self._get_request_url()
        print(f"  请求URL: {request_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    request_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        display_text = response_text[:1000]
                        print(f"❌ API错误: {response.status}")
                        print(f"错误详情: {display_text}")
                        raise Exception(f"API调用失败: {response.status} - {display_text}")

                    result = await response.json()

                    # 提取Token使用信息
                    if 'usage' in result:
                        usage = result['usage']
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                        total_tokens = usage.get('total_tokens', 0)

                        self.total_prompt_tokens += prompt_tokens
                        self.total_completion_tokens += completion_tokens
                        self.total_tokens += total_tokens

                        print(f"  第{page_range}页 Token: 输入={prompt_tokens}, 输出={completion_tokens}, 总计={total_tokens}")

                    # 提取响应内容
                    content = result['choices'][0]['message']['content']

                    api_time = time.time() - start_time
                    print(f"  第{page_range}页 耗时: {api_time:.2f}秒")

                    return self._parse_response_content(content, page_nums)
                    
        except asyncio.TimeoutError:
            print(f"❌ 请求超时（页面 {page_range}）")
            raise
        except Exception as e:
            print(f"❌ 通义千问API调用异常: {type(e).__name__}: {e}")
            raise
    
    async def call_multimodal_api_claude(
        self,
        image_base64_list: List[str],
        page_nums: List[int],
        total_pages: int
    ) -> Dict[str, Any]:
        """调用Claude API"""
        import time
        start_time = time.time()
        
        page_range = f"{page_nums[0]}-{page_nums[-1]}" if len(page_nums) > 1 else str(page_nums[0])
        
        prompt = self._get_extraction_prompt(page_range, total_pages)
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # 构建消息内容 - Claude格式
        claude_content = []
        for img_base64 in image_base64_list:
            claude_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": img_base64
                }
            })
        claude_content.append({"type": "text", "text": prompt})
        
        payload = {
            "model": self.model_name,
            "max_tokens": 4096,
            "temperature": 0.1,
            "system": "你是一个专业的PDF文档信息提取助手。你必须严格按照用户要求的JSON格式返回结果。",
            "messages": [{"role": "user", "content": claude_content}]
        }
        
        payload_size = len(json.dumps(payload))
        print(f"  请求体大小: {payload_size / 1024 / 1024:.2f} MB")
        print(f"  请求URL: {self.model_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.model_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        display_text = response_text[:1000]
                        print(f"❌ API错误: {response.status}")
                        print(f"错误详情: {display_text}")
                        raise Exception(f"API调用失败: {response.status} - {display_text}")

                    result = await response.json()

                    # 提取Token使用信息
                    if 'usage' in result:
                        usage = result['usage']
                        prompt_tokens = usage.get('input_tokens', 0)
                        completion_tokens = usage.get('output_tokens', 0)
                        total_tokens = prompt_tokens + completion_tokens

                        self.total_prompt_tokens += prompt_tokens
                        self.total_completion_tokens += completion_tokens
                        self.total_tokens += total_tokens

                        print(f"  第{page_range}页 Token: 输入={prompt_tokens}, 输出={completion_tokens}, 总计={total_tokens}")

                    # 提取响应内容
                    content = result['content'][0]['text']

                    api_time = time.time() - start_time
                    print(f"  第{page_range}页 耗时: {api_time:.2f}秒")

                    return self._parse_response_content(content, page_nums)
                    
        except asyncio.TimeoutError:
            print(f"❌ 请求超时（页面 {page_range}）")
            raise
        except Exception as e:
            print(f"❌ Claude API调用异常: {type(e).__name__}: {e}")
            raise
    
    def _get_extraction_prompt(self, page_range: str, total_pages: int) -> str:
        """生成提取指令的prompt"""
        return f"""【重要】请直接分析图片内容并返回JSON，不要说"我无法提取"或给出任何解释。

分析这些PDF页面（第{page_range}页，共{total_pages}页）：

1. **Markdown内容**：
   - 识别所有标题层级（# ## ###）
   - 保持段落结构和格式
   - 保留列表、引用
   - 表格用Markdown表格语法
   - 忽略页眉和页脚内容，不要将其识别为标题或正文
   - 按页面顺序组织，页间用 `---` 分隔
   
2. **表格提取**：
   - 提取所有表格（表头+数据）
   - 标注所在页码
   
3. **公式提取**：
   - 提取所有数学公式（行内+独立）
   - 使用LaTeX格式
   - 标注所在页码
   
4. **图片描述**：
   - 描述所有非表格、非公式的图像内容
   - 包括图表、示意图、照片等
   - 输出其视觉内容、含义及上下文作用
   - 标注所在页码

**输出格式要求（必须严格遵守）：**
- 直接返回纯JSON对象
- 不要用```json或```包裹
- 不要添加任何解释文字
- 不要说"我无法..."之类的话

**JSON结构：**
{{
    "pages": [
        {{
            "page_num": 页码(整数),
            "markdown": "该页完整markdown内容",
            "page_title": "主标题或空字符串"
        }}
    ],
    "tables": [
        {{
            "page": 页码(整数),
            "id": "表格1",
            "caption": "表格标题或空字符串",
            "content": "markdown表格",
            "data": [["单元格1", "单元格2"]]
        }}
    ],
    "formulas": [
        {{
            "page": 页码(整数),
            "id": "公式1",
            "latex": "LaTeX公式",
            "type": "inline或display",
            "context": "公式前后文本"
        }}
    ],
    "images": [
        {{
            "page": 页码(整数),
            "id": "图片1",
            "description": "图片的详细描述",
            "type": "chart/graph/photo/diagram/etc",
            "context": "图片出现的上下文"
        }}
    ]
}}

现在请分析图片并直接返回上述JSON结构："""
    
    def _parse_response_content(self, content: str, page_nums: List[int]) -> Dict[str, Any]:
        """解析API响应内容"""
        try:
            # 清理内容
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON解析失败: {e}")
            print(f"原始内容前200字符: {content[:200]}...")
            
            # 检查是否是模型拒绝提取的回复
            refusal_keywords = ["unable to", "cannot", "can't", "sorry", "i'm not able"]
            if any(keyword in content.lower() for keyword in refusal_keywords):
                print(f"⚠️  模型拒绝提取内容，页面 {page_nums} 将标记为处理失败")
                return {
                    "pages": [{
                        "page_num": num,
                        "markdown": f"## 第{num}页\n**提取失败：模型拒绝处理此页面**\n{content[:500]}",
                        "page_title": f"第{num}页（提取失败）"
                    } for num in page_nums],
                    "tables": [],
                    "formulas": [],
                    "images": []
                }
            
            # 如果不是拒绝，尝试将原始内容作为markdown
            print(f"⚠️  将原始响应作为markdown内容保存")
            return {
                "pages": [{
                    "page_num": num,
                    "markdown": content,
                    "page_title": f"第{num}页"
                } for num in page_nums],
                "tables": [],
                "formulas": [],
                "images": []
            }
    
    async def call_multimodal_api(
        self,
        image_base64_list: List[str],
        page_nums: List[int],
        total_pages: int
    ) -> Dict[str, Any]:
        """调用多模态API的统一入口 - 根据API类型路由"""
        if self.api_type == "openai_sdk":
            return await self.call_multimodal_api_openai_sdk(
                image_base64_list, page_nums, total_pages
            )
        elif self.api_type == "qwen":
            return await self.call_multimodal_api_qwen(
                image_base64_list, page_nums, total_pages
            )
        elif self.api_type == "claude":
            return await self.call_multimodal_api_claude(
                image_base64_list, page_nums, total_pages
            )
        else:
            raise ValueError(f"不支持的API类型: {self.api_type}")
    
    async def extract_from_pdf(self, pdf_path: str) -> ExtractionResult:
        """从PDF文件中提取完整信息"""
        import time
        overall_start = time.time()
        
        print(f"开始处理PDF: {pdf_path}")
        print("="*60)
        
        # 1. 转换PDF为图片
        print("\n[步骤1] 正在将PDF转换为图片...")
        convert_start = time.time()
        images = self.pdf_to_images(pdf_path)
        self.pdf_convert_time = time.time() - convert_start
        total_pages = len(images)
        print(f"✓ 转换完成: 共 {total_pages} 页 (耗时: {self.pdf_convert_time:.2f}秒)")
        
        # 2. 分组并逐批分析
        print(f"\n[步骤2] 开始API调用分析 (每次处理{self.pages_per_request}页)...")
        api_start = time.time()
        
        all_markdown = []
        all_tables = []
        all_formulas = []
        all_images = []
        page_titles = []
        per_page_results = []  # 保存每页的详细结果
        
        # 将页面分组
        page_groups = []
        for i in range(0, total_pages, self.pages_per_request):
            end_idx = min(i + self.pages_per_request, total_pages)
            page_group = {
                'images': images[i:end_idx],
                'page_nums': list(range(i + 1, end_idx + 1))
            }
            page_groups.append(page_group)
        
        print(f"已分为 {len(page_groups)} 个批次")
        
        # 顺序执行API调用
        results = []
        for idx, group in enumerate(page_groups):
            print(f"\n处理批次 {idx + 1}/{len(page_groups)}:")
            image_base64_list = [self.image_to_base64(img) for img in group['images']]
            
            try:
                result = await self.call_multimodal_api(
                    image_base64_list, 
                    group['page_nums'], 
                    total_pages
                )
                results.append(result)
                print(f"✓ 批次 {idx + 1} 完成")
            except Exception as e:
                print(f"❌ 批次 {idx + 1} 失败: {e}")
                results.append(Exception(str(e)))
            
            # 批次间延迟
            if idx < len(page_groups) - 1:
                await asyncio.sleep(1)
        
        self.api_call_time = time.time() - api_start
        print(f"\n✓ API调用完成 (总耗时: {self.api_call_time:.2f}秒)")
        
        # 3. 整合结果
        print(f"\n[步骤3] 整合提取结果...")
        
        # 严格按照发送顺序拼接，不依赖大模型返回的page_num
        for batch_idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️  批次 {batch_idx + 1} 处理失败: {result}")
                # 为失败的批次添加占位符
                page_group = page_groups[batch_idx]
                for page_num in page_group['page_nums']:
                    if len(all_markdown) > 0:
                        all_markdown.append("\n---\n")
                    all_markdown.append(f"## 第{page_num}页（处理失败）\n")
                    
                    # 添加失败页的结果记录
                    per_page_results.append({
                        "page_num": page_num,
                        "status": "failed",
                        "error": str(result),
                        "markdown": f"## 第{page_num}页（处理失败）\n",
                        "page_title": "",
                        "tables": [],
                        "formulas": [],
                        "images": []
                    })
                continue
            
            # 获取这个批次的页面数据
            pages_data = result.get('pages', [])
            page_group = page_groups[batch_idx]
            expected_page_nums = page_group['page_nums']
            
            # 严格按照我们发送的页码顺序来拼接
            for i, page_num in enumerate(expected_page_nums):
                # 添加分隔符
                if len(all_markdown) > 0:
                    all_markdown.append("\n---\n")
                
                # 按索引匹配页面数据，不使用大模型返回的page_num
                if i < len(pages_data):
                    page_data = pages_data[i]
                    markdown = page_data.get('markdown', '')
                    page_title = page_data.get('page_title', '')
                    
                    if page_title:
                        page_titles.append(page_title)
                    all_markdown.append(markdown)
                    
                    # 收集该页的表格
                    page_tables = [t for t in result.get('tables', []) 
                                  if t.get('page') == page_num]
                    
                    # 收集该页的公式
                    page_formulas = [f for f in result.get('formulas', []) 
                                    if f.get('page') == page_num]
                    
                    # 收集该页的图片描述
                    page_images = [img for img in result.get('images', []) 
                                  if img.get('page') == page_num]
                    
                    # 保存该页的完整结果
                    per_page_results.append({
                        "page_num": page_num,
                        "status": "success",
                        "markdown": markdown,
                        "page_title": page_title,
                        "tables": page_tables,
                        "formulas": page_formulas,
                        "images": page_images
                    })
                    
                    print(f"✓ 第{page_num}页内容已拼接")
                else:
                    print(f"⚠️  第 {page_num} 页数据缺失")
                    all_markdown.append(f"## 第{page_num}页（数据缺失）\n")
                    
                    # 添加缺失页的结果记录
                    per_page_results.append({
                        "page_num": page_num,
                        "status": "missing",
                        "markdown": f"## 第{page_num}页（数据缺失）\n",
                        "page_title": "",
                        "tables": [],
                        "formulas": [],
                        "images": []
                    })
            
            # 收集表格、公式、图片（保持原有逻辑）
            for table in result.get('tables', []):
                all_tables.append(table)
            
            for formula in result.get('formulas', []):
                all_formulas.append(formula)
            
            for image in result.get('images', []):
                all_images.append(image)
        
        final_markdown = ''.join(all_markdown)
        
        if page_titles:
            document_title = page_titles[0]
            final_markdown = f"# {document_title}\n{final_markdown}"
        
        self.total_time = time.time() - overall_start
        
        token_usage = {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens
        }
        
        time_cost = {
            "pdf_convert_time": round(self.pdf_convert_time, 2),
            "api_call_time": round(self.api_call_time, 2),
            "total_time": round(self.total_time, 2)
        }
        
        metadata = {
            "total_pages": total_pages,
            "total_tables": len(all_tables),
            "total_formulas": len(all_formulas),
            "total_images": len(all_images),
            "page_titles": page_titles
        }
        
        print("\n" + "="*60)
        print("✓ 提取完成！")
        print("="*60)
        print(f"📄 总页数: {metadata['total_pages']}")
        print(f"📊 表格数: {metadata['total_tables']}")
        print(f"🔢 公式数: {metadata['total_formulas']}")
        print(f"🖼️  图片数: {metadata['total_images']}")
        print(f"💰 Token: {token_usage['total_tokens']:,}")
        print(f"⏱️  耗时: {time_cost['total_time']}秒")
        print("="*60)
        
        return ExtractionResult(
            markdown_content=final_markdown,
            tables=all_tables,
            formulas=all_formulas,
            metadata=metadata,
            token_usage=token_usage,
            time_cost=time_cost,
            page_images=images,  # 保存所有页面的图片
            per_page_results=per_page_results  # 保存每页的识别结果
        )
    
    def save_results(self, result: ExtractionResult, output_dir: str = "output"):
        """保存提取结果到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 创建images子目录
        images_path = output_path / "images"
        images_path.mkdir(exist_ok=True)
        
        # 1. 保存每页图片
        print(f"\n💾 保存页面图片...")
        for idx, image in enumerate(result.page_images):
            page_num = idx + 1
            image_filename = f"page_{page_num:03d}.jpg"
            image_path = images_path / image_filename
            
            # 转换并保存图片
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            image.save(image_path, format='JPEG', quality=95)
            print(f"  ✓ 第{page_num}页图片: {image_filename}")
        
        # 2. 保存每页识别结果
        print(f"\n💾 保存每页识别结果...")
        # 为每页结果添加图片文件名
        for page_result in result.per_page_results:
            page_num = page_result['page_num']
            page_result['image_file'] = f"images/page_{page_num:03d}.jpg"
        
        with open(output_path / "per_page_results.json", 'w', encoding='utf-8') as f:
            json.dump(result.per_page_results, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 每页结果: per_page_results.json")
        
        # 3. 保存完整markdown
        with open(output_path / "full_content.md", 'w', encoding='utf-8') as f:
            f.write(result.markdown_content)
        print(f"  ✓ 完整内容: full_content.md")
        
        # 4. 保存所有表格
        with open(output_path / "tables.json", 'w', encoding='utf-8') as f:
            json.dump(result.tables, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 所有表格: tables.json")
        
        # 5. 保存所有公式
        with open(output_path / "formulas.json", 'w', encoding='utf-8') as f:
            json.dump(result.formulas, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 所有公式: formulas.json")
        
        # 6. 保存元数据
        complete_metadata = {
            **result.metadata,
            "token_usage": result.token_usage,
            "time_cost": result.time_cost
        }
        with open(output_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(complete_metadata, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 元数据: metadata.json")
        
        print(f"\n✅ 所有结果已保存到: {output_path.absolute()}")
        print(f"   - 页面图片: {len(result.page_images)} 张")
        print(f"   - 识别结果: {len(result.per_page_results)} 页")


async def main(pdf_file, output_dir="output"):
    extractor = PDFMultimodalExtractor(
        model_url=MODEL_URL,
        api_key=API_KEY,
        model_name=MODEL_NAME
    )
    
    result = await extractor.extract_from_pdf(pdf_file)
    extractor.save_results(result, output_dir=output_dir)
    
    print("\n📝 内容预览 (前500字符):")
    print(result.markdown_content[:500])
    print("...")


if __name__ == "__main__":
    pdf_file = "/Users/xiaonuo_1/Desktop/赋范空间/learn_data/阿里开发手册-泰山版.pdf"
    output = "/Users/xiaonuo_1/Desktop/赋范空间/Information_Extraction/LLM_extraction/output_gpt"
    asyncio.run(main(pdf_file=pdf_file, output_dir=output))