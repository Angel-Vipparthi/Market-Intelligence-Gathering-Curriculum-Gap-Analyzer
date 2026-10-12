# Market Intelligence & Curriculum Gap Analyzer

An AI-powered system that monitors market trends from web URLs and automatically identifies gaps in your curriculum. It uses LLM agents (via OpenRouter) to digest content, compare it against your knowledge base, and generate actionable gap reports with severity scoring.

## What It Does

1. You add URLs (docs, blogs, changelogs) about technologies you teach
2. The **Digest Agent** reads each URL and extracts market signals (new features, deprecations, trends)
3. You review and approve/reject each digest
4. The **Gap Analyzer Agent** compares approved digests against your curriculum knowledge base
5. It generates gap reports — what's missing, what's outdated, severity scores, and recommended actions
6. You review gaps and decide what to act on
7. The system learns from your feedback to improve future analysis

## Tech Stack

- **Backend:** Python, FastAPI, LangGraph, LangChain
- **Frontend:** React 19, TypeScript, Vite, TailwindCSS, React Query, Zustand
- **Database:** Supabase (PostgreSQL)
- **LLM:** OpenRouter (Claude Sonnet 4 via OpenAI-compatible API)
- **Content Extraction:** Firecrawl
- **Observability:** Langfuse, LangSmith

## Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (free tier works)
- OpenRouter API key
- Firecrawl API key

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Angel-Vipparthi/Market-Intelligence-Gathering-Curriculum-Gap-Analyzer.git
cd Market-Intelligence-Gathering-Curriculum-Gap-Analyzer
```

### 2. Set up the database

Run the migration SQL files in order against your Supabase project:

```bash
# In Supabase SQL Editor, run each file from:
backend/app/db/migrations/001_url_registry.sql
backend/app/db/migrations/002_extracted_content.sql
# ... through 020_url_registry_course_name.sql
```

### 3. Set up the backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env with your actual keys:
#   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
#   OPENROUTER_API_KEY
#   FIRECRAWL_API_KEY
#   LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY (optional, for observability)
```

### 4. Set up the frontend

```bash
cd frontend
npm install
```

### 5. Seed the knowledge base (optional)

If you have curriculum data to load:

```bash
cd backend
python -m scripts.seed_assessments
python -m scripts.populate_graph
```

## Running the App

You need two terminals:

**Terminal 1 — Backend:**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## Pages

| Page | What it does |
|------|-------------|
| **Dashboard** | Overview stats — digests processed, gaps found, severity breakdown |
| **URL Management** | Add/manage URLs to monitor for market signals |
| **Digest Review** | Review AI-generated digests, approve or reject each one |
| **Gap Review** | Review identified curriculum gaps, approve/reject with feedback |
| **Gap Report** | Approved gaps grouped by severity with action timeline |
| **Knowledge Base** | Browse your curriculum — courses, modules, sessions |
| **Knowledge Graph** | Visual graph of curriculum relationships and tool dependencies |
| **Skills** | Agent skills the system has learned |
| **Cost Analytics** | Token usage and cost tracking across workflows |

## Project Structure

```
backend/
  app/
    agents/          # LangGraph agents (digest_agent, gap_agent)
      nodes/         # Individual agent nodes
      prompts/       # Prompt templates
    api/             # FastAPI route handlers
    db/
      migrations/    # SQL migration files (001-020)
    models/          # Pydantic models
    config.py        # Settings from environment
    main.py          # FastAPI app entry point
  scripts/           # Seed and populate scripts

frontend/
  src/
    components/      # Shared UI components
    hooks/           # React Query hooks for each API domain
    lib/             # API client, types, utilities
    pages/           # Page components
```

## Environment Variables

Copy `.env.example` to `backend/.env` and fill in your keys. See the example file for all required and optional variables.

## API Docs

With the backend running, visit http://localhost:8001/docs for the interactive Swagger UI.
