import { FileSearch } from "lucide-react";

interface EmptyStateProps {
  type: "initial" | "no-results";
}

export function EmptyState({ type }: EmptyStateProps) {
  if (type === "initial") {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <FileSearch className="h-24 w-24 text-muted-foreground/30 mb-6" />
        <h3 className="text-[16px] mb-2">支持文本+图像/CAD 混合检索</h3>
        <p className="text-[13px] text-muted-foreground max-w-md">
          可直接拖入图像或 CAD 文件，系统将使用多模态大模型进行语义识别与检索
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <FileSearch className="h-24 w-24 text-muted-foreground/30 mb-6" />
      <h3 className="text-[16px] mb-2">未找到匹配项</h3>
      <p className="text-[13px] text-muted-foreground mb-4">
        试试放宽筛选或更换检索策略
      </p>
    </div>
  );
}
