"""Smoke-test prompt YAML load + compile (run from ``cloudcart`` or ``backend``)."""

from __future__ import annotations

import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from prompt_manager import PromptManager


def main() -> None:
    prompts_dir = str(_backend / "prompts")
    manager = PromptManager(prompts_dir=prompts_dir)

    print("\n" + "=" * 50)
    print("LOADING 'CURRENT' PROMPT")
    print("=" * 50)

    prompt_data = manager.load_prompt("current")
    print(f"Loaded File: {prompt_data.get('file_path')}")
    print(f"Active Identity: {prompt_data.get('role', {}).get('identity')}")
    print(f"Refund Limit: {prompt_data.get('constraints', {}).get('monetary_limit')}")

    print("\n" + "=" * 50)
    print("COMPILED FINAL PROMPT (Preview)")
    print("=" * 50)

    final_prompt = manager.compile_prompt(
        prompt_data, "My phone arrived smashed! Fix this!"
    )
    print(final_prompt)


if __name__ == "__main__":
    main()
