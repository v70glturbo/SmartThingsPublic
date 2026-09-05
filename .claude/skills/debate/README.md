# /debate — Claude ⇄ Gemini consult

A Claude Code skill that stages a structured debate between Claude and Gemini
on a question you pose, then gives you both models' independent verdicts and
a synthesis. Transcripts are written to `debates/`.

## Setup (once)

Pick **one** way for Claude to reach Gemini:

**A. Gemini CLI** (uses your Google login)
```sh
npm install -g @google/gemini-cli
gemini            # first run: sign in
```

**B. API key** (no install needed)
```sh
export GEMINI_API_KEY="..."      # from https://aistudio.google.com/apikey
export GEMINI_MODEL="gemini-2.5-pro"   # optional; see --list-models
```

Check it works:
```sh
echo "Reply with the word READY." | python3 .claude/skills/debate/scripts/gemini.py
python3 .claude/skills/debate/scripts/gemini.py --list-models   # API backend only
```

## Use

In Claude Code, from this repo:

```
/debate Should the Hue device handler poll every minute or rely on push updates? --rounds 2
/debate Is Groovy metaprogramming worth it for the SmartApp DSL? --claude-side "no, keep it explicit" --gemini-side "yes"
```

What happens: Gemini opens, Claude opens, N rebuttal rounds alternate, each
side closes with an out-of-role verdict, and Claude prints a synthesis.
See `SKILL.md` for the full protocol.

## Notes

- Claude both hosts and debates one side; the out-of-role verdict from Gemini
  and the side-by-side verdicts exist to offset that bias.
- `gemini.py` is stdlib-only Python 3.9+. Backend order: `gemini` CLI if on
  PATH, else the REST API. Force with `--backend cli|api` or `GEMINI_BACKEND`.
- Transcript files under `debates/` are safe to commit or ignore as you prefer.
