---
id: "032"
title: "ChatPanel Judge Mode UI"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Upgrade ChatPanel to Judge Mode UI"
labels: ["phase-iii", "chat-ui", "frontend", "tailwind", "glassmorphism", "dark-mode"]
links:
  spec: "specs/api/chat-endpoint.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "frontend/components/ChatPanel.tsx"
  - "frontend/app/globals.css"
tests: []
---

## Prompt

Upgrade ChatPanel to Judge Mode UI.

Requirements:
- Add typing indicator animation ("AI is typing...")
- Add gradient header bar for Phase III Preview
- Auto scroll to latest message
- Add small AI avatar circle before assistant messages
- Smooth fade-in animation for messages

Design:
- Tailwind only
- rounded-2xl
- backdrop-blur-md
- dark mode compatible

Do NOT change backend logic.
Only UI enhancements.

## Response

### frontend/app/globals.css (1 addition)

Added `@keyframes msg-in` and `.msg-in` utility class for fade + slide-up animation:
```css
@keyframes msg-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.msg-in { animation: msg-in 0.22s ease-out both; }
```
Uses plain CSS so no extra packages required.

### frontend/components/ChatPanel.tsx (full upgrade)

1. **Gradient header bar**: Merged the previous "Phase III Preview" thin banner and plain header into one visually prominent bar with `bg-linear-to-r from-violet-600 via-purple-600 to-blue-600`. Retains pulsing emerald online dot, title "AI Assistant", subtitle "Phase III Preview", and close button.

2. **AI avatar** (`AiAvatar` component): Small `w-6 h-6` circle with `bg-linear-to-br from-violet-500 to-purple-600` gradient and a white star SVG. Rendered immediately to the left of every assistant bubble and the typing indicator.

3. **"AI is typing…" label**: Added italic `text-[11px]` label next to bouncing dots inside the loading indicator row. Avatar is also shown alongside.

4. **Fade-in animation**: Applied `.msg-in` class to each message row and the typing indicator row — every new element slides up 6px and fades in over 220ms.

5. **Send button**: Updated to gradient (`bg-linear-to-br from-violet-600 to-purple-600`) to match header.

6. **Focus ring**: Input focus ring updated to `focus:ring-violet-500` / `dark:focus:ring-violet-400` to match gradient theme.

Backend (`chat.py`, `agent.py`) untouched. Zero TypeScript errors.

## Outcome

- [x] Gradient header bar with "AI Assistant" + "Phase III Preview" subtitle
- [x] Pulsing ping-animation online dot in header
- [x] AI avatar circle before every assistant message and typing indicator
- [x] "AI is typing…" label beside bouncing dots
- [x] `.msg-in` fade-in animation (opacity 0→1, translateY 6px→0, 220ms)
- [x] Auto-scroll unchanged (useEffect + bottomRef)
- [x] Dark mode compatible throughout
- [x] Zero TypeScript errors (`tsc --noEmit` clean)
- [x] No new npm packages required
