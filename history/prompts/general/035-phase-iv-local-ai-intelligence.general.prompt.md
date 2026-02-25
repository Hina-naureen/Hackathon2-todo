---
id: "035"
title: "Phase IV Local AI Intelligence"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Prepare Phase IV AI Assistant logic (no real API) — keyword detection + smart replies"
labels: ["phase-iv", "chat-ui", "frontend", "ai-simulation", "keyword-detection"]
links:
  spec: "specs/features/chatbot.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "frontend/components/ChatPanel.tsx"
tests: []
---

## Prompt

Prepare Phase IV AI Assistant logic (no real API).

Goals:
- Add fake AI intelligence layer
- Detect keywords: "add", "tomorrow", "today", "urgent"
- Return smart assistant replies

Example:
User: "add homework tomorrow"
AI: "I suggest creating a task for tomorrow. Should I add it?"

Rules:
- No backend API calls
- Frontend logic only
- Modify ChatPanel.tsx only
- Keep existing UI
- Tailwind untouched

## Response

### frontend/components/ChatPanel.tsx (logic only — zero UI/Tailwind changes)

Added two pure helper functions and one constant above the component:

**`extractTask(raw: string): string`**
Strips intent keywords from the raw message to isolate the task subject:
```
"add homework tomorrow" → "homework"
"urgent add report" → "report"
"add" → "" → falls back to "this task" at call site
```
Uses a regex replace over a known keyword list + whitespace normalisation.

**`detectIntent(text: string): string | null`**
Priority-ordered keyword matching (most specific → most general):
| Pattern | Reply |
|---|---|
| add + urgent | "That sounds urgent! Should I create a high-priority task called '…'?" |
| add + today | "Got it! I can add that for today. Want me to create '…'?" |
| add + tomorrow | "I suggest creating a task for tomorrow. Should I add '…'?" |
| add alone | "Sure! Should I create a task called '…'?" |
| urgent alone | "That sounds important! Would you like me to add this as an urgent task?" |
| today alone | "Would you like me to schedule something for today?" |
| tomorrow alone | "Should I create a task for tomorrow? Tell me what you need!" |
| no match | `null` |

**`LOCAL_REPLY_DELAY = 700`**
Milliseconds to keep the typing indicator visible for local replies (authenticity).

**`handleSend` update**
After appending the user bubble:
1. Call `detectIntent(text)`
2. If non-null → `setLoading(true)`, await 700ms, `setLoading(false)`, append smart reply, `return` (no API call)
3. If null → fall through to `chatApi.sendMessage` exactly as before

The typing indicator ("AI is typing…") shows for 700ms even for local replies, making the experience feel natural.

## Outcome

- [x] "add homework tomorrow" → "I suggest creating a task for tomorrow. Should I add "homework"?"
- [x] "urgent add report" → high-priority suggestion reply
- [x] "today" alone → scheduling prompt
- [x] Typing indicator shown for 700ms on all local replies
- [x] Backend is still reached for messages with no recognised keywords
- [x] Zero UI or Tailwind changes
- [x] Zero TypeScript errors (`tsc --noEmit` clean)
- [x] No new dependencies
