from gptpdf import parse_pdf

pdf_path = '/Users/xiaonuo_1/Desktop/赋范空间/learn_data/阿里开发手册-泰山版.pdf'
output_dir = '/Users/xiaonuo_1/Desktop/赋范空间/Information_Extraction/LLM_extraction/gptpdf/output/阿里开发手册-泰山版'  # 结果（图片、output.md）会写到这里


API_KEY = "sk-0fb27bf3a9a448fa9a6f02bd70e37cd8"
MODEL_NAME = "qwen3-vl-plus"
MODEL_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

content, image_paths = parse_pdf(
    pdf_path=pdf_path,
    output_dir=output_dir,
    api_key=API_KEY,
    base_url=MODEL_URL,
    model=MODEL_NAME,
    gpt_worker=1,
    # 删掉这三行 ↓↓↓
    # prompt=None,
    # rect_prompt=None,
    # role_prompt=None,
)

print('Markdown length:', len(content))
print('Extracted images:', image_paths)
# output_dir/output.md 会同时写入最终的 markdown