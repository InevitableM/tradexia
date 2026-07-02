"use client";

import { Trash2 } from "lucide-react";
import { Conversation } from "./types";

interface Props {
  label: string;
  items: Conversation[];
  activeId: string;
  hoveredId: string | null;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
}

export default function ConvoGroup({ label, items, activeId, hoveredId, onSelect, onHover, onDelete }: Props) {
  if (items.length === 0) return null;

  return (
    <div className="pt-3 first:pt-1">
      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider px-2 pb-1">
        {label}
      </p>
      {items.map((c) => (
        <div key={c.id}
          onMouseEnter={() => onHover(c.id)} onMouseLeave={() => onHover(null)}
          className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors cursor-pointer ${
            activeId === c.id
              ? "bg-accent text-foreground"
              : "text-muted-foreground hover:bg-accent hover:text-foreground"
          }`}>
          <span className="flex-1 truncate text-sm" onClick={() => onSelect(c.id)}>{c.title}</span>
          {(hoveredId === c.id || activeId === c.id) && (
            <button onClick={(e) => onDelete(c.id, e)}
              className="p-0.5 rounded text-muted-foreground hover:text-foreground transition-colors shrink-0">
              <Trash2 size={12} />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
