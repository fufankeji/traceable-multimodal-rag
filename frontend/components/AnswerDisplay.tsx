import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { AlertCircle, RotateCcw } from "lucide-react";
import type { QASource, QueryType } from "../types";

interface AnswerDisplayProps {
  question: string;
  answer: string;
  sources: QASource[];
  confidence: number;
  queryType: QueryType;
  onNewQuestion?: () => void;  // 添加重新提问回调
}

const queryTypeLabels: Record<QueryType, { label: string; color: string }> = {
  exact_query: { label: "精确查询", color: "from-blue-500/20 to-cyan-500/20 text-blue-400 border-blue-500/30" },
  filter_query: { label: "过滤查询", color: "from-purple-500/20 to-pink-500/20 text-purple-400 border-purple-500/30" },
  general_query: { label: "通用查询", color: "from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30" },
};

export function AnswerDisplay({ question, answer, confidence, queryType, onNewQuestion }: AnswerDisplayProps) {
  const typeInfo = queryTypeLabels[queryType];
  const confidencePercent = Math.round(confidence * 100);
  const confidenceColor = confidence >= 0.7 ? "text-emerald-400" : confidence >= 0.4 ? "text-yellow-400" : "text-orange-400";

  return (
    <div className="space-y-4">
      {/* 用户问题卡片 */}
      <div className="relative backdrop-blur-xl bg-primary/5 border border-primary/20 rounded-2xl p-5 shadow-lg">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            <span className="text-sm font-semibold text-primary">Q</span>
          </div>
          <div className="flex-1">
            <p className="text-[15px] font-medium text-white leading-relaxed">
              {question}
            </p>
          </div>
          {onNewQuestion && (
            <Button
              variant="outline"
              size="sm"
              onClick={onNewQuestion}
              className="flex-shrink-0 h-8 px-3 text-[12px] border-border/60 text-gray-200 hover:border-primary/40 hover:bg-primary/10 hover:text-white"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
              重新提问
            </Button>
          )}
        </div>
      </div>

      {/* 答案卡片 */}
      <div className="relative backdrop-blur-xl bg-card/60 rounded-2xl p-6 border border-border/30 shadow-2xl shadow-black/10">
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-primary/5 via-transparent to-purple-500/5 pointer-events-none" />

        <div className="relative space-y-4">
          {/* AI头像和元信息 */}
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-sm font-semibold text-emerald-400">A</span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-[15px] font-semibold text-white">AI 回答</h3>
                <Badge
                  variant="default"
                  className={`text-[11px] px-2 py-0.5 bg-gradient-to-r ${typeInfo.color}`}
                >
                  {typeInfo.label}
                </Badge>
                <Badge
                  variant="outline"
                  className={`text-[11px] px-2 py-0.5 border-border/50 ${confidenceColor}`}
                >
                  置信度 {confidencePercent}%
                </Badge>
              </div>
            </div>
          </div>

          {/* 答案内容 */}
          <div className="prose prose-sm max-w-none pl-11">
            <div className="text-[14px] leading-relaxed text-gray-200 whitespace-pre-wrap">
              {answer}
            </div>
          </div>

          {/* 置信度低时的提示 */}
          {confidence < 0.4 && (
            <div className="flex items-start gap-2 p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg ml-11">
              <AlertCircle className="h-4 w-4 text-orange-400 mt-0.5 flex-shrink-0" />
              <p className="text-[12px] text-orange-400">
                该答案的置信度较低，建议参考更多来源信息或重新描述问题。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
