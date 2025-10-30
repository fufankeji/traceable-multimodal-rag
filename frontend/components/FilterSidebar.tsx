import { Badge } from "./ui/badge";
import { Checkbox } from "./ui/checkbox";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Calendar } from "lucide-react";

interface FilterSidebarProps {
  selectedCorpus: string;
  setSelectedCorpus: (value: string) => void;
  selectedFileTypes: string[];
  toggleFileType: (type: string) => void;
  selectedTags: string[];
  toggleTag: (tag: string) => void;
  clearFilters: () => void;
}

export function FilterSidebar({
  selectedCorpus,
  setSelectedCorpus,
  selectedFileTypes,
  toggleFileType,
  selectedTags,
  toggleTag,
  clearFilters,
}: FilterSidebarProps) {
  const corpusOptions = ["全部", "工程制造", "研发架构", "工业档案"];
  const fileTypes = [
    { id: "cad", label: "CAD（.dwg/.dxf）" },
    { id: "pdf", label: "PDF" },
    { id: "image", label: "图片（.png/.jpg）" },
    { id: "office", label: "Office" },
  ];
  const tags = ["v1.2", "生产线A", "流程图", "装配", "BOM"];

  return (
    <aside className="w-[280px] backdrop-blur-xl bg-card/60 border-r border-border p-6 overflow-y-auto">
      <div className="space-y-6">
        <div>
          <h3 className="text-[14px] mb-3 text-foreground/90">知识库</h3>
          <div className="flex flex-wrap gap-2">
            {corpusOptions.map((corpus) => (
              <Badge
                key={corpus}
                variant={selectedCorpus === corpus ? "default" : "outline"}
                className={`cursor-pointer px-3 py-1 text-[12px] transition-all ${
                  selectedCorpus === corpus
                    ? "bg-primary/20 text-primary border-primary/50 shadow-lg shadow-primary/20"
                    : "border-border/50 hover:border-primary/30"
                }`}
                onClick={() => setSelectedCorpus(corpus)}
              >
                {corpus}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-[14px] mb-3">文件类型</h3>
          <div className="space-y-2">
            {fileTypes.map((type) => (
              <div key={type.id} className="flex items-center space-x-2">
                <Checkbox
                  id={type.id}
                  checked={selectedFileTypes.includes(type.id)}
                  onCheckedChange={() => toggleFileType(type.id)}
                />
                <Label
                  htmlFor={type.id}
                  className="text-[13px] cursor-pointer font-normal"
                >
                  {type.label}
                </Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-[14px] mb-3">时间范围</h3>
          <Button
            variant="outline"
            className="w-full justify-start text-[13px] h-9"
          >
            <Calendar className="mr-2 h-4 w-4" />
            选择日期范围
          </Button>
        </div>

        <div>
          <h3 className="text-[14px] mb-3 text-foreground/90">版本/标签</h3>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <Badge
                key={tag}
                variant={selectedTags.includes(tag) ? "default" : "outline"}
                className={`cursor-pointer px-3 py-1 text-[12px] transition-all ${
                  selectedTags.includes(tag)
                    ? "bg-primary/20 text-primary border-primary/50 shadow-lg shadow-primary/20"
                    : "border-border/50 hover:border-primary/30"
                }`}
                onClick={() => toggleTag(tag)}
              >
                {tag}
              </Badge>
            ))}
          </div>
        </div>

        <Button
          variant="link"
          className="text-[12px] px-0 h-auto text-muted-foreground"
          onClick={clearFilters}
        >
          清空筛选
        </Button>
      </div>
    </aside>
  );
}
