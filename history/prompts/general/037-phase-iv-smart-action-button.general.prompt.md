---
id: "037"
title: "Phase IV Smart Action Button"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Upgrade Phase IV – Smart Action Suggestion: Create Task button below AI reply when 'add' keyword detected"
labels: ["phase-iv", "chat-ui", "frontend", "action-button"]
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

Add "Create Task" action button below AI reply when "add" keyword is detected.
Button: rounded-xl bg-slate-900 text-white hover:scale-105 transition.
On click: console.log("Create task triggered"). No real task creation yet.

## Response

### frontend/components/ChatPanel.tsx (4 targeted edits)

1. `import { Fragment }` added alongside existing hooks.

2. `Message` interface — added `showAction?: boolean`:
   Set to `true` on assistant messages when the user's input contained "add".

3. `handleSend` — assistant message object extended:
   ```ts
   showAction: text.toLowerCase().includes('add')
   ```

4. Messages render — wrapped each entry in `<Fragment key={msg.id}>` so the
   action button can be a sibling of the bubble row without breaking the key prop:
   ```tsx
   {msg.role === 'assistant' && msg.showAction && (
     <div className="msg-in flex justify-start pl-8">
       <button
         onClick={() => console.log('Create task triggered')}
         className="px-3 py-1.5 text-xs font-medium rounded-xl bg-slate-900 text-white
                    hover:scale-105 active:scale-95 transition-all duration-200
                    dark:bg-white dark:text-slate-900"
       >
         + Create Task
       </button>
     </div>
   )}
   ```
   `pl-8` (32px) = avatar width (w-6 = 24px) + gap (gap-2 = 8px) — aligns the button flush with the left edge of the AI bubble.

## Outcome

- [x] "Create Task" button appears below every AI reply where input contained "add"
- [x] Button absent for replies to non-add messages (urgent, today, fallback, etc.)
- [x] `console.log('Create task triggered')` fires on click
- [x] `msg-in` fade-in animation applies to the button row too
- [x] Dark mode: `dark:bg-white dark:text-slate-900` (inverted, matching user bubble)
- [x] All existing features unchanged (simulateAI, 700ms delay, typing indicator, avatar)
- [x] Zero TypeScript errors
