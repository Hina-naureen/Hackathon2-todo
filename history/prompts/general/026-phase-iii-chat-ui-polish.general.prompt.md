---
id: "026"
title: "Phase III Chat UI Polish"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Prepare UI for Phase III AI Chatbot"
labels: ["phase-iii", "chat-ui", "glassmorphism", "dark-mode", "frontend"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "frontend/components/ChatWidget.tsx"
  - "frontend/components/ChatPanel.tsx"
tests: []
---

## Prompt

Prepare UI for Phase III AI Chatbot.

Requirements:
- Add floating chat button bottom-right
- Create chat panel component
- Tailwind glassmorphism style
- dark mode compatible
- No backend logic yet

Files:
components/ChatWidget.tsx
components/ChatPanel.tsx

Design:
- rounded-2xl
- backdrop-blur-md
- shadow-xl
- hover animations

Do not change existing todo logic.

## Response

Enhanced both Phase III chat UI components. No backend logic added; all changes are pure UI scaffolding.

### ChatWidget.tsx changes
- **Fixed animation**: replaced `animate-in fade-in slide-in-from-bottom-4` (requires `tailwindcss-animate`, not installed) with a native CSS transition using `opacity`, `scale`, and `translate-y` on an always-mounted wrapper div. Panel smoothly fades and scales in from bottom-right.
- **SVG icons**: replaced text characters (`✦` / `×`) with inline SVG chat-bubble and X icons — reliable cross-platform rendering.
- **Online indicator**: added pulsing `bg-emerald-400 animate-pulse` dot badge at top-right of button when panel is closed, signalling AI availability.
- **Press feedback**: added `active:scale-95` for tactile button press feel.
- All existing glassmorphism (`backdrop-blur-md`, `rounded-2xl`, `shadow-xl`, `hover:scale-110 hover:shadow-2xl`) and dark mode variants preserved.

### ChatPanel.tsx changes
- **Phase III preview banner**: gradient banner (`from-violet-500/10 via-purple-500/10 to-blue-500/10`) at the very top of the panel with `PHASE III PREVIEW` in uppercase tracking-widest, clearly marking this as a coming-soon feature.
- **SVG close icon**: replaced `×` text character in header close button with inline SVG X icon.
- **SVG send icon**: replaced `↑` text character in send button with inline SVG up-arrow icon.
- **Removed redundant badge**: eliminated `· Phase III` inline text from header (now handled by the top banner).
- All message bubble styling, auto-scroll, Enter-to-send, stub response logic, and dark mode variants left intact.

### Non-changes (todo logic untouched)
- `TasksView.tsx` — not modified
- `Header.tsx` — not modified
- `lib/api.ts`, `lib/auth.ts` — not modified
- No new dependencies added

## Outcome

Both files satisfy all stated requirements:
- [x] Floating chat button fixed bottom-right (`fixed bottom-6 right-6`)
- [x] Chat panel component with glassmorphism (`backdrop-blur-md bg-white/90 rounded-2xl shadow-xl`)
- [x] Dark mode compatible (all `dark:` variants present)
- [x] No backend logic (stub response only)
- [x] Hover animations (`hover:scale-110 hover:shadow-2xl active:scale-95`)
- [x] Animation works without extra npm packages
