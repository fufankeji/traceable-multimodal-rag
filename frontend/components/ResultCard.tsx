import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { FileText, Copy } from "lucide-react";

interface ResultCardProps {
  id: string;
  fileName: string;
  filePath: string;
  fileType: string;
  similarity: number;
  page?: string;
  date: string;
  snippet: string;
  citationNumber: number;
  isSelected: boolean;
  onSelect: () => void;
  thumbnailType: "cad" | "pdf" | "image";
  thumbnailUrl?: string;
}

export function ResultCard({
  fileName,
  filePath,
  fileType,
  similarity,
  page,
  date,
  snippet,
  citationNumber,
  isSelected,
  onSelect,
  thumbnailType,
  thumbnailUrl,
}: ResultCardProps) {
  return (
    <div
      className={`relative backdrop-blur-xl bg-card/60 rounded-2xl p-5 border transition-all cursor-pointer group ${
        isSelected 
          ? "border-primary/50 shadow-2xl shadow-primary/10" 
          : "border-border/30 hover:border-primary/30 shadow-lg shadow-black/5"
      }`}
      onClick={onSelect}
    >
      {isSelected && (
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-primary/5 via-transparent to-purple-500/5 pointer-events-none" />
      )}
      <div className="relative flex gap-4">
        <div className="w-[120px] h-[120px] flex-shrink-0 bg-muted/30 rounded-xl flex items-center justify-center border border-border/30 backdrop-blur-sm overflow-hidden">
          {(thumbnailType === "image" || thumbnailType === "pdf") && thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt={fileName}
              className="w-full h-full object-cover"
              onError={(e) => {
                // 图片加载失败时显示占位图标
                e.currentTarget.style.display = 'none';
                const iconType = thumbnailType === "pdf" ? "PDF" : "图片";
                e.currentTarget.parentElement!.innerHTML = `<div class="text-center"><svg class="h-10 w-10 text-muted-foreground mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg><span class="text-[11px] text-muted-foreground">${iconType}</span></div>`;
              }}
            />
          ) : thumbnailType === "cad" ? (
            <div className="text-center">
              <FileText className="h-10 w-10 text-muted-foreground mx-auto mb-2" />
              <span className="text-[11px] text-muted-foreground">CAD</span>
            </div>
          ) : thumbnailType === "pdf" ? (
            <div className="text-center">
              <FileText className="h-10 w-10 text-muted-foreground mx-auto mb-2" />
              <span className="text-[11px] text-muted-foreground">PDF</span>
            </div>
          ) : (
            <div className="text-center">
              <FileText className="h-10 w-10 text-muted-foreground mx-auto mb-2" />
              <span className="text-[11px] text-muted-foreground">图片</span>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <h4 className="text-[15px] truncate mb-1 text-foreground/90">{fileName}</h4>
              <p className="text-[12px] text-muted-foreground/70 truncate">
                {filePath}
              </p>
            </div>
            <Badge
              variant="secondary"
              className="ml-2 text-[11px] px-2 py-0.5 flex-shrink-0 bg-primary/10 text-primary border-primary/30"
            >
              [{citationNumber}]
            </Badge>
          </div>

          <div className="flex flex-wrap gap-2 mb-3">
            <Badge variant="outline" className="text-[11px] px-2 py-0.5 border-border/50">
              {fileType}
            </Badge>
            <Badge
              variant="default"
              className="text-[11px] px-2 py-0.5 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border-emerald-500/30"
            >
              相似度 {similarity}%
            </Badge>
            {page && (
              <Badge variant="outline" className="text-[11px] px-2 py-0.5 border-border/50">
                {page}
              </Badge>
            )}
            <Badge variant="outline" className="text-[11px] px-2 py-0.5 border-border/50">
              {date}
            </Badge>
          </div>

          <p className="text-[13px] text-foreground/80 line-clamp-2 mb-3">
            {snippet.split("").map((char, i) => {
              const highlightWords = ["孔径", "中心距", "材质", "消息队列"];
              const shouldHighlight = highlightWords.some((word) =>
                snippet.substring(i).startsWith(word)
              );
              return shouldHighlight ? (
                <mark
                  key={i}
                  className="bg-yellow-200 text-foreground px-0.5 rounded"
                >
                  {char}
                </mark>
              ) : (
                char
              );
            })}
          </p>

          <div className="flex items-center gap-2">
            <Button size="sm" className="h-8 text-[12px] bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 shadow-lg shadow-primary/20 border border-primary/20">
              预览与溯源
            </Button>
            <Button variant="outline" size="sm" className="h-8 text-[12px] border-border/50 hover:border-primary/30 hover:bg-primary/5">
              定位原文/原图
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-primary/10 hover:text-primary">
              <Copy className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
