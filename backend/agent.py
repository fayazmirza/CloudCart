import os
import re

# ``langchain_groq`` pulls in ``transformers``; set before that import (also set in ``app.py``).
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from backend.prompt_manager import PromptManager

# Load secrets: project ``cloudcart/.env``, then cwd / process env (python-dotenv default).
_CLOUDCART_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_CLOUDCART_ROOT / ".env")
load_dotenv()

MAX_USER_INPUT_CHARS = 500

# Tell PromptManager where to find our YAML files
base_dir = os.path.dirname(os.path.abspath(__file__))
manager = PromptManager(prompts_dir=os.path.join(base_dir, "prompts"))


def get_course_llm() -> ChatGroq:
    """Shared Groq chat model for the Streamlit app (cached via ``@st.cache_resource`` in ``frontend/app.py``)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not str(api_key).strip():
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to the project `.env` file (repository root of this app) or your environment."
        )
    return ChatGroq(
        groq_api_key=api_key.strip(),
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,
    )


# --- PART B.1: Input Validator ---
def input_validator(text: str) -> Tuple[bool, str]:
    """Checks for prompt injection, PII, and length limits."""
    if len(text) > MAX_USER_INPUT_CHARS:
        return False, f"Input exceeds maximum length of {MAX_USER_INPUT_CHARS} characters."

    if re.search(r"\b(?:\d[ -]*?){13,16}\b", text) or re.search(r"[\w\.-]+@[\w\.-]+", text):
        return False, "PII detected. Please remove sensitive information."

    injection_patterns = ["ignore previous", "system prompt", "bypass", "override", "act as"]
    if any(pattern in text.lower() for pattern in injection_patterns):
        return False, "Potential prompt injection detected. Request blocked."

    return True, "Valid"


# --- PART B.3: Output Validator ---
def output_validator(response_text: str) -> Tuple[bool, str]:
    """Checks the LLM response for policy violations or leaks."""
    lower_response = response_text.lower()

    if (
        "monetary limit" in lower_response
        or "role:" in lower_response
        or "prohibited actions" in lower_response
    ):
        return False, "System instructions leaked in output."

    return True, "Valid"


# --- PART A & B: The Safe Agent Assembly ---
def safe_cloudcart_agent(
    user_input: str,
    *,
    llm: Optional[ChatGroq] = None,
    platform_name: str = "CloudCart",
    support_tier: str = "standard",
) -> Dict[str, Any]:
    """Input validation → hardened prompt + LLM → output checks."""
    is_valid, reason = input_validator(user_input)
    if not is_valid:
        return {
            "status": "input_rejected",
            "response": f"🛡️ Input Blocked: {reason}",
            "reason": reason,
        }

    client = llm if llm is not None else get_course_llm()

    try:
        prompt_data = manager.load_prompt("current")
        context_prefix = (
            f"[Support session: platform={platform_name}, tier={support_tier}]\n\n"
        )
        final_prompt = manager.compile_prompt(prompt_data, context_prefix + user_input)

        response = client.invoke([HumanMessage(content=final_prompt)])

        is_safe_output, out_reason = output_validator(response.content)
        if not is_safe_output:
            issues: List[str] = [out_reason]
            return {
                "status": "output_rejected",
                "response": f"🛡️ Output Blocked: {out_reason}",
                "issues": issues,
            }

        return {"status": "success", "response": response.content}

    except Exception as e:
        return {
            "status": "llm_error",
            "response": "Could not complete the request.",
            "reason": str(e),
        }
