import { Message } from "./types";
import { formatTime } from "./helpers";

function formatContent(content: string) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let codeBlock: string[] = [];
  let inCode = false;
  let key = 0;

  for (const line of lines) {
    if (line.startsWith("```")) {
      if (inCode) {
        elements.push(
          <pre key={key++} className="bg-background border border-border rounded-lg px-3 py-2.5 text-xs font-mono overflow-x-auto my-2 text-foreground">
            {codeBlock.join("\n")}
          </pre>
        );
        codeBlock = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) { codeBlock.push(line); continue; }

    const parsed = line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith("**") && part.endsWith("**")
        ? <strong key={i}>{part.slice(2, -2)}</strong>
        : part
    );
    elements.push(<p key={key++} className={line === "" ? "h-2" : ""}>{parsed}</p>);
  }

  return <>{elements}</>;
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold flex-shrink-0 mt-0.5 ${
        isUser ? "bg-foreground text-background" : "bg-muted text-muted-foreground border border-border"
      }`}>
        {isUser ? "U" : "AI"}
      </div>

      <div className={`flex-1 min-w-0 ${isUser ? "flex flex-col items-end" : ""}`}>
        <div className={`inline-block max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-sm"
            : "bg-muted text-foreground rounded-bl-sm"
        }`}>
          {isUser ? message.content : formatContent(message.content)}
        </div>
        <span className="text-[11px] text-muted-foreground mt-1 px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
