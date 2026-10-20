# ICMA project instructions

## Project state: CurrentState.md

@CurrentState.md

`CurrentState.md` at the repo root is the project's long-running memory: the goal, every decision
with its date and reason, what exists, results, open decisions and next steps. It is imported above,
so every session starts with it, and a new session needs nothing else to pick up the work.

- Treat it as the record of project state. If it disagrees with the code or git, trust them, tell
  Ahmed, and fix the file.
- Update it in the same change as any work that makes a decision, produces a result, adds a file,
  service or command, opens or settles a question, or finishes a next step. Before ending a session
  that changed any of these, check that the file is current.
- Replace stale lines instead of appending a log; git history keeps the past. Use absolute dates.
- Keep it short enough to read in full every session, under about 250 lines. Put detail in
  `docs/`, `eval/` or `reports/` and link it.
- Do not copy project state into Claude's auto-memory. Memory keeps only a pointer to this file.

## Shared vocabulary with Ahmed

Ahmed is learning ICMA while building this app. Two files set the words we use:

- @GLOSSARY.md defines one word per idea, built up from the basics.
- @learning/KNOWN.md records which of those words Ahmed knows.

When explaining any ICMA idea to Ahmed, in chat or in a doc written for Ahmed:

1. Use only words marked Known, plus plain English. Never use the words a glossary entry lists
   under "Don't say".
2. When a new word is unavoidable, introduce it on its own line starting **New word:**, defined
   only with Known words. Introduce at most two new words per answer.
3. Start with the problem the idea solves, then the rule, then a worked example: a made-up one
   with simple names first, then a real case from the Pavlovitch 2011 gold study (`eval/gold/`)
   where it helps. Small text diagrams of chains help.
4. Put scholar names and page numbers after the plain explanation.
5. End by listing the new words used and asking whether to mark them Known.

## Keeping the vocabulary files current

- Add or fix a glossary entry as soon as a word is settled. A definition may only use plain
  English and words defined above it.
- Move a word to Known only when Ahmed says it is known or uses it correctly. Covering it in an
  explanation does not count.
- If Ahmed's understanding of a word is wrong, record the correction under Corrected and keep the
  word out of Known.
- When code, app text or scholars use a different word for a glossary idea, add it under
  Conflicts in the glossary instead of switching words.
