"""
CloudCart support UI — Part B ``safe_cloudcart_agent`` (input + LLM + output checks).

Run from ``cloudcart``:

    streamlit run frontend/app.py
"""

from __future__ import annotations

import os

# ``langchain_groq`` imports Hugging Face ``transformers``, which otherwise logs hundreds of
# ``[transformers] Accessing __path__`` WARNING lines. Must be set before that import chain runs.
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

import logging
import sys
from pathlib import Path

# Extra guard: HF loggers attach their own handler when first configured.
logging.getLogger("transformers").setLevel(logging.ERROR)

import streamlit as st

# cloudcart/frontend/app.py → package root is parent directory
_Q1_ROOT = Path(__file__).resolve().parent.parent
if str(_Q1_ROOT) not in sys.path:
    sys.path.insert(0, str(_Q1_ROOT))

from backend.agent import (  # noqa: E402
    MAX_USER_INPUT_CHARS,
    safe_cloudcart_agent,
    get_course_llm,
)


@st.cache_resource
def _cached_llm():
    return get_course_llm()


def main() -> None:
    st.set_page_config(
        page_title="CloudCart Support",
        page_icon="🛒",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.title("🛍️ CloudCart Support")

    user_message = st.text_area(
        "Your question",
        height=160,
        placeholder="e.g. Where can I see my order status?",
        key="cloudcart_question",
    )

    n = len(user_message.strip()) if user_message else 0
    st.caption(f"Length: {n} / {MAX_USER_INPUT_CHARS} characters (inputs over the limit are rejected).")

    if st.button("Submit", type="primary"):
        if not user_message.strip():
            st.warning("Enter your question in the box above, then click **Submit**.")
            return
        try:
            llm = _cached_llm()
        except RuntimeError as exc:
            st.error(str(exc))
            return

        with st.spinner("Contacting support…"):
            result = safe_cloudcart_agent(
                user_message.strip(),
                llm=llm,
                platform_name="CloudCart",
                support_tier="standard",
            )

        status = result.get("status", "unknown")
        response = result.get("response") or ""

        if status == "success":
            st.success("Here's your support reply...👇")
            st.markdown(response)
        elif status == "input_rejected":
            st.error("Sorry, your question was not accepted. Please try again.")
            st.markdown(response)
        elif status == "output_rejected":
            st.error("Reply blocked by output policy")
            issues = result.get("issues") or []
            for issue in issues:
                st.caption(f"• {issue}")
            st.markdown(response)
        elif status == "llm_error":
            st.error("Could not reach the assistant")
            if result.get("reason"):
                st.code(result["reason"], language="text")
            st.markdown(response)
        else:
            st.warning(f"Unknown status: {status!r}")
            st.markdown(response)


if __name__ == "__main__":
    main()
