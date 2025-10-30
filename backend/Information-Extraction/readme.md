Information-Extraction/
├── 01_rule_based/                    # ✅ 已完成，保留即可
│   ├── MarkItDown/
│   ├── PDFMiner/
│   ├── PDFPlumber/
│   ├── PyMuPDF/
│   ├── PyMuPDF4LLM/
│   ├── Unstructured/
│   └── README.md                     # 补充：方案1总结对比
│
├── 02_lightweight_ocr/               # 方案2：只测1个主力工具
│   ├── PaddleOCR/                    # ⭐ 唯一必测 - 中文最强
│   │   ├── basic_ocr.py              # 基础OCR
│   │   ├── ppstructure_v3.py         # 文档解析（核心）
│   │   └── README.md
│   └── README.md                     # 与方案1的对比说明
│
├── 03_integrated_tools/              # 方案3：测2个做对比
│   ├── MinerU/                       # ⭐ 主力 - 专为RAG设计
│   └── Marker/                       # 🔥 对比 - 速度快，看差异
|
│
├── 04_vlm_based/                     # 方案4：VLM方案
├── olmOCR/                       # ⭐ 必测 - 通用场景最强
│   ├── setup.sh                  
│   ├── single_pdf_test.py        
│   ├── benchmark_vs_mineru.py    # 与MinerU对比
│   └── README.md
├── Logics-Parsing/               # 🔬 可选 - STEM内容专家
│   ├── setup.sh
│   ├── basic_test.py
│   ├── chemistry_test.py         # 化学式识别测试（独特功能）
│   ├── vs_olmocr.py              # 与olmOCR对比
│   └── README.md
├── comparison/                   # 对比分析
│   ├── benchmark_results.md      # 详细对比数据
│   └── selection_guide.md        # 选型指南
└── README.md                     # VLM方案总结