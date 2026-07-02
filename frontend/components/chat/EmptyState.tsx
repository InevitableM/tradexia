import { MessageSquare } from "lucide-react";

const SUGGESTIONS = [
  "Give me a full analysis of TCS",
  "Is NIFTY50 attractively valued right now?",
  "Compare HDFC Bank and ICICI Bank fundamentals",
  "What is the historical performance of BANKNIFTY?",
];

export default function EmptyState({ onPrompt }: { onPrompt: (p: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-4 py-16">
      <div className="w-10 h-10 bg-foreground rounded-xl flex items-center justify-center mb-4">
        <MessageSquare size={18} className="text-background" />
      </div>
      <h2 className="text-lg font-semibold text-foreground mb-1">What would you like to analyze?</h2>
      <p className="text-sm text-muted-foreground mb-8">Ask about any stock or index</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => onPrompt(s)}
            className="text-left text-sm text-foreground px-3.5 py-3 rounded-xl border border-border bg-background hover:bg-accent transition-colors leading-snug">
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
