import { db } from "./dbService";

export interface ConversationRow {
  id: string;
  userId: string;
  title: string | null;
  sessionId: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface MessageRow {
  id: string;
  conversationId: string;
  role: string;
  content: string;
  createdAt: Date;
}

class ConversationService {
  // -------------------------------------------------------------------------
  // getOrCreateConversation
  // Called when the first message of a session arrives.
  // If a conversation with this sessionId already exists, return it.
  // Otherwise create a new one, using the first 60 chars of the message as title.
  // -------------------------------------------------------------------------
  async getOrCreateConversation(
    userId: string,
    sessionId: string,
    firstMessage: string
  ): Promise<ConversationRow> {
    const existing = await db.prisma.$queryRaw<ConversationRow[]>`
      SELECT id, "userId", title, "sessionId", "createdAt", "updatedAt"
      FROM conversations
      WHERE "sessionId" = ${sessionId}
      LIMIT 1
    `;
    if (existing[0]) return existing[0];

    const title = firstMessage.slice(0, 60) + (firstMessage.length > 60 ? "…" : "");
    const rows = await db.prisma.$queryRaw<ConversationRow[]>`
      INSERT INTO conversations ("userId", title, "sessionId", "createdAt", "updatedAt")
      VALUES (${userId}::uuid, ${title}, ${sessionId}, NOW(), NOW())
      RETURNING id, "userId", title, "sessionId", "createdAt", "updatedAt"
    `;
    return rows[0];
  }

  // -------------------------------------------------------------------------
  // addMessage
  // -------------------------------------------------------------------------
  async addMessage(
    conversationId: string,
    role: "user" | "assistant",
    content: string
  ): Promise<MessageRow> {
    const rows = await db.prisma.$queryRaw<MessageRow[]>`
      INSERT INTO messages ("conversationId", role, content, "createdAt")
      VALUES (${conversationId}::uuid, ${role}, ${content}, NOW())
      RETURNING id, "conversationId", role, content, "createdAt"
    `;
    return rows[0];
  }

  // -------------------------------------------------------------------------
  // getConversations  — list for sidebar, most recent first
  // -------------------------------------------------------------------------
  async getConversations(userId: string): Promise<ConversationRow[]> {
    return db.prisma.$queryRaw<ConversationRow[]>`
      SELECT id, "userId", title, "sessionId", "createdAt", "updatedAt"
      FROM conversations
      WHERE "userId" = ${userId}::uuid
      ORDER BY "updatedAt" DESC
    `;
  }

  // -------------------------------------------------------------------------
  // getMessages  — full message history for one conversation
  // -------------------------------------------------------------------------
  async getMessages(conversationId: string, userId: string): Promise<MessageRow[]> {
    return db.prisma.$queryRaw<MessageRow[]>`
      SELECT m.id, m."conversationId", m.role, m.content, m."createdAt"
      FROM messages m
      JOIN conversations c ON c.id = m."conversationId"
      WHERE m."conversationId" = ${conversationId}::uuid
        AND c."userId" = ${userId}::uuid
      ORDER BY m."createdAt" ASC
    `;
  }

  // -------------------------------------------------------------------------
  // deleteConversation
  // -------------------------------------------------------------------------
  async deleteConversation(id: string, userId: string): Promise<boolean> {
    const result = await db.prisma.$executeRaw`
      DELETE FROM conversations
      WHERE id = ${id}::uuid AND "userId" = ${userId}::uuid
    `;
    return result > 0;
  }

  // -------------------------------------------------------------------------
  // touchConversation — update updatedAt so it floats to top of sidebar
  // -------------------------------------------------------------------------
  async touchConversation(sessionId: string): Promise<void> {
    await db.prisma.$executeRaw`
      UPDATE conversations SET "updatedAt" = NOW() WHERE "sessionId" = ${sessionId}
    `;
  }
}

// Instantiated once here; shares db's single PrismaClient rather than opening
// a second connection pool to the same database. Only the methods listed
// below are part of the public surface.
const instance = new ConversationService();

export const conversationService = {
  getOrCreateConversation: instance.getOrCreateConversation.bind(instance),
  addMessage: instance.addMessage.bind(instance),
  getConversations: instance.getConversations.bind(instance),
  getMessages: instance.getMessages.bind(instance),
  deleteConversation: instance.deleteConversation.bind(instance),
  touchConversation: instance.touchConversation.bind(instance),
};
