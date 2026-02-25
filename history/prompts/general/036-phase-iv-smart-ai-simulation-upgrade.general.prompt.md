---
id: "036"
title: "Phase IV Smart AI Simulation Upgrade"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Upgrade Phase IV – Smart AI Assistant Layer (NO REAL API)"
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

Upgrade Phase IV – Smart AI Assistant Layer (NO REAL API).

Keywords: add, tomorrow, today, urgent, homework, meeting
Fallback: "Tell me more about your task so I can help."
Architecture: function simulateAI(message: string) inside ChatPanel.tsx
700ms fake thinking delay. No backend. Only ChatPanel.tsx.

## Response

### frontend/components/ChatPanel.tsx

**Removed:** `chatApi`, `ApiError` imports (no backend calls).
**Removed:** `MUTATION_TOOLS`, `detectIntent`, `extractTask` (superseded).
**Added:** `extractTask` (kept as private helper), `simulateAI`, `AI_THINKING_DELAY = 700`.

#### `extractTask(raw: string): string`
Strips intent/context keywords from the raw message to surface the task subject.
Regex covers: add create make schedule put set today tomorrow urgent homework meeting please a an the.

#### `simulateAI(message: string): string`
Priority-ordered keyword detection, always returns a non-empty string:

| Pattern | Reply |
|---|---|
| add + urgent | "That sounds urgent! Should I create a high-priority task called '…'?" |
| urgent + meeting | "This sounds important. I recommend marking it as high priority." |
| add + homework | "I suggest creating a homework task. Should I add it to your list?" |
| add + meeting | "I can add a meeting task for you. Want me to create it?" |
| add + today | "Got it! I can add that for today. Want me to create '…'?" |
| add + tomorrow | "I suggest creating a task for tomorrow. Should I add '…'?" |
| add alone | "Sure! Should I create a task called '…'?" |
| urgent alone | "That sounds important! Would you like me to add this as an urgent task?" |
| homework alone | "Sounds like a study task! Want me to add it to your list?" |
| meeting alone | "Got it, a meeting! Should I schedule it as a task?" |
| today alone | "Would you like me to schedule something for today? Just tell me what to add!" |
| tomorrow alone | "Should I create a task for tomorrow? Tell me what you need!" |
| fallback | "Tell me more about your task so I can help." |

#### `handleSend` — simplified
```
setLoading(true)
await delay(700ms)   ← typing indicator visible
setLoading(false)
append simulateAI(text) reply
```
No try/catch, no backend call, no `onMutation` trigger. Purely local.

## Outcome

- [x] `simulateAI` function with 12 keyword patterns + fallback
- [x] `extractTask` helper isolates task name from the raw message
- [x] 700ms `AI_THINKING_DELAY` — typing indicator shows before every reply
- [x] Fallback: "Tell me more about your task so I can help."
- [x] No backend imports or calls in the component
- [x] All UI unchanged (glassmorphism, dark mode, avatar, typing dots, fade-in)
- [x] Zero TypeScript errors (`tsc --noEmit` clean)
