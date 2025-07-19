# Tutor Assistant API

A Django REST API for user authentication, profile management, and a Retrieval-Augmented Generation (RAG) assistant powered by LangChain, FAISS, and LLMs (Mistral 7B locally, DeepSeek in production).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)

---

## Features
- **User Registration, Login, Logout** (JWT-based, with refresh tokens)
- **Profile endpoint** (get user details)
- **RAG Chat endpoint**: POST a prompt, get an LLM-powered answer with textbook context
- **PDF ingestion**: Ingest and index PDFs for context retrieval
- **Dockerized**: Ready for local and production deployment
- **Postgres & Redis**: For scalable, production-ready backend

---

## Repository Structure

```
apps/
  api/           # Auth, profile, JWT logic
  rag_assistant/ # RAG chat, PDF ingest, LLM integration
core/            # Django project settings, URLs
manage.py        # Django entrypoint
requirements.txt # All dependencies
requirements-dev.txt # Dev/test dependencies
pyproject.toml   # Project metadata and tool config
Dockerfile       # Build instructions
docker-compose.yml # Multi-service orchestration
start_api.sh     # Entrypoint script
wait-for-it.sh   # Wait for DB before starting
docs/            # Extended documentation, API reference, usage
notebooks/       # Example Jupyter notebooks
CHANGELOG.md     # Project changelog
CONTRIBUTING.md  # Contribution guidelines
CODE_OF_CONDUCT.md # Community standards
LICENSE          # MIT License
.env.example     # Example environment variables
```

---

## Documentation & Resources
- **[notebooks/usage_example.ipynb](notebooks/usage_example.ipynb)** — Example notebook for API usage
- **[.env.example](.env.example)** — All required environment variables
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — How to contribute
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** — Community standards
- **[CHANGELOG.md](CHANGELOG.md)** — Release history
- **[LICENSE](LICENSE)** — MIT License

---

## Local Development

### 1. Prerequisites
- Docker & Docker Compose
- [LM Studio](https://lmstudio.ai/) running Mistral 7B locally (or any OpenAI-compatible endpoint), do make sure options like CORS and Serve on local network are enabled so API service from docker can send request to it.
  ![alt text](image.png)

### 2. Setup
1. Copy `.env.example` to `.env` and adjust as needed.
2. Place your PDFs in `apps/rag_assistant/management/commands/resources/pdfs/`.
   - During development, you can use a couple of sap manuals, but any PDF document will suffice. Just make sure to use prompts related to the topic of your PDFs so you can see the context retrieval in action.
3. Build and start the stack:
   ```bash
   docker compose up --build
   ```
4. Ingest PDFs (from inside the running container):
   ```bash
   docker compose exec api-rag-assistant python manage.py ingest
   ```

### 3. LLM Setup (Local)
**Note:** This step describes setting up a local LLM for use with the project. While LM Studio with the Mistral 7B model is suggested for local deployment, you are free to use any OpenAI-compatible model, whether hosted locally or in the cloud. If you choose to use a cloud-hosted LLM (such as OpenAI's API), simply provide your API key in the `LLM_API_KEY` environment variable.
- Start LM Studio and run the Mistral 7B model.
- Ensure `.env` has:
  ```env
  LLM_API_URL=http://host.docker.internal:1234/v1/chat/completions
  LLM_MODEL=mistralai/mathstral-7b-v0.1
  LLM_API_KEY=
  ```

---

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
  - Body: `{
  "prompt": "What is a maintenance order in SAP PM and how is it created?"}`

---

## Environment Variables
See [.env.example](.env.example) for all required variables (Postgres, Redis, LLM, Django settings).

---

## Notes
- All tokens are JWT (access/refresh). Store them securely in your client.
- The RAG assistant uses FAISS and LangChain for context retrieval from your ingested PDFs.
- The project is ready for extension (e.g., Celery, more LLMs, etc.).
- Unit tests are yet to be added.
- The project will be possibly deployed and available at emmanuelcodinghub.com, the hardware requirements are being evaluated.

---

## Prompt Customization

The prompt used by the RAG assistant is fully customizable. By default, a template is provided in `apps/rag_assistant/prompt_template.txt`. To customize the prompt for your deployment:

1. **Copy the template:**
   ```bash
   cp apps/rag_assistant/prompt_template.txt apps/rag_assistant/prompt.txt
   ```
2. **Edit `prompt.txt`:**
   Modify `apps/rag_assistant/prompt.txt` as needed. You can change the instructions, tone, or add/remove variables. The placeholders `{context}` and `{user_input}` will be dynamically replaced at runtime with the retrieved context from the vector database and the user's question, respectively.
3. **Usage:**
   The system will load the prompt from `prompt.txt` and use it to construct the message sent to the LLM. If `prompt.txt` is missing, it will fall back to the default `prompt_template.txt`.

This allows you to easily adapt the assistant's behavior and style for different audiences or use cases without changing any code.

---

## Contributing, License, and Community
- Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
- Please review our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating.
- Licensed under the [MIT License](LICENSE).

---

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for release history and major updates.

---

## Citation
If you use this project in your research or product, please cite it as follows:

```
@misc{tutorassistant2025,
  author = {Your Name},
  title = {SAP Assistant API: A Modular RAG Assistant with Django, DRF, and LangChain},
  year = {2025},
  url = {https://github.com/molero3111/tutor-assistant}
}
```

---

## Contact & Support
- For questions, open an issue or discussion on GitHub.
- For feature requests or bug reports, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Quickstart
- Try the [notebooks/usage_example.ipynb](notebooks/usage_example.ipynb) for a hands-on demo.
