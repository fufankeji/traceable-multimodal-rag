
import re, json
from typing import List, Dict, Tuple
from langchain_text_splitters import MarkdownTextSplitter

# ========== 1) 基础：按 {{第N页}} 分页 ==========
def split_pages(md_text: str) -> Tuple[str, List[Tuple[int, str]]]:
    pattern = re.compile(r"\{\{第(\d+)页\}\}")
    parts = pattern.split(md_text)
    page_blocks: List[Tuple[int, str]] = []
    # 处理页标前的前缀（若有）
    prefix = parts[0]
    if prefix.strip():
        page_blocks.append((1, prefix))
    # 解析 (page_no, content) 对
    for i in range(1, len(parts), 2):
        page_no = int(parts[i])
        content = parts[i + 1]
        page_blocks.append((page_no, content))
    # 去掉页标后的"全文"
    full_text_clean = "".join(block for _, block in page_blocks)
    return full_text_clean, page_blocks

# ========== 2) 主流程：MarkdownTextSplitter 切分 ==========
def chunk_markdown_only_with_cross_page(
    md_text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 80,
    merge_tolerance: float = 0.2,
    max_page_span: int = 3,
    bridge_span: int = 150
) -> Dict:
    """
    改进版：仅使用 MarkdownTextSplitter，合并时以chunk_size为目标
    
    参数:
        md_text: 输入的markdown文本
        chunk_size: 目标chunk大小
        chunk_overlap: 切分时的重叠长度
        merge_tolerance: 合并时允许超出chunk_size的比例（默认20%）
        max_page_span: 单个chunk允许跨越的最大页数（默认3页，0表示不限制）
        bridge_span: 跨页桥接片段长度
        
    输出：
    {
      "full_text": <去页标全文>,
      "chunks": [
        {
          "page_start": int, "page_end": int, "pages": [..],
          "text": str,
          "text_length": int,
          "continued": bool,
          "cross_page_bridge": bool,
          "is_table_like": bool
        }, ...
      ]
    }
    """
    full_text_clean, page_blocks = split_pages(md_text)

    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # 第一步：逐页切分 - 这些是"最小不可分单元"
    raw_chunks: List[Dict] = []
    for page_no, page_text in page_blocks:
        sub_texts = splitter.split_text(page_text)
        for sub in sub_texts:
            t = sub.strip()
            raw_chunks.append({
                "page_start": page_no,
                "page_end": page_no,
                "pages": [page_no],
                "text": t,
                "text_length": len(t),
                "continued": False,
                "cross_page_bridge": False,
                # 简易表格判断：以竖线开头或包含表格行分隔
                "is_table_like": t.startswith("|") or "\n|" in t
            })

    # 第二步：改进的合并策略 - 以chunk_size为目标
    stitched = stitch_chunks_aggressively(raw_chunks, chunk_size, merge_tolerance, max_page_span)

    # 第三步：可选——添加跨页桥接片段
    with_bridges = add_cross_page_bridges(stitched, bridge_span=bridge_span)

    return {"full_text": full_text_clean, "chunks": with_bridges}

# ========== 3) 启发式合并规则 ==========
SENT_END = "。！？.!?"
HEADING_PAT = re.compile(r"^\s{0,3}#{1,6}\s")          # # / ## / ### 标题
HR_PAT = re.compile(r"^\s{0,3}(-{3,}|\*{3,}|_{3,})\s*$") # --- 或 *** 分隔线
LIST_OR_CODE_START = re.compile(r"^\s{0,3}(\*|\-|\+|\d+\.)\s|^\s{0,3}```")  # 列表项或代码围栏

def looks_like_block_start(s: str) -> bool:
    """判断下块是否像新段/新节的开始（避免误并）"""
    if not s.strip():
        return False
    head = s.strip().splitlines()[0]
    return (
        HEADING_PAT.match(head) is not None or
        HR_PAT.match(head) is not None or
        LIST_OR_CODE_START.match(head) is not None
    )

def ends_with_sentence_break(s: str) -> bool:
    """判断文本是否以句子结束符结尾"""
    s = s.rstrip()
    return len(s) > 0 and s[-1] in SENT_END

def stitch_chunks_aggressively(chunks: List[Dict], chunk_size: int, tolerance: float = 0.2, max_page_span: int = 3) -> List[Dict]:
    """
    改进的合并策略：目标是让chunk尽量接近chunk_size，但不破坏最小单元
    
    对于没有标题信息的纯文本切分，使用启发式规则：
    1. 同页内，合并后不超过容忍范围 -> 合并
    2. 相邻页：
       - 合并后 <= chunk_size 且符合语义连续性 -> 合并
       - 合并后在容忍范围内且是表格或短块 -> 合并
    3. 跨页数不超过 max_page_span（0表示不限制）
    """
    if not chunks:
        return []
    
    stitched = [chunks[0]]
    max_allowed = int(chunk_size * (1 + tolerance))
    
    for curr in chunks[1:]:
        prev = stitched[-1]
        combined_len = len(prev["text"]) + len(curr["text"])
        
        should_merge = False
        
        # 检查页数跨度限制
        if max_page_span > 0:
            # 计算合并后的页数跨度
            potential_page_span = curr["page_end"] - prev["page_start"] + 1
            if potential_page_span > max_page_span:
                # 超过最大页数跨度，不合并
                stitched.append(curr)
                continue
        
        # 条件1: 同一页内
        if prev["page_end"] == curr["page_start"]:
            # 同页内更激进地合并
            if combined_len <= max_allowed:
                should_merge = True
        
        # 条件2: 相邻页
        elif curr["pages"][0] - prev["pages"][-1] == 1:
            if combined_len <= chunk_size:
                # 不超过目标大小，检查语义连续性
                # 规则A: 表格两端
                if prev.get("is_table_like") and curr.get("is_table_like"):
                    should_merge = True
                # 规则B: 上一块未断句 + 下一块不像新块开始
                elif (not ends_with_sentence_break(prev["text"])) and (not looks_like_block_start(curr["text"])):
                    should_merge = True
                # 规则C: 上一块太短（疑似被截断）
                elif len(prev["text"]) < chunk_size * 0.3 and (not looks_like_block_start(curr["text"])):
                    should_merge = True
            elif combined_len <= max_allowed:
                # 略超目标但在容忍范围内
                # 表格优先合并（避免截断）
                if prev.get("is_table_like") and curr.get("is_table_like"):
                    should_merge = True
                # 当前块很小
                elif len(curr["text"]) < chunk_size * 0.3:
                    should_merge = True
        
        if should_merge:
            # 执行合并
            prev["text"] = prev["text"].rstrip() + "\n" + curr["text"].lstrip()
            prev["text_length"] = len(prev["text"])
            prev["page_end"] = curr["page_end"]
            prev["pages"] = sorted(set(prev["pages"] + curr["pages"]))
            prev["continued"] = True
            prev["is_table_like"] = prev.get("is_table_like") and curr.get("is_table_like")
        else:
            stitched.append(curr)
    
    return stitched

# ========== 4) 跨页桥接片段 ==========
def add_cross_page_bridges(chunks: List[Dict], bridge_span: int = 150) -> List[Dict]:
    """
    为跨页边界添加"小桥"chunk，便于检索跨页语义
    """
    out: List[Dict] = []
    for i, c in enumerate(chunks):
        out.append(c)
        if i + 1 < len(chunks):
            n = chunks[i + 1]
            # 只在页码相邻时添加桥
            if n["pages"][0] - c["pages"][-1] == 1:
                tail = c["text"][-bridge_span:] if len(c["text"]) >= bridge_span else c["text"]
                head = n["text"][0:bridge_span] if len(n["text"]) >= bridge_span else n["text"]
                if tail.strip() and head.strip():
                    bridge_text = tail + "\n" + head
                    out.append({
                        "page_start": c["page_end"],
                        "page_end": n["page_start"],
                        "pages": [c["page_end"], n["page_start"]],
                        "text": bridge_text,
                        "text_length": len(bridge_text),
                        "continued": True,
                        "cross_page_bridge": True,
                        "is_table_like": c.get("is_table_like") or n.get("is_table_like")
                    })
    return out

# ========== 5) DEMO ==========
if __name__ == "__main__":
    md_path = "/home/data/nongwa/workspace/Information-Extraction/unified/output/阿里开发手册-泰山版_1/accurate_text.md"
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    data = chunk_markdown_only_with_cross_page(
        md_text,
        chunk_size=600,
        chunk_overlap=80,
        merge_tolerance=0.2,
        bridge_span=150
    )
    
    print("=" * 80)
    print(f"总chunk数: {len(data['chunks'])}")
    print("=" * 80)
    
    for i, chunk in enumerate(data["chunks"], 1):
        print(f"\n[Chunk {i}]")
        print(f"页码: {chunk['pages']}")
        print(f"长度: {chunk['text_length']}")
        print(f"跨页: {chunk['continued']}")
        print(f"桥接: {chunk['cross_page_bridge']}")
        print(f"表格: {chunk['is_table_like']}")
        print(f"文本预览: {chunk['text'][:100]}...")
        print("-" * 80)