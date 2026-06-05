import { useState } from "react";
import { ChevronRight, CheckCircle2, AlertCircle, Loader2, Wrench } from "lucide-react";
import type { ToolCallRecord } from "../store/useChatStore";

export function ToolCallCard({ call }: { call: ToolCallRecord }) {
  const [open, setOpen] = useState(false);

  const Icon =
    call.status === "running"
      ? Loader2
      : call.status === "error"
        ? AlertCircle
        : CheckCircle2;
  const iconClass = `tool-icon tool-icon-${call.status}`;

  return (
    <div className={`tool-card tool-card-${call.status}`}>
      <button className="tool-card-header" onClick={() => setOpen(!open)}>
        <Wrench size={12} style={{ marginRight: 4 }} />
        <code className="tool-name">{call.tool}</code>
        <span className="tool-args">{call.args_preview}</span>
        <Icon size={14} className={iconClass} style={{ marginLeft: "auto" }} />
        <ChevronRight
          size={14}
          style={{
            transform: open ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.15s",
          }}
        />
      </button>
      {open && (
        <div className="tool-card-body">
          {call.error ? (
            <pre className="tool-result-error">{call.error}</pre>
          ) : (
            <pre>{call.result_preview || "(无结果)"}</pre>
          )}
        </div>
      )}
    </div>
  );
}
