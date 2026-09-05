---
name: debate
description: Run a structured, multi-round debate between Claude and Gemini on a question or design decision, then deliver a synthesized verdict with both models' closing judgments. Use when the user says /debate, "have Claude and Gemini debate", "AI consult", "get a second opinion from Gemini", or wants two models to argue opposing sides of a decision.
---

# /debate — Claude vs Gemini consult

You are the **host** and the **Claude debater**. Gemini is the other debater,
reached through `scripts/gemini.py` (relative to this skill's directory). Gemini
is stateless: every call must include the full transcript so far.

## Arguments

`/debate <question> [--rounds N] [--claude-side <position>] [--gemini-side <position>]`

- `question` — required. If missing, ask for it and stop.
- `--rounds` — rebuttal rounds after openings. Default **2**. Cap at 4.
- `--claude-side` / `--gemini-side` — force positions. If not given, run
  **Step 1** to assign them.

## Preflight

1. Resolve `SKILL_DIR` to this skill's directory and run
   `python3 $SKILL_DIR/scripts/gemini.py --help`. If Python is missing, stop.
2. Send a one-line smoke prompt ("Reply with the single word READY.") through
   the script. If it fails, show the user the script's stderr verbatim (it names
   the fix: install the CLI or export `GEMINI_API_KEY`) and stop. Do not
   simulate Gemini's side yourself under any circumstances.
3. Create `debates/` at the repo root if absent and open the transcript at
   `debates/YYYY-MM-DD-<slug>.md` (slug: ≤6 words of the question, kebab-case).
   Append to this file after **every** turn so a crash loses nothing.

## Step 1 — Frame and assign sides

If sides weren't forced, write down the two strongest opposing positions on the
question (not "yes/no" — concrete stances). Assign Claude the side you find
**less** intuitively appealing; Gemini gets the other. State this in the
transcript header. If the question has no real second side, tell the user and
offer a "critique" mode instead: Gemini attacks a proposal, Claude defends.

Transcript header:

```
# Debate: <question>
Date · Claude side: … · Gemini side: … · Rounds: N · Gemini model: <from script output or env>
```

## Step 2 — Openings

**Gemini first** (so Claude cannot anchor it). Use the prompt template below
with `TASK = opening`. Then write Claude's opening. Each opening: ≤300 words,
must state the position, 3 strongest arguments, and the single condition under
which the speaker would switch sides.

## Step 3 — Rebuttal rounds (× N)

Alternate: Gemini rebuts, then Claude rebuts. Each rebuttal ≤250 words and must:
- quote or paraphrase the specific claim it is answering,
- concede anything it now agrees with (explicitly: "Conceded: …"),
- introduce at most one new argument.

Argue Claude's side in good faith and at full strength, even if you privately
disagree. Do not soften toward Gemini to be agreeable. Do not read ahead or
edit Gemini's text.

## Step 4 — Closings and independent verdicts

Ask Gemini for a closing with `TASK = closing`: ≤200 words summarizing the
strongest surviving argument on **each** side, then its own verdict —
which position it now finds more defensible and a confidence 0–100%,
**stepping out of its assigned role**.

Then write Claude's closing under the same rules. Be honest here: if Gemini
won, say so.

## Step 5 — Synthesis (shown to the user)

Print a short report, also appended to the transcript:

1. **Verdicts side by side** — Gemini's and Claude's out-of-role verdicts and
   confidences. If they disagree, say so plainly; do not paper over it.
2. **Points of agreement** — what both sides conceded or converged on.
3. **Live disagreements** — the cruxes still open, each with the fact or
   experiment that would settle it.
4. **Recommendation** — one paragraph, written as the host, with a caveat that
   Claude hosted and judged its own side.
5. Path to the transcript.

## Gemini prompt template

Write each Gemini prompt to a scratch file and call:
`python3 $SKILL_DIR/scripts/gemini.py --prompt-file <file>`

```
You are Gemini, one of two AI debaters in a structured consult. The other is Claude.
QUESTION: <question>
YOUR ASSIGNED POSITION: <gemini side>
CLAUDE'S ASSIGNED POSITION: <claude side>

RULES
- Argue your assigned position in good faith and at full strength.
- Be concrete: cite mechanisms, tradeoffs, numbers, or code where relevant.
- Quote the specific claim you are rebutting. Concede explicitly ("Conceded: ...")
  when you agree. Introduce at most one new argument per rebuttal.
- Word limit for this turn: <limit>. Plain prose or short bullets; no preamble.

TRANSCRIPT SO FAR
<full transcript, or "(none — you speak first)">

YOUR TASK: <opening | rebuttal round K | closing>
<for closing add:>
Summarize the strongest surviving argument on each side, then step OUT of your
assigned role and give your honest verdict: which position is more defensible,
and a confidence from 0 to 100%. Format the last line exactly as:
VERDICT: <position> — <NN>%
```

## Guardrails

- Never fabricate a Gemini turn. A failed call ends the debate with the error shown.
- Never run more than 4 rebuttal rounds; if the user asks, explain the cap.
- Keep user-visible output to the synthesis; the full transcript lives in the file.
- If the question involves the user's own code, both debaters may be given
  relevant file excerpts — include them in the Gemini prompt under
  `CONTEXT`; do not make Gemini guess at code it cannot see.
