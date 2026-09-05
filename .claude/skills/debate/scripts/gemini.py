#!/usr/bin/env python3
"""Send one prompt to Gemini and print the reply.

Used by the /debate skill so Claude can hand Gemini a turn of the debate.
Stateless: the caller passes the full transcript each time.

Backends, tried in order:
  1. `gemini` CLI on PATH  (gemini -p "<prompt>")
  2. Gemini REST API with GEMINI_API_KEY (no third-party deps)

Usage:
  python3 gemini.py --prompt-file turn.md            # prompt from a file
  echo "prompt" | python3 gemini.py                  # prompt from stdin
  python3 gemini.py --backend api --model gemini-2.5-pro --prompt-file turn.md
  python3 gemini.py --list-models                    # API backend only

Env:
  GEMINI_API_KEY   required for the API backend
  GEMINI_MODEL     default model (default: gemini-2.5-pro)
  GEMINI_BACKEND   auto | cli | api  (default: auto)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def die(msg, code=1):
    print(f"gemini.py: {msg}", file=sys.stderr)
    sys.exit(code)


def read_prompt(args):
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            return f.read()
    if sys.stdin.isatty():
        die("no prompt: pass --prompt-file or pipe the prompt on stdin")
    return sys.stdin.read()


def run_cli(prompt, model):
    cmd = ["gemini", "-p", prompt]
    if model:
        cmd += ["-m", model]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        die(f"gemini CLI failed (exit {proc.returncode}):\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        die("GEMINI_API_KEY is not set and no `gemini` CLI was found on PATH.\n"
            "  Get a key at https://aistudio.google.com/apikey and export GEMINI_API_KEY,\n"
            "  or install the CLI: npm install -g @google/gemini-cli")
    return key


def api_request(path, payload=None):
    url = f"{API_BASE}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if data else "GET",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key()},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        die(f"Gemini API HTTP {e.code} for {path}:\n{body}")
    except urllib.error.URLError as e:
        die(f"Gemini API unreachable: {e.reason}")


def run_api(prompt, model, temperature):
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    out = api_request(f"models/{model}:generateContent", payload)
    try:
        cands = out["candidates"]
        parts = cands[0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError):
        reason = out.get("promptFeedback", {}).get("blockReason")
        die(f"unexpected Gemini response{f' (blocked: {reason})' if reason else ''}:\n"
            f"{json.dumps(out, indent=2)[:2000]}")
    if not text:
        die(f"Gemini returned an empty reply (finishReason="
            f"{cands[0].get('finishReason')})")
    return text


def list_models():
    out = api_request("models")
    for m in out.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(m["name"].removeprefix("models/"))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt-file", help="file containing the prompt (default: stdin)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--backend", choices=["auto", "cli", "api"],
                    default=os.environ.get("GEMINI_BACKEND", "auto"))
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--list-models", action="store_true",
                    help="print models that support generateContent (API backend)")
    args = ap.parse_args()

    if args.list_models:
        list_models()
        return

    prompt = read_prompt(args)
    if not prompt.strip():
        die("prompt is empty")

    backend = args.backend
    if backend == "auto":
        backend = "cli" if shutil.which("gemini") else "api"

    reply = run_cli(prompt, args.model) if backend == "cli" \
        else run_api(prompt, args.model, args.temperature)
    print(reply)


if __name__ == "__main__":
    main()
