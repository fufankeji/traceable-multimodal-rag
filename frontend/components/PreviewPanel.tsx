import { useState } from "react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Separator } from "../ui/separator";
import { Eye, EyeOff, ZoomIn, Download, ExternalLink, Copy, Send } from "lucide-react";
import { useFollowUpQuestion } from "../hooks";
import type { VLMModel, StructuredData } from "../types";

interface PreviewPanelProps {
  documentId: string;
  citationNumber: number;
  fileName: string;
  filePath: string;
  version: string;
  page: string;
  date: string;
  snippet: string;
  structuredData: StructuredData[];
  selectedModel: VLMModel;
  thumbnailUrl?: string;
  thumbnailType?: "cad" | "pdf" | "image";
}

export function PreviewPanel({
  documentId,
  citationNumber,
  fileName,
  filePath,
  version,
  page,
  date,
  snippet,
  structuredData,
  selectedModel,
  thumbnailUrl,
  thumbnailType,
}: PreviewPanelProps) {
  const [showHighlight, setShowHighlight] = useState(true);
  const [followUpQuestion, setFollowUpQuestion] = useState("");

  const { qaHistory, isAsking, askQuestion } = useFollowUpQuestion();

  const handleAskQuestion = async () => {
    if (!followUpQuestion.trim()) return;

    await askQuestion(documentId, followUpQuestion, selectedModel);
    setFollowUpQuestion("");
  };

  return (
    <aside className="w-[420px] backdrop-blur-xl bg-card/60 border-l border-border/50 overflow-y-auto shadow-2xl shadow-black/20">
      <div className="sticky top-0 backdrop-blur-xl bg-gradient-to-r from-card/90 to-card/80 border-b border-border/50 px-6 py-4 z-10">
        <div className="flex items-center justify-between">
          <h3 className="text-[16px] font-semibold text-white flex items-center gap-2">
            预览与溯源
            <Badge variant="secondary" className="text-[11px] px-2 py-0.5 bg-primary/10 text-primary border-primary/30">
              [{citationNumber}]
            </Badge>
          </h3>
        </div>
      </div>

      <div className="p-5 space-y-5">
        <div>
          <div className="bg-muted/20 rounded-xl border border-border/30 relative overflow-hidden backdrop-blur-sm">
            {thumbnailType === "image" && thumbnailUrl ? (
              // 图片类型：显示缩略图
              <div className="aspect-square flex items-center justify-center">
                <img
                  src={thumbnailUrl}
                  alt={fileName}
                  className="w-full h-full object-contain"
                />
                {showHighlight && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-24 h-24 border-2 border-primary bg-primary/10 rounded shadow-lg shadow-primary/30 animate-pulse" />
                  </div>
                )}
              </div>
            ) : thumbnailType === "pdf" ? (
              // PDF类型：显示Markdown文本预览
              <div className="p-4 max-h-[500px] overflow-y-auto scrollbar-thin">
                <div className="text-[11px] leading-relaxed whitespace-pre-wrap prose prose-sm prose-invert max-w-none">
                  {(() => {
                    // 简单的Markdown链接渲染
                    const renderMarkdown = (text: string) => {
                      const parts: JSX.Element[] = [];
                      let lastIndex = 0;
                      const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
                      let match;

                      while ((match = linkRegex.exec(text)) !== null) {
                        if (match.index > lastIndex) {
                          parts.push(<span key={`text-${lastIndex}`}>{text.substring(lastIndex, match.index)}</span>);
                        }
                        parts.push(
                          <a
                            key={`link-${match.index}`}
                            href={match[2]}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300 underline"
                          >
                            {match[1]}
                          </a>
                        );
                        lastIndex = match.index + match[0].length;
                      }

                      if (lastIndex < text.length) {
                        parts.push(<span key={`text-${lastIndex}`}>{text.substring(lastIndex)}</span>);
                      }

                      return parts.length > 0 ? parts : text;
                    };

                    // 显示完整的snippet内容
                    return <>{renderMarkdown(snippet)}</>;
                  })()}
                </div>
              </div>
            ) : (
              // CAD等其他类型
              <div className="aspect-square flex items-center justify-center text-center text-muted-foreground">
                <div>
                  <div className="text-[11px] mb-2">CAD 图纸预览</div>
                  <div className="text-[10px]">{fileName}</div>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2 mt-3">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 text-[11px] h-8"
              onClick={() => setShowHighlight(!showHighlight)}
            >
              {showHighlight ? (
                <>
                  <EyeOff className="h-3.5 w-3.5 mr-1" />
                  隐藏高亮
                </>
              ) : (
                <>
                  <Eye className="h-3.5 w-3.5 mr-1" />
                  显示高亮
                </>
              )}
            </Button>
            <Button variant="outline" size="sm" className="text-[11px] h-8 px-3">
              <ZoomIn className="h-3.5 w-3.5" />
            </Button>
            <Button variant="outline" size="sm" className="text-[11px] h-8 px-3">
              <Download className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        <div>
          <h4 className="text-[14px] font-medium mb-3 text-white">引用片段</h4>
          <div className="bg-muted/30 rounded-xl p-4 text-[12px] border border-border/30 backdrop-blur-sm">
            <div className="mb-2 whitespace-pre-wrap break-words text-[11px] leading-relaxed overflow-x-auto prose prose-sm prose-invert max-w-none">
              {(() => {
                // 简单的Markdown渲染：将链接转换为可点击的<a>标签
                const renderMarkdown = (text: string) => {
                  // 匹配 [文本](URL) 格式的链接
                  const parts: JSX.Element[] = [];
                  let lastIndex = 0;
                  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
                  let match;

                  while ((match = linkRegex.exec(text)) !== null) {
                    // 添加链接前的文本
                    if (match.index > lastIndex) {
                      parts.push(<span key={`text-${lastIndex}`}>{text.substring(lastIndex, match.index)}</span>);
                    }
                    // 添加链接
                    parts.push(
                      <a
                        key={`link-${match.index}`}
                        href={match[2]}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline"
                      >
                        {match[1]}
                      </a>
                    );
                    lastIndex = match.index + match[0].length;
                  }

                  // 添加剩余文本
                  if (lastIndex < text.length) {
                    parts.push(<span key={`text-${lastIndex}`}>{text.substring(lastIndex)}</span>);
                  }

                  return parts.length > 0 ? parts : text;
                };

                try {
                  // 尝试解析 snippet 中的 JSON 部分
                  const jsonMatch = snippet.match(/\{[^]*\}/);
                  if (jsonMatch) {
                    const textBefore = snippet.substring(0, jsonMatch.index);
                    const jsonPart = JSON.parse(jsonMatch[0]);
                    const textAfter = snippet.substring(jsonMatch.index! + jsonMatch[0].length);
                    return (
                      <>
                        {renderMarkdown(textBefore)}
                        <div className="bg-black/20 rounded p-2 my-2 font-mono text-[10px]">
                          {JSON.stringify(jsonPart, null, 2)}
                        </div>
                        {renderMarkdown(textAfter)}
                      </>
                    );
                  }
                } catch (e) {
                  // JSON 解析失败，直接渲染Markdown
                }
                return <>{renderMarkdown(snippet)}</>;
              })()}
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-[11px] px-2"
              onClick={() => navigator.clipboard.writeText(snippet)}
            >
              <Copy className="h-3 w-3 mr-1" />
              复制引用
            </Button>
          </div>
        </div>

        <Separator />

        <div>
          <h4 className="text-[14px] font-medium mb-3 text-white">来源信息（Provenance）</h4>
          <div className="bg-gradient-to-br from-muted/30 to-muted/20 rounded-xl p-4 space-y-3 text-[12px] border border-border/30 backdrop-blur-sm shadow-lg shadow-black/5">
            <div className="flex gap-3">
              <span className="text-gray-400 w-16 flex-shrink-0">文件：</span>
              <span className="flex-1 break-all text-white font-medium">{fileName}</span>
            </div>
            <div className="flex gap-3">
              <span className="text-gray-400 w-16 flex-shrink-0">路径：</span>
              <span className="flex-1 break-all text-[11px] text-gray-300">{filePath}</span>
            </div>
            <div className="flex gap-3">
              <span className="text-gray-400 w-16 flex-shrink-0">版本：</span>
              <span className="flex-1 text-gray-200">{version}</span>
            </div>
            <div className="flex gap-3">
              <span className="text-gray-400 w-16 flex-shrink-0">页码：</span>
              <span className="flex-1 text-gray-200">{page}</span>
            </div>
            <div className="flex gap-3">
              <span className="text-gray-400 w-16 flex-shrink-0">时间：</span>
              <span className="flex-1 text-gray-200">{date}</span>
            </div>
            <div className="pt-2 border-t border-border/30">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-[11px] text-primary hover:text-primary hover:bg-primary/10 w-full justify-start"
              >
                <ExternalLink className="h-3.5 w-3.5 mr-2" />
                在新窗口打开原文/原图
              </Button>
            </div>
          </div>
        </div>

        <div>
          <h4 className="text-[14px] font-medium mb-3 text-white">结构化解析</h4>
          <div className="space-y-2">
            {structuredData.length > 0 ? (
              structuredData.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between bg-muted/20 rounded-lg px-3 py-2.5 text-[12px] border border-border/30 backdrop-blur-sm hover:bg-muted/30 transition-colors"
                >
                  <span className="text-gray-400">{item.label}：</span>
                  <span className="text-white font-medium">{item.value}</span>
                </div>
              ))
            ) : (
              <div className="bg-muted/20 rounded-lg px-3 py-3 text-[12px] border border-border/30 backdrop-blur-sm text-center">
                <span className="text-gray-400">暂无结构化信息</span>
              </div>
            )}
          </div>
          <p className="text-[10px] text-gray-500 mt-3">
            由 VLM 智能解析，仅供参考
          </p>
        </div>

        <Separator />

        <div>
          <h4 className="text-[14px] font-medium mb-3 text-white">追问与深度分析</h4>

          {qaHistory.length > 0 && (
            <div className="space-y-3 mb-4 max-h-[300px] overflow-y-auto">
              {qaHistory.map((qa, i) => (
                <div key={i} className="space-y-2">
                  <div className="bg-primary/10 rounded-lg px-3 py-2.5 text-[12px] border border-primary/30">
                    <strong className="text-primary">问：</strong>{" "}
                    <span className="text-white">{qa.question}</span>
                  </div>
                  <div className="bg-muted/30 rounded-lg px-3 py-2.5 text-[12px] border border-border/30">
                    <strong className="text-emerald-400">答：</strong>{" "}
                    <span className="text-gray-200">{qa.answer}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <Input
              placeholder="继续追问，例如：'中心距是否满足 v1.2 工艺规范？'"
              value={followUpQuestion}
              onChange={(e) => setFollowUpQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !isAsking && handleAskQuestion()}
              disabled={isAsking}
              className="text-[12px] h-10 bg-transparent border-border/60 focus:border-primary/60 text-white placeholder:text-gray-500"
            />
            <Button
              size="sm"
              className="h-10 px-4 bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 shadow-lg shadow-primary/20"
              onClick={handleAskQuestion}
              disabled={isAsking}
            >
              {isAsking ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </aside>
  );
}
