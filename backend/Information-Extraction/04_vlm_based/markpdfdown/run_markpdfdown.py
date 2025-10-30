import os
from dotenv import load_dotenv
from src.markpdfdown import convert_to_markdown

# 加载环境变量（含 OPENAI_API_KEY, MODEL_NAME 等）
load_dotenv()

input_pdf = "/Users/xiaonuo_1/Desktop/赋范空间/learn_data/阿里开发手册-泰山版.pdf"

# 读取文件为二进制
with open(input_pdf, "rb") as f:
    data = f.read()

# 调用核心函数
markdown_text = convert_to_markdown(
    input_data=data,
    input_filename=os.path.basename(input_pdf),
    # start_page=1,
    # end_page=10  # 可选
)

# 保存输出
output_path = "/Users/xiaonuo_1/Desktop/赋范空间/Information_Extraction/LLM_extraction/markpdfdown/output/阿里开发手册-泰山版.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(markdown_text)

print("✅ 转换完成:", output_path)
