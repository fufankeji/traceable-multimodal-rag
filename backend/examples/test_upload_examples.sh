#!/bin/bash
# 测试上传功能的示例脚本

BASE_URL="http://localhost:8000"

echo "=================================="
echo "多模态 RAG 上传测试示例"
echo "=================================="
echo ""

# 示例1: 上传图片 - 自动识别类型
echo "示例1: 上传图片（自动识别类型）"
echo "curl -X POST $BASE_URL/upload -F \"file=@your_image.png\""
echo ""

# 示例2: 上传CAD图纸 - 手动指定类型
echo "示例2: 上传CAD图纸（手动指定）"
echo "curl -X POST $BASE_URL/upload \\"
echo "  -F \"file=@cad_drawing.dwg\" \\"
echo "  -F \"image_type=cad\""
echo ""

# 示例3: 上传平面布置图
echo "示例3: 上传平面布置图"
echo "curl -X POST $BASE_URL/upload \\"
echo "  -F \"file=@floor_plan.png\" \\"
echo "  -F \"image_type=floor_plan\""
echo ""

# 示例4: 上传架构图
echo "示例4: 上传架构图"
echo "curl -X POST $BASE_URL/upload \\"
echo "  -F \"file=@architecture_diagram.jpg\" \\"
echo "  -F \"image_type=architecture\""
echo ""

# 示例5: 上传技术文档
echo "示例5: 上传技术文档"
echo "curl -X POST $BASE_URL/upload \\"
echo "  -F \"file=@technical_doc.jpg\" \\"
echo "  -F \"image_type=technical_doc\""
echo ""

# 示例6: 上传包含图片的PDF
echo "示例6: 上传包含图片的PDF（自动分析图片页面）"
echo "curl -X POST $BASE_URL/upload \\"
echo "  -F \"file=@manual_with_images.pdf\""
echo ""

# 示例7: 查看响应（带类型检测）
echo "示例7: 完整示例 - 上传并查看响应"
echo "curl -X POST $BASE_URL/upload \\"
echo "  -F \"file=@test_image.png\" | jq"
echo ""
echo "# 响应示例："
echo "# {"
echo "#   \"success\": true,"
echo "#   \"fileId\": \"abc-123-def-456\","
echo "#   \"fileName\": \"test_image.png\","
echo "#   \"detectedImageType\": \"floor_plan\","
echo "#   \"message\": \"文件上传成功，已分割为 3 个文本块并建立索引\""
echo "# }"
echo ""

echo "=================================="
echo "支持的图片类型："
echo "  - cad: CAD工程制造图纸"
echo "  - floor_plan: 室内平面布置图"
echo "  - architecture: 架构图/流程图"
echo "  - technical_doc: 技术文档/工艺文件"
echo "=================================="
