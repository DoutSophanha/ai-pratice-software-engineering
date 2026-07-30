"""
AskBot — Session 1 Lab starter
Practical AI for Software Engineering · Week 1

Work through the PARTs in order. Each has TODOs. Run the file after every part:
    python askbot.py

You only need to edit the sections marked TODO. Helper wiring is done for you.
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv
from openai import OpenAI

# --- provider wiring (done for you) ----------------------------------------
load_dotenv()

API_KEY = os.environ.get("LLM_API_KEY")
if not API_KEY or API_KEY.startswith("your-"):
    sys.exit(
        "[!] No API key found. Copy .env.example to .env and paste your key "
        "into LLM_API_KEY, then run again."
    )

client = OpenAI(
    api_key=API_KEY,
    base_url=os.environ.get("LLM_BASE_URL"),
)
MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")


# ===========================================================================
# PART 1 — Your first completion
#   Goal: send one prompt, print the reply.
# ===========================================================================
def ask_once(prompt: str, temperature: float = 0.7) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as err:  # network, auth, rate limit, etc.
        return f"[!] API error: {err}"


# ===========================================================================
# PART 2 — Interactive REPL with memory
#   Goal: a loop that keeps the conversation so the bot remembers context.
# ===========================================================================
def chat_loop(system_prompt: str, temperature: float):
    # Part 2: history holds the WHOLE conversation. The API is stateless, so
    # we resend everything each turn — that is what gives the bot "memory".
    history = [{"role": "system", "content": system_prompt}]
    total_tokens = 0  # Part 4: running token meter across the session

    while True:
        try:
            user_input = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye 👋")
            break

        if user_input.lower() in ("quit", "exit"):
            print("bye 👋")
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})

        # Part 4: call the API with retries on transient failures.
        reply = None
        for attempt in range(1, 4):  # up to 3 tries
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=history,
                    temperature=temperature,
                )
                reply = response.choices[0].message.content

                usage = getattr(response, "usage", None)
                if usage:
                    total_tokens += usage.total_tokens
                break
            except Exception as err:  # network, rate limit, auth, etc.
                if attempt < 3:
                    wait = 2 ** attempt  # 2s, 4s backoff
                    print(f"[!] API error ({err}). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"[!] Failed after 3 attempts: {err}")

        if reply is None:
            history.pop()  # drop the user turn we couldn't answer
            continue

        print(f"bot > {reply}")
        if total_tokens:
            print(f"      (session tokens: {total_tokens})")
        history.append({"role": "assistant", "content": reply})


# ===========================================================================
# PART 3 — CLI flags (done for you — wire your functions in)
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="AskBot — a tiny LLM CLI")
    parser.add_argument("--persona", default="You are a concise, helpful assistant.",
                        help="System prompt / persona")
    parser.add_argument("--temp", type=float, default=0.7,
                        help="Temperature 0.0–2.0")
    parser.add_argument("--once", metavar="PROMPT",
                        help="Ask a single question and exit")
    args = parser.parse_args()

    if args.once:
        print(ask_once(args.once, args.temp))
    else:
        print(f"AskBot ready (model={MODEL}, temp={args.temp}). Type 'quit' to exit.")
        chat_loop(args.persona, args.temp)


if __name__ == "__main__":
    main()
