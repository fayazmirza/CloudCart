# CloudCart — Prompt management with LLM

**CloudCart** is a small e-commerce support demo for a GenAI **Question 1**–style lab. It is meant to practice **prompt-injection awareness**, **input and output validation** around a **safe agent-style** pipeline, and **versioned YAML prompts** via **`PromptManager`**. Prompts are built from **layered YAML** (role, constraints, context, examples, top/bottom security guards) and **compiled into one string** for `HumanMessage`—this repo does **not** use LangChain **`ChatPromptTemplate`** or **`.partial()`**; you can combine those patterns separately if you extend the app.

**Runtime:** When **`GROQ_API_KEY`** is set, the app calls **Groq** with **`llama-3.3-70b-versatile`** through LangChain **`ChatGroq`** (temperature **0.3** in `get_course_llm`). There is **no** built-in “mock LLM” fallback in this code path: without a key, **`get_course_llm`** raises and the Streamlit UI shows that error. For **offline** use, run **`backend/test_loading.py`** to load and print a compiled prompt without contacting Groq.

The UI calls **`safe_cloudcart_agent`** in **`backend/agent.py`**, which loads **`backend/prompts/current.yaml`**, prepends a short session context (platform / tier), and returns structured statuses for the UI.

## What it does

| Stage | Behavior |
|--------|----------|
| **Input** | Max **500** characters; blocks common **injection** phrases; blocks likely **PII** (long digit runs like card numbers, email-shaped strings). |
| **Prompt** | YAML defines **role**, **constraints**, **context**, **examples**, and **security** top/bottom guards; `compile_prompt` builds one string (sandwich-style guards). |
| **Model** | `llama-3.3-70b-versatile` via **LangChain** `ChatGroq`, temperature **0.3** (see `get_course_llm` in `backend/agent.py`). |
| **Output** | Rejects replies that look like **system-instruction leaks** (e.g. phrases related to internal limits / prohibited actions / `role:`). |

Returned payloads use `status`: `success`, `input_rejected`, `output_rejected`, or `llm_error` (see `frontend/app.py` for how each is shown).

## Project structure

Relevant paths under this repository (clone or folder is typically named **`cloudcart/`**).

```text
cloudcart/
├── .gitignore           # ignores .env, __pycache__, etc.
├── README.md
├── requirements.txt
├── .env                 # local only; create from your keys (not committed)
├── frontend/
│   └── app.py           # Streamlit UI
└── backend/
    ├── agent.py         # validators, safe_cloudcart_agent, ChatGroq factory
    ├── prompt_manager.py
    ├── test_loading.py  # offline YAML smoke test
    └── prompts/
        ├── current.yaml # active prompt (v1.2.0 CloudCart content in repo)
        ├── v1.0.0.yaml
        └── v1.1.0.yaml
```

| Path | Role |
|------|------|
| `frontend/app.py` | Streamlit UI; adds `cloudcart` to `sys.path`, caches the LLM with `@st.cache_resource`. |
| `backend/agent.py` | Env loading, validators, `safe_cloudcart_agent`, Groq client factory. |
| `backend/prompt_manager.py` | Load versioned YAML, `compile_prompt`, `get_version_history`. |
| `backend/prompts/` | `current.yaml` (active prompt; may be a symlink to `v*.yaml` on your machine) and versioned files such as `v1.0.0.yaml`, `v1.1.0.yaml`. |
| `backend/test_loading.py` | Smoke test: load `current`, print metadata and a compiled prompt preview (**no API key**). |
| `requirements.txt` | Minimal dependencies to run this folder alone. |
| `.gitignore` | Keeps `.env` and other local/bytecode files out of Git. |
| `.env` | **Local** secrets (not committed); see Setup. |

## Setup

1. **Python** — use Python **3.10+** and a virtual environment, then from the repository root:

   ```bash
   pip install -r requirements.txt
   ```

2. **Secrets** — create or edit `.env` in this folder with:

   ```bash
   GROQ_API_KEY=your_key_here
   ```

   In `backend/agent.py`, `load_dotenv` loads **`<repo>/.env`** first, then **`load_dotenv()`** with no path (which may pick up a `.env` in your **current working directory**). With python-dotenv’s default **`override=False`**, variables already present in the process environment are left as-is, and values from an **earlier** successful load are not overwritten by a later one.

3. **Run the app** — working directory should be the **repository root** (so imports resolve):

   ```bash
   streamlit run frontend/app.py
   ```

   Alternatively:

   ```bash
   cd frontend
   streamlit run app.py
   ```

## Smoke test (prompts only)

No Groq key required; only reads YAML and prints a compiled prompt preview.

From the **repository root**:

```bash
python backend/test_loading.py
```

From **`backend/`**:

```bash
python test_loading.py
```

## Prompt versions

- **`PromptManager.load_prompt("current")`** reads `backend/prompts/current.yaml`.
- **`load_prompt("v1.1.0")`** reads `backend/prompts/v1.1.0.yaml`.
- **`get_version_history()`** lists stems of all `v*.yaml` files in `backend/prompts/`.

To point **`current`** at another version (from `backend/prompts/`):

```bash
ln -sf v1.1.0.yaml current.yaml
```

(On Windows, copy or recreate the symlink with your shell’s equivalent.)

## Notes

- Do **not** commit real API keys. Keep them in **`.env`** locally. This repo’s **`.gitignore`** ignores `.env` (and allows **`!.env.example`** if you add a template file).
- **`v1.0.0`** uses a **₹5000** auto-refund ceiling (two examples). **`v1.1.0`** and **`current` (1.2.0)** use **₹6000** and richer context; pick a file when comparing prompt versions.
