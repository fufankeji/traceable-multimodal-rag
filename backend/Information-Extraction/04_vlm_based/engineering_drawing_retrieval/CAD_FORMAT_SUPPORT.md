# CAD 文件格式支持方案

## 📋 当前状态

### ✅ 已支持格式
- **PNG/JPG/JPEG**：图像格式，可直接被 VLM 分析
- 通过 PIL (Pillow) 加载

### ❌ 未支持格式
- **DWG**：AutoCAD 原生格式（矢量）
- **DXF**：AutoCAD 交换格式（矢量）
- **PDF**：常见导出格式
- **DWF/DWFX**：AutoCAD Web 格式

---

## 🎯 扩展方案

### 方案 1：仅添加格式转换（最简单）

**适用场景**：只需要 VLM 视觉分析，不需要提取矢量数据

**实现步骤**：

#### 1.1 添加 PDF 支持

```bash
pip install pdf2image poppler-utils
```

```python
from pdf2image import convert_from_path

def convert_pdf_to_image(pdf_path: str, output_path: str, dpi: int = 300):
    """将 PDF 转换为图像"""
    images = convert_from_path(pdf_path, dpi=dpi)
    images[0].save(output_path, 'PNG')
    return output_path
```

#### 1.2 添加 DXF/DWG 转 PNG 支持

**使用 ezdxf + matplotlib**：

```bash
pip install ezdxf matplotlib
```

```python
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt

def render_dxf_to_image(dxf_path: str, output_path: str, dpi: int = 300):
    """将 DXF 渲染为图像"""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    fig = plt.figure(figsize=(20, 20), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)

    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close()
    return output_path
```

**使用 ODA File Converter**（更精确）：

```bash
# 下载 ODA File Converter
# https://www.opendesign.com/guestfiles/oda_file_converter

# 命令行转换
ODAFileConverter input.dwg output.pdf
```

---

### 方案 2：混合解析（推荐 ⭐）

**适用场景**：既需要精确的矢量数据，又需要 VLM 的语义理解

**架构设计**：

```
CAD 文件 (DWG/DXF)
    ↓
┌─────────────┴─────────────┐
↓                           ↓
矢量数据提取              图像渲染
(ezdxf)                   (matplotlib/ODA)
↓                           ↓
文字、尺寸、图层          PNG 图像
↓                           ↓
└─────────────┬─────────────┘
              ↓
        VLM 分析 (布局、空间关系)
              ↓
        数据融合
              ↓
      完整结构化数据
```

**代码实现框架**：

```python
class CADAnalyzer:
    """CAD 文件分析器（矢量 + VLM 混合）"""

    def __init__(self):
        self.vlm_analyzer = EngineeringDrawingAnalyzer()

    async def analyze_cad_file(self, cad_path: str) -> dict:
        """分析 CAD 文件"""
        # 1. 判断文件类型
        file_ext = Path(cad_path).suffix.lower()

        if file_ext in ['.dxf', '.dwg']:
            # 2. 提取矢量数据
            vector_data = self.extract_vector_data(cad_path)

            # 3. 渲染为图像
            image_path = self.render_to_image(cad_path)

            # 4. VLM 分析
            vlm_result = await self.vlm_analyzer.analyze_image(
                image_path,
                image_type="floor_plan"
            )

            # 5. 融合数据
            return self.merge_results(vector_data, vlm_result)

        elif file_ext in ['.png', '.jpg', '.jpeg']:
            # 直接使用 VLM 分析
            return await self.vlm_analyzer.analyze_image(cad_path)

        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    def extract_vector_data(self, dxf_path: str) -> dict:
        """从 DXF 提取矢量数据"""
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # 提取文字标注
        texts = []
        for text_entity in msp.query('TEXT MTEXT'):
            texts.append({
                'content': text_entity.dxf.text,
                'position': tuple(text_entity.dxf.insert),
                'height': text_entity.dxf.height
            })

        # 提取尺寸标注
        dimensions = []
        for dim in msp.query('DIMENSION'):
            dimensions.append({
                'value': dim.get_measurement(),
                'position': tuple(dim.dxf.defpoint)
            })

        # 提取图层信息
        layers = [layer.dxf.name for layer in doc.layers]

        return {
            'texts': texts,
            'dimensions': dimensions,
            'layers': layers
        }

    def render_to_image(self, dxf_path: str, dpi: int = 300) -> str:
        """将 DXF 渲染为图像"""
        output_path = dxf_path.replace('.dxf', '_rendered.png')
        # 使用方案 1.2 的渲染代码
        render_dxf_to_image(dxf_path, output_path, dpi)
        return output_path

    def merge_results(self, vector_data: dict, vlm_result) -> dict:
        """融合矢量数据和 VLM 结果"""
        merged = vlm_result.structured_data.copy()

        # 用精确的矢量尺寸覆盖 VLM 估算的尺寸
        merged['precise_dimensions'] = vector_data['dimensions']

        # 用 OCR 提取的文字补充 VLM 识别的标注
        merged['precise_annotations'] = vector_data['texts']

        # 添加图层信息
        merged['layers'] = vector_data['layers']

        return merged
```

---

### 方案 3：纯矢量解析（高精度）

**适用场景**：对尺寸精度要求极高，不需要 VLM 语义理解

**特点**：
- ✅ 100% 精确的尺寸数据
- ✅ 完整的图层、标注信息
- ❌ 无法理解"这是客厅"等语义信息
- ❌ 需要图纸规范性高（标注完整）

**实现示例**：

```python
import ezdxf

def extract_floor_plan_info(dxf_path: str) -> dict:
    """从 DXF 提取平面图信息"""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    rooms = []

    # 提取封闭区域（假设房间是 POLYLINE 或 LWPOLYLINE）
    for polyline in msp.query('LWPOLYLINE POLYLINE'):
        if polyline.is_closed:
            # 计算面积
            area = polyline.area()

            # 查找该区域内的文字（作为房间名称）
            center = polyline.bounding_box().center
            nearby_texts = find_texts_near(msp, center, radius=500)
            room_name = nearby_texts[0] if nearby_texts else "未命名"

            rooms.append({
                'name': room_name,
                'area': area / 1000000,  # mm² -> m²
                'perimeter': polyline.length(),
                'vertices': list(polyline.vertices())
            })

    return {'rooms': rooms}
```

---

## 🛠️ 实施建议

### 阶段 1：快速原型（1-2 天）
✅ 实现方案 1（格式转换）
- 添加 PDF → PNG 转换
- 添加 DXF → PNG 渲染
- 修改 `vlm_analyzer.py` 自动检测格式并转换

### 阶段 2：混合增强（3-5 天）
✅ 实现方案 2（混合解析）
- 集成 ezdxf 提取矢量数据
- 实现数据融合逻辑
- 提高尺寸精度（用矢量数据覆盖 VLM 估算）

### 阶段 3：深度优化（1-2 周）
✅ 实现方案 3（纯矢量解析）
- 开发 CAD 图纸结构化解析器
- 建立房间识别算法（基于封闭轮廓）
- 添加规范性验证（检查标注完整性）

---

## 📦 依赖库安装

```bash
# 基础图像处理
pip install pillow

# PDF 支持
pip install pdf2image
# 系统依赖（Ubuntu/Debian）
sudo apt-get install poppler-utils

# DXF/DWG 支持
pip install ezdxf

# 渲染支持
pip install matplotlib

# （可选）高级 CAD 处理
pip install OCC  # OpenCascade - 复杂几何计算
```

---

## 🧪 测试用例

### 测试 1：PNG 图像（当前已支持）
```python
result = await analyzer.analyze_image("floor_plan.png", "floor_plan")
```

### 测试 2：PDF 转换
```python
# 先转换
image_path = convert_pdf_to_image("floor_plan.pdf", "temp.png")
result = await analyzer.analyze_image(image_path, "floor_plan")
```

### 测试 3：DXF 混合解析
```python
cad_analyzer = CADAnalyzer()
result = await cad_analyzer.analyze_cad_file("floor_plan.dxf")
# 应该包含：
# - 精确尺寸（从 DXF）
# - 房间语义（从 VLM）
# - 动线分析（从 VLM）
```

---

## ❓ 常见问题

### Q1: DWG 和 DXF 有什么区别？
- **DWG**：二进制格式，AutoCAD 原生，需要专门库解析
- **DXF**：文本/二进制格式，开放标准，更容易解析
- **建议**：优先要求用户提供 DXF 格式

### Q2: ezdxf 能读取 DWG 吗？
- **不能直接读取**，需要先转换 DWG → DXF
- 可以使用 ODA File Converter 或 AutoCAD 导出

### Q3: 渲染的图像和原始 CAD 显示不一致？
- 可能原因：线宽、颜色、图层显示设置不同
- 解决方案：使用 ODA File Converter 导出 PDF，再转 PNG

### Q4: 如何处理多页 PDF（多张图纸）？
```python
images = convert_from_path("drawings.pdf")
results = []
for i, image in enumerate(images):
    image.save(f"temp_page_{i}.png")
    result = await analyzer.analyze_image(f"temp_page_{i}.png")
    results.append(result)
```

---

## 🎯 下一步行动

你想先实现哪个方案？

1. **方案 1**：快速支持 PDF 和 DXF 转图像（1-2 小时）
2. **方案 2**：混合解析，提取矢量数据 + VLM（半天）
3. **先看看效果**：我帮你用当前 PNG/JPG 方案测试一下

请告诉我你的选择，或者提供你的 CAD 文件（DXF/DWG/PDF/PNG 都可以），我帮你分析！
