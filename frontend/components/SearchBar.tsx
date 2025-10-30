import { useRef, useState } from "react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Search, Upload, CheckCircle2, XCircle } from "lucide-react";
import { useUpload } from "../hooks";

interface SearchBarProps {
  searchQuery: string;
  setSearchQuery: (value: string) => void;
  onSearch: () => void;
}

export function SearchBar({ searchQuery, setSearchQuery, onSearch }: SearchBarProps) {
  const suggestions = ["CAD 尺寸", "结构解析", "流程图模块", "工艺参数", "版本对比"];
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isUploading, uploadDocument } = useUpload();
  const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const result = await uploadDocument(file);
      if (result) {
        setNotification({ type: 'success', message: `文件上传成功: ${result.fileName}` });
        setTimeout(() => setNotification(null), 4000);
      } else {
        setNotification({ type: 'error', message: '文件上传失败，请重试' });
        setTimeout(() => setNotification(null), 4000);
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="relative backdrop-blur-xl bg-card/60 rounded-2xl p-5 border border-border shadow-2xl shadow-primary/5">
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-primary/5 via-transparent to-purple-500/5 pointer-events-none" />

      {/* 通知弹窗 */}
      {notification && (
        <div className={`absolute top-0 left-1/2 -translate-x-1/2 -translate-y-full mb-2 z-50 animate-in slide-in-from-top-2 duration-300 ${
          notification.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-destructive/10 border-destructive/30 text-destructive'
        } backdrop-blur-xl border rounded-xl px-6 py-3 shadow-xl flex items-center gap-3`}>
          {notification.type === 'success' ? (
            <CheckCircle2 className="h-5 w-5" />
          ) : (
            <XCircle className="h-5 w-5" />
          )}
          <span className="text-[14px] font-medium">{notification.message}</span>
        </div>
      )}

      <div className="relative flex gap-3 mb-4">
        <div className="flex-1 relative">
          <Input
            placeholder="用自然语言提问，例如：'查询电机支架 CAD 的孔径与中心距'"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch()}
            className="h-11 pr-4 bg-transparent border-border/60 focus:border-primary/60 focus:ring-primary/20 text-[15px] font-semibold text-white placeholder:text-gray-400 placeholder:font-normal backdrop-blur-sm"
          />
        </div>
        <Button onClick={onSearch} className="h-11 px-6 bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 shadow-lg shadow-primary/20 border border-primary/20">
          <Search className="h-4 w-4 mr-2" />
          检索
        </Button>
        <Button
          variant="outline"
          className="h-11 px-5 backdrop-blur-xl bg-card/40 border-border/60 hover:bg-primary/5 hover:border-primary/40 transition-all duration-200 group relative overflow-hidden"
          onClick={handleUploadClick}
          disabled={isUploading}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          {isUploading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2 relative z-10" />
              <span className="relative z-10 text-[13px] font-medium">上传中...</span>
            </>
          ) : (
            <>
              <Upload className="h-4 w-4 mr-2 relative z-10 group-hover:text-primary transition-colors" />
              <span className="relative z-10 text-[13px] font-medium">上传</span>
            </>
          )}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf,.dwg,.dxf,.step,.stp"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      <div className="relative flex items-center gap-2 flex-wrap">
        <span className="text-[12px] text-gray-300">快捷查询：</span>
        {suggestions.map((suggestion) => (
          <Badge
            key={suggestion}
            variant="outline"
            className="cursor-pointer text-[12px] px-3 py-1 border-border/60 text-gray-200 hover:border-primary/60 hover:bg-primary/10 hover:text-white transition-all"
            onClick={() => setSearchQuery(suggestion)}
          >
            {suggestion}
          </Badge>
        ))}
      </div>

      <div className="relative mt-4 space-y-1 text-[11px] text-gray-400">
        <p>• 工程制造图纸解读：支持结构、尺寸与参数解析与检索</p>
        <p>• 研发架构图理解：识别架构/流程图语义并进行检索</p>
        <p>• 工业技术档案：支持语义检索与设计版本图像识别</p>
      </div>
    </div>
  );
}
