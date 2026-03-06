# AtomeBot

AtomeBot is an AI customer support workspace for Atome use cases.

Repository:

- https://github.com/zzybluebell/TA-atome-bot

## Product Scope

- Uses RAG over Atome help-center content
- Supports tool-based support actions (mocked)
- Lets managers update behavior rules in real time
- Supports knowledge-doc upload with relevance filtering

## User Types

### User Type A: Beginner End User

- Use only the packaged software file:
  - `mac_build/AtomeDesk-macOS.zip`
- End users do not need to read code, configure backend, or run terminal commands.
- End users only need to double-click `AtomeDesk` after unzipping.
- If the app prompts for runtime support, install/open Docker Desktop once and launch again.

### User Type B: Professional Developer

- Docker workflow is for developers only.
- Clone repository and run the full stack for development, debugging, and code changes.

## Beginner Usage (No Code Workflow)

1. Get `AtomeDesk-macOS.zip`.
2. Double-click to unzip.
3. Open `AtomeDesk` folder.
4. Double-click `AtomeDesk`.
5. Browser opens to `http://localhost:5173`.

## Developer Usage (Docker)

### Prerequisites

- macOS
- Docker Desktop
- OpenAI API key

### Steps

```bash
git clone https://github.com/zzybluebell/TA-atome-bot.git
cd TA-atome-bot
```

Create API key file from template:

```bash
cp atome-bot/backend/.env.example atome-bot/backend/.env
```

Then edit with your own api key:

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

Start (hot-reload mode, bind mounts):

```bash
docker compose up --build
```

If Docker Desktop reports mount permission errors on macOS, use no-volume mode:

```bash
docker compose -f docker-compose.yml -f docker-compose.novolumes.yml up --build
```

Open:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

Stop:

```bash
docker compose down
```

### Docker Troubleshooting (macOS)

- Error example: `error while creating mount source path ... operation not permitted`
- Cause: Docker Desktop cannot mount your project folder from host.
- Fix A (recommended): run no-volume mode
  - `docker compose -f docker-compose.yml -f docker-compose.novolumes.yml up --build`
- Fix B: allow folder sharing in Docker Desktop
  - Docker Desktop → Settings → Resources → File Sharing
  - Add your project parent folder (for example `/Users/<you>/Downloads`)
- Fix C: if still blocked, grant Full Disk Access to Docker Desktop in macOS Privacy settings, then restart Docker Desktop.
- If backend shows `ImportError` around `langchain.agents`:
  - Pull latest code and rebuild images:
  - `git pull && docker compose build --no-cache && docker compose up`

## Developer Usage (Without Docker)

Python requirement for local mode: 3.10 / 3.11 / 3.12.

```bash
./dev_setup.sh
```

Then:

```bash
cd atome-bot/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

In a new terminal:

```bash
cd atome-bot/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

## Developer Helper Script (`start.sh`)

- `start.sh` is a developer convenience script for local runs.
- It checks whether `atome-bot/backend/.env` already contains an OpenAI key.
- It starts backend (`uvicorn`) and frontend (`npm run dev`) together in one terminal.
- It tracks child process IDs and stops both services automatically when you exit (`Ctrl + C`).
- Use it only after local dependencies are already installed:
  - backend virtual environment is ready
  - frontend packages are installed

## Current Web Rules

- Upload supports `.pdf`, `.docx`, `.txt`, `.md`
- Max upload count is 10 files per request
- Max file size is 10MB per file
- Encrypted PDFs are rejected
- Replace mode clears existing vector knowledge first
- Refresh URL triggers full recrawl and re-index
- Apply Instruction updates system guidelines immediately

## Project Structure

- `atome-bot/backend/`: FastAPI + LangChain + ChromaDB
- `atome-bot/backend/.env.example`: environment variable template for developers
- `atome-bot/frontend/`: React + Vite + Tailwind
- `docker-compose.yml`: developer docker stack
- `docker-compose.novolumes.yml`: docker override without host mounts
- `dev_setup.sh`: developer local setup script
- `start.sh`: one-terminal local dev startup (backend + frontend)

## AI Assistance Disclosure

- This project used AI-assisted development support.
- LLM used: GPT-5.3.
- IDE used for AI-assisted development: Trae IDE.
