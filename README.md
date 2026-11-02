# Enterprise Multi-Agent RAG Assistant

An authenticated document-generation assistant that combines retrieval-augmented generation (RAG), a four-agent Google ADK workflow, human review, source verification, and Markdown/PDF export.

## Goals and current features

The application generates source-grounded documents from private documents and optional web research while isolating each user's data by the authenticated Logto subject.

Current capabilities:

- Four-agent workflow: Researcher, Writer, Fact-Checker, and Editor.
- Google ADK orchestration with Gemini generation and embedding models.
- Central model configuration: change GEMINI_GENERATION_MODEL or GEMINI_EMBEDDING_MODEL in one environment file.
- Text and file ingestion.
- Persistent ChromaDB vector search with SQLite workflow, artifact, source, and citation metadata.
- Optional Tavily web research through a remote MCP endpoint.
- Owner-scoped sources, workflows, artifacts, history, and exports.
- Reviewer-only approve/reject actions.
- Markdown and PDF downloads.
- Logto Traditional Web authentication with encrypted HTTP-only server-side session cookies.
- Next.js server-side backend proxy; browser JavaScript does not receive the FastAPI access token.
- Dark theme by default with a light/dark switch.
- Docker Compose, Kubernetes/Minikube manifests, and GitHub Actions CI.

Normal flow:

1. Visit the Next.js application and sign in through Logto.
2. Add text or upload a document.
3. Submit a document request.
4. Researcher retrieves private chunks and optional web sources.
5. Writer, Fact-Checker, and Editor produce the final document.
6. A reviewer approves or rejects it.
7. Download Markdown or PDF.

## Architecture

~~~text
Browser
  |
  v
Next.js frontend -- Logto Traditional Web -- Logto tenant
  |  encrypted server session
  |  /api/backend/* adds FastAPI access token server-side
  v
FastAPI backend -- OIDC/JWT validation using Logto issuer/JWKS/audience
  |
  +-- ResearchPipeline / Google ADK agents
  |     +-- Researcher: ChromaDB retrieval + optional Tavily MCP
  |     +-- Writer: Gemini generation
  |     +-- Fact-Checker: Gemini generation + source metadata
  |     +-- Editor: Gemini generation
  |
  +-- SQLite: workflows, artifacts, sources, chunks, owner IDs
  +-- ChromaDB: persistent embeddings and chunk documents
~~~

Visiting the root page checks the Logto session and redirects unauthenticated visitors to the sign-in route. FastAPI independently validates bearer tokens.

## Technology versions

| Area | Current technology |
|---|---|
| Backend | Python 3.12+, FastAPI 0.138.0, Uvicorn 0.49.0 |
| Agent framework | Google ADK 2.3.0 |
| Model SDK | Google GenAI 2.9.0 |
| Generation and embeddings | Gemini, selected through environment variables |
| Vector database | ChromaDB 1.x, constrained below 2.0 |
| Metadata database | SQLite and SQLAlchemy 2.0.51 |
| Authentication | Logto Traditional Web, @logto/next 4.2.11, OIDC/JWT |
| Web research | Tavily remote MCP |
| Frontend | Node.js 22+, Next.js 16.2.9, React 19.2.4, TypeScript 5 |
| UI | Tailwind CSS 4 and Lucide React |
| Export | Markdown and ReportLab PDF |
| Deployment | Docker Compose, Kubernetes, Minikube |
| CI | GitHub Actions |

Exact backend packages are in backend/requirements.txt. Exact frontend packages are locked in frontend/package-lock.json.

## Prerequisites

Install:

- Python 3.12 or newer.
- Node.js 22 or newer and npm.
- Git.
- A Google Gemini API key.
- A Logto tenant and Traditional Web application.
- A Tavily API key if web research is required.
- Docker Desktop for Compose.
- Minikube and kubectl only if Kubernetes is required.

Check tools in PowerShell:

~~~powershell
python --version
node --version
npm --version
git --version
docker --version
kubectl version --client
minikube version
~~~

Docker, kubectl, and Minikube are optional for the two-process local run.

### Windows installation options

If Windows Package Manager is available, the core tools can be installed with:

~~~powershell
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Git.Git -e
winget install --id Docker.DockerDesktop -e
winget install --id Kubernetes.kubectl -e
winget install --id Kubernetes.minikube -e
~~~

Docker Desktop, kubectl, and Minikube are optional. Restart PowerShell after installation so the updated PATH is available. If a package ID is unavailable on your machine, install that tool from its official distribution channel and rerun the verification commands above.

## Provider setup

### Gemini

Create a Google AI Studio/Gemini API key and put it in backend/.env as GOOGLE_API_KEY. Choose the generation and embedding models available to your account. The application reads both names centrally from settings.

### Logto

Create a Logto Traditional Web application and configure:

- Redirect URI: http://localhost:3000/api/auth/callback
- Post sign-out redirect URI: http://localhost:3000
- API resource indicator: the same value used by LOGTO_API_RESOURCE and OIDC_AUDIENCE
- At least one test user
- A reviewer role assigned to users who can approve or reject

The current authorization configuration expects this claim:

~~~json
{ "roles": ["reviewer"] }
~~~

If your provider uses another claim or role name, change OIDC_ROLE_CLAIM and OIDC_REVIEWER_ROLE in backend/.env and the Kubernetes configuration.

### Tavily

Create a Tavily API key and set TAVILY_API_KEY. The Researcher connects to TAVILY_MCP_URL, currently https://mcp.tavily.com/mcp/. Web research is optional; private-source retrieval remains available without it.

## Configuration

### Create local environment files

From the repository root:

~~~powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
~~~

Edit both files locally. Never commit them or put real values in the example files.

### Backend environment: backend/.env

| Variable | Required | Purpose |
|---|---:|---|
| GOOGLE_API_KEY | Yes | Gemini API key |
| GEMINI_GENERATION_MODEL | Yes | Generation model; example gemini-2.5-flash |
| GEMINI_EMBEDDING_MODEL | Yes | Embedding model; example gemini-embedding-001 |
| OIDC_ISSUER_URL | Yes | Logto OIDC issuer, normally https://tenant.logto.app/oidc |
| OIDC_JWKS_URL | Yes | Logto signing-key endpoint, normally .../oidc/jwks |
| OIDC_AUDIENCE | Yes | Logto API resource indicator |
| OIDC_AUTHORIZATION_URL | Recommended | OAuth authorization URL for OpenAPI metadata |
| OIDC_TOKEN_URL | Recommended | OAuth token URL for OpenAPI metadata |
| OIDC_ROLE_CLAIM | Yes | Current value: roles |
| OIDC_REVIEWER_ROLE | Yes | Current value: reviewer |
| TAVILY_API_KEY | Optional | Tavily web research key |
| TAVILY_MCP_URL | Optional | Tavily MCP endpoint |
| TAVILY_SEARCH_DEPTH | Optional | Current value: basic |
| SQLITE_PATH | Yes | Local default: backend/database/sqllite.db |
| CHROMA_PERSIST_DIRECTORY | Yes | Local default: backend/database/chroma |
| CHROMA_COLLECTION_NAME | Yes | Current value: rag_chunks |
| CORS_ORIGINS | Yes | Frontend origin, normally http://localhost:3000 |
| DEFAULT_TOP_K | Optional | Retrieved chunk count, default 6 |
| MAX_RETRIES | Optional | Model retry count, default 3 |
| RETRY_DELAY_SECONDS | Optional | Retry delay, default 2 |
| TEMPERATURE | Optional | Generation temperature, default 0.2 |

Relative database paths work from the repository root and backend directory. Docker and Kubernetes replace them with container paths.

### Frontend environment: frontend/.env.local

| Variable | Required | Purpose |
|---|---:|---|
| NEXT_PUBLIC_API_URL | Yes | Browser-facing API reference; local default http://localhost:8000 |
| BACKEND_INTERNAL_URL | Yes | Server-side proxy target; local default http://localhost:8000 |
| LOGTO_APP_ID | Yes | Logto application ID |
| LOGTO_APP_SECRET | Yes | Logto application secret; server-side only |
| LOGTO_ENDPOINT | Yes | Logto tenant endpoint |
| LOGTO_BASE_URL | Yes | Frontend base URL; local default http://localhost:3000 |
| LOGTO_COOKIE_SECRET | Yes | Strong secret used to encrypt the session cookie |
| LOGTO_API_RESOURCE | Yes | API resource requested by the frontend |

LOGTO_API_RESOURCE must equal OIDC_AUDIENCE. The base URL, redirect URI, and browser URL must use the same host and port.

Generate a cookie secret if needed:

~~~powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
~~~

Do not add NODE_TLS_REJECT_UNAUTHORIZED=0. It disables TLS verification and is not a valid Logto fix.

## Run locally

### Start the backend

Open PowerShell 1:

~~~powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
~~~

The backend runs at http://localhost:8000.

If PowerShell blocks activation:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
~~~

### Start the frontend

Open PowerShell 2:

~~~powershell
cd frontend
npm ci
npm run dev
~~~

Open http://localhost:3000. The expected sequence is:

1. Next.js checks the server-side Logto session.
2. An unauthenticated visitor is redirected to Logto.
3. Logto returns to /api/auth/callback.
4. The workspace renders after the session is established.

For a production-mode local check:

~~~powershell
cd frontend
npm run build
npm run start
~~~

Use /api/auth/sign-in to restart login manually. Do not open the callback URL directly.

## Use the application

### Add source material

The workspace supports plain text ingestion and document upload. Upload support currently includes `.txt`, `.md`, and `.pdf`. Ingestion chunks content, creates Gemini embeddings, writes vectors to ChromaDB, and stores source metadata in SQLite. Sources are owned by the authenticated Logto sub.

### Generate a document

Enter one concise request, for example:

~~~text
Create an executive briefing on the uploaded security policy. Include key controls, risks, evidence citations, and an implementation checklist.
~~~

Researcher retrieves relevant private chunks and optional web sources. Writer, Fact-Checker, and Editor then create the final document.

### Review and export

- Authenticated owners can view their own workflows and artifacts.
- Only users containing the configured reviewer role can approve or reject.
- Markdown and PDF downloads are available when an editor artifact exists.
- History and proof-source links are owner-scoped.
- Dark theme is the default; the workspace includes a light/dark switch.
- Logout is handled through the Logto sign-out route.

## API reference

With the backend running:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health: GET /health

| Method | Path | Authentication | Purpose |
|---|---|---|---|
| POST | /rag/ingest-text | Bearer token | Add text to the user's RAG collection |
| POST | /rag/ingest-file | Bearer token | Upload and index a supported document |
| POST | /workflow/run | Bearer token | Run the multi-agent workflow |
| GET | /workflows | Bearer token | List the user's workflows |
| GET | /workflows/{id}/artifacts | Bearer token | Retrieve owner-scoped artifacts |
| POST | /workflow/approve | Bearer token + reviewer role | Approve an owned workflow |
| POST | /workflow/reject | Bearer token + reviewer role | Reject an owned workflow |
| GET | /workflows/{id}/export/markdown | Bearer token | Download Markdown |
| GET | /workflows/{id}/export/pdf | Bearer token | Download PDF |
| POST | /chat | No auth in current implementation | Direct generation helper endpoint |

The frontend normally calls protected backend routes through /api/backend/*. Do not store a backend token in browser storage.

Health check:

~~~powershell
Invoke-WebRequest http://localhost:8000/health | Select-Object -ExpandProperty Content
~~~

## Data and persistence

Generated data is stored under backend/database/:

- sqllite.db: workflows, artifacts, sources, chunks, and owner relationships.
- chroma/: persistent embeddings and chunk documents.

The application initializes the SQLite schema on startup and adds current owner columns when an older database is encountered. Existing ownerless records are retained for migration safety but are not visible to authenticated users until explicitly assigned.

Back up SQLite and Chroma together. Restoring only one can create mismatched metadata and vectors.

## Docker Compose

Install and start Docker Desktop. From the repository root:

~~~powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
# Edit both files with real provider values.
docker compose config
docker compose up --build
~~~

Open http://localhost:3000; the backend is at http://localhost:8000. Compose waits for the backend health check and persists SQLite/Chroma in the named backend-data volume.

Useful commands:

~~~powershell
docker compose ps
docker compose logs -f backend frontend
docker compose down
~~~

To remove the persistent volume as well (this deletes local application data):

~~~powershell
docker compose down -v
~~~

Inside Compose, the frontend uses BACKEND_INTERNAL_URL=http://backend:8000; localhost inside a container refers to that container.

## Kubernetes and Minikube

The manifests are for local evaluation: one backend replica, one frontend replica, a PVC, a ConfigMap, and a Secret template. They are not a production cluster security model.

### Build and deploy

~~~powershell
minikube start
minikube status
minikube image build -t enterprise-rag-backend:latest ./backend
minikube image build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t enterprise-rag-frontend:latest ./frontend
Copy-Item k8s/secret.example.yaml k8s/secret.local.yaml
# Edit k8s/secret.local.yaml and fill real values; never commit it.
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.local.yaml
kubectl apply -f k8s/backend-pvc.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
~~~

The Kubernetes secret must include Gemini, OIDC, Logto, and optional Tavily values. Update Logto URLs and CORS_ORIGINS if the application is accessed through a different host.

### Verify and access

~~~powershell
kubectl apply --dry-run=client -f k8s
kubectl -n enterprise-rag get pods,services,pvc
kubectl -n enterprise-rag rollout status deployment/rag-backend
kubectl -n enterprise-rag rollout status deployment/rag-frontend
kubectl -n enterprise-rag logs deployment/rag-backend
kubectl -n enterprise-rag port-forward service/rag-backend 8000:8000
~~~

In another terminal:

~~~powershell
kubectl -n enterprise-rag port-forward service/rag-frontend 3000:3000
~~~

Open http://localhost:3000. For an unhealthy pod:

~~~powershell
kubectl -n enterprise-rag describe pod <pod-name>
kubectl -n enterprise-rag logs <pod-name> --previous
~~~

## Tests and GitHub Actions

### Run checks locally

Backend:

~~~powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python -m compileall agents api config database orchestrator security services tools
~~~

Frontend:

~~~powershell
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build
~~~

### GitHub Actions workflow

.github/workflows/ci.yml runs on pushes to main and pull requests. It performs:

- Python 3.12 setup and backend dependency installation.
- Backend python -m pytest -q.
- Node.js 22 setup and frontend npm ci.
- Frontend ESLint.
- Frontend TypeScript type-checking.
- Frontend Next.js production build.

CI uses a placeholder Gemini key so tests do not require a live Gemini request. It does not perform live Logto, Gemini, Tavily, Docker, Kubernetes, or deployment tests.

Push changes:

~~~powershell
git status
git add .
git commit -m "Update application"
git push origin <branch-name>
~~~

Open GitHub's Actions tab and select CI. A green run confirms automated checks passed; perform an authenticated smoke test separately.

## Troubleshooting

### Sign-in session not found

This means a callback URL was opened directly, a stale callback was reused, or temporary Logto transaction state no longer exists.

1. Open http://localhost:3000/api/auth/sign-in.
2. Complete login from Logto.
3. Confirm the callback URI is exactly http://localhost:3000/api/auth/callback.
4. Confirm LOGTO_BASE_URL=http://localhost:3000.
5. Clear cookies for localhost:3000 if the old session is stuck.
6. Restart Next.js after changing frontend/.env.local.

The callback handler restarts sign-in for stale/direct callback failures. Do not use NODE_TLS_REJECT_UNAUTHORIZED=0.

### Frontend authentication configuration errors

Check LOGTO_APP_ID, LOGTO_APP_SECRET, LOGTO_ENDPOINT, LOGTO_BASE_URL, LOGTO_COOKIE_SECRET, and LOGTO_API_RESOURCE. Restart Next.js after editing frontend/.env.local.

### Backend 401, 403, or 503

- 401: missing, expired, incorrectly signed, or incorrectly scoped token.
- 403: reviewer role is missing for approve/reject.
- 503: OIDC configuration is missing or the JWKS endpoint cannot be reached.

Verify that LOGTO_API_RESOURCE equals OIDC_AUDIENCE, issuer and JWKS belong to the same tenant, and the user has the expected role claim.

### Docker frontend cannot reach backend

Inside Compose, use BACKEND_INTERNAL_URL=http://backend:8000, not localhost. Rebuild after changing build arguments or environment values:

~~~powershell
docker compose build --no-cache
docker compose up
~~~

### Kubernetes pod is not ready

~~~powershell
kubectl -n enterprise-rag get pods,pvc
kubectl -n enterprise-rag describe pod <pod-name>
kubectl -n enterprise-rag logs <pod-name>
~~~

### Model changes do not take effect

Change only the model variables in backend/.env and restart the backend. For Docker/Kubernetes, update the environment source and recreate or roll out the workload. Agents and the RAG engine read these settings centrally.

## Security and production checklist

Before deploying beyond local development:

- Use HTTPS and update all Logto redirect/sign-out URLs.
- Generate a strong unique LOGTO_COOKIE_SECRET.
- Keep .env files, filled Kubernetes secrets, tokens, and database/vector files out of Git.
- Use a managed secret store instead of committing k8s/secret.local.yaml.
- Set explicit production CORS_ORIGINS; do not use a wildcard with credentials.
- Use production persistent storage and back up SQLite and Chroma together.
- Rotate Gemini, Tavily, and Logto credentials if exposed.
- Verify issuer, audience, JWKS, token expiry, and reviewer role before enabling approvals.
- Run CI and an authenticated smoke test after deployment.
- Treat uploaded sources and generated documents as sensitive data.

## Repository layout

~~~text
backend/
  agents/                 Researcher, Writer, Fact-Checker, Editor
  adk/                    Google ADK registration and execution helpers
  api/                    Chat, history, and export routers
  config/                 Settings, constants, logging, prompt loading
  database/               SQLite persistence
  orchestrator/           Multi-agent pipeline
  security/               OIDC/JWT validation and reviewer authorization
  services/               Gemini, RAG, Markdown, and PDF services
  tests/                  Backend tests
  tools/                  Tavily MCP integration
  .env.example            Backend configuration template
  Dockerfile              Backend image
frontend/
  app/                    Next.js pages, workspace, auth, and proxy routes
  components/hooks/       Workspace UI and workflow helpers
  types/utils/            Frontend types and download/error helpers
  .env.example            Frontend configuration template
  Dockerfile              Frontend production image
k8s/                      Kubernetes namespace, deployments, services, PVC, config, secret template
.github/workflows/ci.yml  GitHub Actions validation pipeline
docker-compose.yml        Local multi-container deployment
~~~

## License

This is an open-source repository built only for pure Educational purpose.