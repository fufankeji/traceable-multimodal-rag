import { useState, useRef } from "react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { Search, Loader2, MessageSquare, Upload, FileImage, ExternalLink } from "lucide-react";
import { useIntelligentQA } from "../hooks/useIntelligentQA";
import { useUpload } from "../hooks/useUpload";
import { AnswerDisplay } from "./AnswerDisplay";
import { EmptyState } from "./EmptyState";


export function IntelligentQA() {
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");  // 保存已提交的问题
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { answer, sources, confidence, queryType, isLoading, error: qaError, ask, clearAnswer } = useIntelligentQA();
  const { uploadDocument, isUploading, error: uploadError } = useUpload();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!uploadedFile) return;

    try {
      await uploadDocument(uploadedFile);
      // 上传成功后，可以提示用户提问
      console.log("✅ 文件上传成功，现在可以提问了");
    } catch (err) {
      console.error("❌ 文件上传失败", err);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    // 保存当前问题
    setSubmittedQuestion(question);

    // 如果有待上传的文件，先上传
    if (uploadedFile && !isUploading) {
      await handleUpload();
    }

    await ask(question);
  };

  const handleClear = () => {
    setQuestion("");
    setSubmittedQuestion("");  // 同时清空已提交的问题
    setUploadedFile(null);
    clearAnswer();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="h-full flex overflow-hidden">
      {/* 主内容区域 - 左侧 */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto space-y-8">
          {/* 标题 */}
          <div className="flex items-center justify-center gap-3">
            <MessageSquare className="h-6 w-6 text-primary" />
            <h2 className="text-xl font-semibold text-foreground/90">智能问答</h2>
          </div>

          {/* 如果有答案，显示答案 */}
          {!isLoading && answer && queryType ? (
            <AnswerDisplay
              question={submittedQuestion}
              answer={answer}
              sources={sources}
              confidence={confidence}
              queryType={queryType}
              onNewQuestion={handleClear}  // 传递重新提问回调
            />
          ) : isLoading ? (
          /* 加载状态 */
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
            <p className="text-[14px] text-muted-foreground">正在分析您的问题...</p>
          </div>
        ) : (
          /* 主要的输入区域 - 居中显示 */
          <div className="space-y-6">
            {/* 错误提示 */}
            {(qaError || uploadError) && (
              <div className="backdrop-blur-xl bg-destructive/10 border border-destructive/30 rounded-2xl p-4">
                <p className="text-[13px] text-destructive">{qaError || uploadError}</p>
              </div>
            )}

            {/* 文件上传区域 */}
            <div className="backdrop-blur-xl bg-card/40 border border-border/50 rounded-2xl p-6 shadow-xl">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,.pdf,.dwg,.dxf"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="flex flex-col items-center justify-center gap-4 cursor-pointer hover:bg-primary/5 p-8 rounded-xl transition-all duration-200 border-2 border-dashed border-border/50 hover:border-primary/40 min-h-[220px] group"
                >
                  {uploadedFile ? (
                    <>
                      <div className="relative">
                        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full"></div>
                        <FileImage className="relative h-16 w-16 text-primary" />
                      </div>
                      <div className="text-center space-y-2">
                        <p className="text-[15px] font-medium text-foreground/90">
                          已选择文件
                        </p>
                        <p className="text-[13px] text-muted-foreground bg-muted/30 px-4 py-2 rounded-lg border border-border/30 max-w-xs truncate">
                          {uploadedFile.name}
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.preventDefault();
                          setUploadedFile(null);
                          if (fileInputRef.current) {
                            fileInputRef.current.value = "";
                          }
                        }}
                        className="h-9 px-4 text-[13px] border-border/50 hover:border-destructive/40 hover:bg-destructive/5 hover:text-destructive transition-colors"
                      >
                        移除文件
                      </Button>
                    </>
                  ) : (
                    <>
                      <div className="relative">
                        <div className="absolute inset-0 bg-primary/10 blur-2xl rounded-full group-hover:bg-primary/20 transition-colors"></div>
                        <Upload className="relative h-14 w-14 text-muted-foreground group-hover:text-primary transition-colors" />
                      </div>
                      <div className="text-center space-y-2">
                        <p className="text-[16px] text-foreground/90 font-medium">
                          点击上传图像或 CAD 文件
                        </p>
                        <p className="text-[13px] text-muted-foreground">
                          支持 PNG, JPG, PDF, DWG, DXF 格式
                        </p>
                        <p className="text-[12px] text-muted-foreground/60">
                          或拖拽文件到此区域
                        </p>
                      </div>
                    </>
                  )}
                </label>
                {isUploading && (
                  <div className="flex items-center justify-center gap-3 mt-6 p-4 bg-primary/5 border border-primary/20 rounded-xl">
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    <span className="text-[13px] text-foreground/80 font-medium">正在上传并分析文件...</span>
                  </div>
                )}
                {uploadError && (
                  <div className="mt-6 p-4 bg-destructive/10 border border-destructive/30 rounded-xl text-[13px] text-destructive text-center">
                    {uploadError}
                  </div>
                )}
              </div>

              {/* 问题输入框 */}
              <form onSubmit={handleAsk}>
                <div className="relative">
                  <Input
                    type="text"
                    placeholder="请输入您的问题，例如：这张图中有几个卧室？总面积是多少？"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={isLoading || isUploading}
                    className="h-14 pl-12 pr-32 text-[15px] backdrop-blur-xl bg-transparent border-border/60 rounded-2xl shadow-lg focus-visible:ring-2 focus-visible:ring-primary/30 text-white font-semibold placeholder:text-gray-400 placeholder:font-normal"
                  />
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2">
                    <Button
                      type="submit"
                      size="sm"
                      disabled={!question.trim() || isLoading || isUploading}
                      className="h-10 px-6 text-[13px] bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 shadow-lg shadow-primary/20"
                    >
                      {isLoading || isUploading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          {isUploading ? "上传中..." : "提问中..."}
                        </>
                      ) : (
                        "提问"
                      )}
                    </Button>
                  </div>
                </div>
              </form>

              {/* 示例问题 */}
              <div className="flex flex-wrap gap-2 justify-center">
                <span className="text-[12px] text-gray-300">试试这些问题：</span>
                {[
                  "这张图中有几个卧室？",
                  "总面积是多少？",
                  "建筑的长度和宽度是多少？",
                  "主卧的面积是多少？",
                ].map((exampleQuestion) => (
                  <Button
                    key={exampleQuestion}
                    variant="outline"
                    size="sm"
                    className="h-7 text-[11px] border-border/60 text-gray-200 hover:border-primary/40 hover:bg-primary/10 hover:text-white"
                    onClick={() => setQuestion(exampleQuestion)}
                  >
                    {exampleQuestion}
                  </Button>
                ))}
              </div>

              {/* 空状态说明 */}
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted/30 mb-4">
                  <Search className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-[16px] font-medium text-white mb-2">
                  支持文本+图像/CAD 混合检索
                </h3>
                <p className="text-[13px] text-gray-400 max-w-md mx-auto">
                  可直接输入图像或 CAD 文件，系统将使用多模态大模型进行语义识别与检索
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* 右侧溯源面板 - 仅在有答案和来源时显示 */}
      {!isLoading && answer && sources.length > 0 && (
        <aside className="w-[420px] backdrop-blur-xl bg-card/60 border-l border-border/50 overflow-y-auto shadow-2xl shadow-black/20">
          <div className="sticky top-0 backdrop-blur-xl bg-gradient-to-r from-card/90 to-card/80 border-b border-border/50 px-6 py-4 z-10">
            <div className="flex items-center justify-between">
              <h3 className="text-[16px] font-semibold text-white flex items-center gap-2">
                来源文档
              </h3>
            </div>
          </div>

          <div className="p-5 space-y-3">
            {sources.map((source, index) => (
              <div
                key={source.file_id}
                className="group backdrop-blur-xl bg-card/40 border border-border/30 rounded-2xl p-4 hover:border-primary/40 hover:bg-primary/5 transition-all cursor-pointer shadow-lg"
              >
                <div className="flex items-start gap-2 mb-3">
                  <Badge
                    variant="secondary"
                    className="text-[10px] px-2 py-1 flex-shrink-0 bg-primary/10 text-primary border-primary/30"
                  >
                    [{index + 1}]
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <h5 className="text-[13px] font-medium text-white mb-2">
                      {source.file_name}
                    </h5>
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="outline" className="text-[10px] px-2 py-0.5 border-border/50 text-gray-300">
                        {source.file_type}
                      </Badge>
                      <Badge
                        variant="default"
                        className="text-[10px] px-2 py-0.5 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border-emerald-500/30"
                      >
                        相似度 {Math.round(source.similarity * 100)}%
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* 显示提取的文本片段 */}
                {source.chunk_text && (
                  <div className="mt-3 p-3 bg-muted/30 rounded-lg border border-border/30">
                    <p className="text-[11px] text-gray-300 leading-relaxed line-clamp-4">
                      {source.chunk_text}
                    </p>
                  </div>
                )}

                {/* 查看详情按钮 */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-3 w-full h-8 text-[11px] hover:bg-primary/10 hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => {
                    console.log('预览文档:', source.file_id);
                  }}
                >
                  <ExternalLink className="h-3 w-3 mr-2" />
                  查看详情
                </Button>
              </div>
            ))}
          </div>
        </aside>
      )}
    </div>
  );
}
