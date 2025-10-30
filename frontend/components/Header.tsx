import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Zap, Sparkles, MessageSquare, Search } from "lucide-react";

interface HeaderProps {
  mode?: "search" | "qa";
  onModeChange?: (mode: "search" | "qa") => void;
}

export function Header({ mode = "search", onModeChange }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-card/40 border-b border-border px-8 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center shadow-lg shadow-primary/20">
            <Zap className="h-5 w-5 text-primary-foreground" />
          </div>
          <h1 className="text-[20px] font-medium bg-gradient-to-r from-primary via-purple-400 to-primary bg-clip-text text-transparent">
            赋范空间公开课
          </h1>
        </div>

        <div className="flex items-center gap-4">
          {/* 模式切换按钮 */}
          {onModeChange && (
            <div className="flex items-center gap-2 p-1 bg-muted/30 rounded-lg border border-border/50">
              <Button
                variant={mode === "search" ? "default" : "ghost"}
                size="sm"
                className={`h-8 px-4 text-[12px] ${
                  mode === "search"
                    ? "bg-gradient-to-r from-primary to-purple-500 shadow-lg shadow-primary/20"
                    : "hover:bg-muted/50"
                }`}
                onClick={() => onModeChange("search")}
              >
                <Search className="h-3.5 w-3.5 mr-1.5" />
                向量检索
              </Button>
              <Button
                variant={mode === "qa" ? "default" : "ghost"}
                size="sm"
                className={`h-8 px-4 text-[12px] ${
                  mode === "qa"
                    ? "bg-gradient-to-r from-primary to-purple-500 shadow-lg shadow-primary/20"
                    : "hover:bg-muted/50"
                }`}
                onClick={() => onModeChange("qa")}
              >
                <MessageSquare className="h-3.5 w-3.5 mr-1.5" />
                智能问答
              </Button>
            </div>
          )}

          <Button className="h-10 px-6 bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 text-primary-foreground shadow-lg shadow-primary/20 border border-primary/20">
            <Sparkles className="h-4 w-4 mr-2" />
            点击获取课程优惠
          </Button>
        </div>
      </div>
    </header>
  );
}
