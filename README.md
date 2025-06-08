# Tutor Assistant API

A Django REST API for user authentication, profile management, and a Retrieval-Augmented Generation (RAG) assistant powered by LangChain, FAISS, and LLMs (Mistral 7B locally, DeepSeek in production).

---

## Features
- **User Registration, Login, Logout** (JWT-based, with refresh tokens)
- **Profile endpoint** (get user details)
- **RAG Chat endpoint**: POST a prompt, get an LLM-powered answer with textbook context
- **PDF ingestion**: Ingest and index PDFs for context retrieval
- **Dockerized**: Ready for local and production deployment
- **Postgres & Redis**: For scalable, production-ready backend

---

## Project Structure
```
apps/
  api/           # Auth, profile, JWT logic
  rag_assistant/ # RAG chat, PDF ingest, LLM integration
core/            # Django project settings, URLs
manage.py        # Django entrypoint
requirements.txt # All dependencies
Dockerfile       # Build instructions
start_api.sh     # Entrypoint script
wait-for-it.sh   # Wait for DB before starting
```

---

## Local Development

### 1. Prerequisites
- Docker & Docker Compose
- [LM Studio](https://lmstudio.ai/) running Mistral 7B locally (or any OpenAI-compatible endpoint)

### 2. Setup
1. Copy `.env.example` to `.env` and adjust as needed.
2. Place your PDFs in `apps/rag_assistant/management/commands/resources/pdfs/`.
3. Build and start the stack:
   ```bash
   docker-compose up --build
   ```
4. Ingest PDFs (from inside the running container):
   ```bash
   docker-compose exec api-rag-assistant python manage.py ingest --pdf_dir=apps/rag_assistant/management/commands/resources/pdfs/
   ```

### 3. LLM Setup (Local)
- Start LM Studio and run the Mistral 7B model.
- Ensure `.env` has:
  ```env
  LLM_API_URL=http://host.docker.internal:1234/v1/chat/completions
  LLM_MODEL=mistralai/mathstral-7b-v0.1
  LLM_API_KEY=
  ```

## API Endpoints

### Auth
- `POST /api/register/` — Register (returns access & refresh tokens)
- `POST /api/login/` — Login (returns access & refresh tokens)
- `POST /api/logout/` — Logout (blacklists refresh token)
- `POST /api/token/refresh/` — Get new access token

### Profile
- `GET /api/profile/` — Get user details (JWT required)

### RAG Chat
- `POST /api/rag/chat/` — Send prompt, get LLM answer with context
  - Body: `{ "prompt": "What is photosynthesis?" }`

---

## Environment Variables
See `.env.example` for all required variables (Postgres, Redis, LLM, Django settings).

---

## Notes
- All tokens are JWT (access/refresh). Store them securely in your client.
- The RAG assistant uses FAISS and LangChain for context retrieval from your ingested PDFs.
- The project is ready for extension (e.g., Celery, more LLMs, etc.).