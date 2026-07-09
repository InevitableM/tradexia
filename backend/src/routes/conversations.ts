import { Router, Response } from "express";
import { authenticate } from "../middleware/requestHandler";
import { AuthRequest } from "../types/index";
import { conversationService } from "../services/conversationService";

const router = Router();

// All conversation routes require a valid JWT
router.use(authenticate);

// ---------------------------------------------------------------------------
// GET /api/conversations
// List all conversations for the logged-in user (sidebar)
// ---------------------------------------------------------------------------
router.get("/", async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.userId;
    const conversations = await conversationService.getConversations(userId);
    res.json({ success: true, data: conversations });
  } catch (err) {
    console.error("[conversations] GET /", err);
    res.status(500).json({ success: false, error: "Failed to fetch conversations" });
  }
});

// ---------------------------------------------------------------------------
// GET /api/conversations/:id/messages
// Get full message history for a single conversation
// ---------------------------------------------------------------------------
router.get("/:id/messages", async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.userId;
    const messages = await conversationService.getMessages(req.params.id as string, userId);
    res.json({ success: true, data: messages });
  } catch (err) {
    console.error("[conversations] GET /:id/messages", err);
    res.status(500).json({ success: false, error: "Failed to fetch messages" });
  }
});

// ---------------------------------------------------------------------------
// POST /api/conversations
// Create or return existing conversation for a sessionId, and save both
// the user message and the assistant reply in one shot.
//
// Body: { sessionId, userMessage, assistantMessage }
// ---------------------------------------------------------------------------
router.post("/", async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.userId;
    const { sessionId, userMessage, assistantMessage } = req.body as {
      sessionId?: string;
      userMessage?: string;
      assistantMessage?: string;
    };

    if (!sessionId || !userMessage || !assistantMessage) {
      res.status(400).json({ success: false, error: "sessionId, userMessage, and assistantMessage are required" });
      return;
    }

    const conversation = await conversationService.getOrCreateConversation(userId, sessionId, userMessage);

    const [userMsg, assistantMsg] = await Promise.all([
      conversationService.addMessage(conversation.id, "user", userMessage),
      conversationService.addMessage(conversation.id, "assistant", assistantMessage),
    ]);

    await conversationService.touchConversation(sessionId);

    res.status(201).json({
      success: true,
      data: { conversation, messages: [userMsg, assistantMsg] },
    });
  } catch (err) {
    console.error("[conversations] POST /", err);
    res.status(500).json({ success: false, error: "Failed to save conversation" });
  }
});

// ---------------------------------------------------------------------------
// DELETE /api/conversations/:id
// Delete a conversation (and its messages via CASCADE)
// ---------------------------------------------------------------------------
router.delete("/:id", async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.userId;
    const deleted = await conversationService.deleteConversation(req.params.id as string, userId);
    if (!deleted) {
      res.status(404).json({ success: false, error: "Conversation not found" });
      return;
    }
    res.json({ success: true, message: "Conversation deleted" });
  } catch (err) {
    console.error("[conversations] DELETE /:id", err);
    res.status(500).json({ success: false, error: "Failed to delete conversation" });
  }
});

export default router;
