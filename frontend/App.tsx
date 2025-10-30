import { useState } from "react";
import { Header } from "./components/Header";
import { SearchBar } from "./components/SearchBar";
import { ResultCard } from "./components/ResultCard";
import { PreviewPanel } from "./components/PreviewPanel";
import { EmptyState } from "./components/EmptyState";
import { IntelligentQA } from "./components/IntelligentQA";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { useSearch } from "./hooks";
import type { VLMModel, RetrievalStrategy } from "./types";
import { MessageSquare, Search as SearchIcon } from "lucide-react";

type AppMode = "search" | "qa";

export default function App() {
  const [mode, setMode] = useState<AppMode>("search");
  const [selectedModel, setSelectedModel] = useState<VLMModel>("gpt-4o");
  const [searchQuery, setSearchQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);

  const { results, isLoading, error, search } = useSearch();

  const handleSearch = async () => {
    setHasSearched(true);
    // 后端只实现了向量检索，固定使用 vector 策略
    await search(searchQuery, selectedModel, "vector");

    // Auto-select first result
    if (results.length > 0) {
      setSelectedResultId(results[0].id);
    }
  };

  const selectedResult = results.find((r) => r.id === selectedResultId);

  return (
    <div className="h-screen flex flex-col">
      <Header mode={mode} onModeChange={setMode} />

      <div className="flex-1 flex overflow-hidden">
        {/* 模式切换 - 智能问答或向量检索 */}
        {mode === "qa" ? (
          <div className="flex-1 w-full">
            <IntelligentQA />
          </div>
        ) : (
          <main className="flex-1 overflow-y-auto p-8">
            <div className="max-w-5xl mx-auto">
              <div className="mb-8">
                <div className="flex items-center justify-center gap-4 mb-6">
                  <h1 className="text-[28px] font-medium bg-gradient-to-r from-primary via-purple-400 to-primary bg-clip-text text-transparent">
                    多模态文档检索 RAG（VLM）
                  </h1>
                </div>

                <div className="flex items-center justify-center gap-3 mb-4">
                  <p className="text-[13px] text-muted-foreground/80 text-center max-w-2xl">
                    借助多模态大模型（VLM）对架构图、工程图纸、CAD 图等进行语义识别与检索
                  </p>
                </div>

                <div className="flex items-center justify-center gap-2 mb-6">
                  <Badge variant="secondary" className="text-[11px] px-3 py-1 bg-primary/10 text-primary border-primary/30">
                    产品级应用
                  </Badge>
                  <Badge variant="secondary" className="text-[11px] px-3 py-1 bg-purple-500/10 text-purple-400 border-purple-500/30">
                    LangChain
                  </Badge>
                  <Badge variant="secondary" className="text-[11px] px-3 py-1 bg-muted/30 border-border/50">
                    难度：⭐⭐⭐⭐⭐
                  </Badge>
                </div>

                <div className="flex items-center justify-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] text-muted-foreground">VLM 模型</span>
                    <Select value={selectedModel} onValueChange={setSelectedModel}>
                      <SelectTrigger className="w-[140px] h-9 bg-card/60 border-border/50 backdrop-blur-xl">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                        <SelectItem value="qwen-vl">Qwen-VL</SelectItem>
                        <SelectItem value="intern-vl">InternVL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[13px] text-muted-foreground">检索策略</span>
                    <Badge variant="secondary" className="text-[11px] px-3 py-1 bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                      向量检索
                    </Badge>
                  </div>
                </div>
              </div>
              <SearchBar
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                onSearch={handleSearch}
              />

            <div className="mt-8">
              {!hasSearched ? (
                <EmptyState type="initial" />
              ) : isLoading ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
                  <p className="text-[13px] text-muted-foreground">正在检索中...</p>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <p className="text-[14px] text-destructive mb-2">搜索出错</p>
                  <p className="text-[13px] text-muted-foreground">{error}</p>
                </div>
              ) : results.length === 0 ? (
                <EmptyState type="no-results" />
              ) : (
                <div className="space-y-4">
                  {results.map((result) => (
                    <ResultCard
                      key={result.id}
                      {...result}
                      isSelected={selectedResultId === result.id}
                      onSelect={() => setSelectedResultId(result.id)}
                    />
                  ))}
                  <div className="flex justify-center pt-4">
                    <Button variant="outline" className="text-[13px] border-border/50 hover:border-primary/30 hover:bg-primary/5">
                      加载更多结果
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
        )}

        {/* PreviewPanel 只在 search 模式下显示 */}
        {mode === "search" && hasSearched && selectedResult && (
          <PreviewPanel
            documentId={selectedResult.id}
            citationNumber={selectedResult.citationNumber}
            fileName={selectedResult.fileName}
            filePath={selectedResult.filePath}
            version={selectedResult.version}
            page={selectedResult.page || "N/A"}
            date={selectedResult.date}
            snippet={selectedResult.snippet}
            structuredData={selectedResult.structuredData}
            selectedModel={selectedModel}
            thumbnailUrl={selectedResult.thumbnailUrl}
            thumbnailType={selectedResult.thumbnailType}
          />
        )}
      </div>
    </div>
  );
}
