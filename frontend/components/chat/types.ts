export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface Conversation {
  id: string;
  title: string;
  sessionId: string;
  preview: string;
  timestamp: Date;
  messages: Message[];
}
