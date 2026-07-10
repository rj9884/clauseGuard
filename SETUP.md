# ClauseGuard - Setup Guide

This guide details the prerequisites, configuration, and execution instructions for running ClauseGuard in both Docker and manual environments.

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| Docker | Latest | Required for Docker container deployment |
| Node.js | v18.0.0+ | Only required for manual (non-Docker) setup |
| Python | 3.10+ | Only required for manual (non-Docker) setup |
| Gemini API Key | | Required for analysis and categorization features |

---

## Environment Configuration

Before launching the application, you must define your environment variables. 

1. Create a `.env` file in the root directory by copying the template:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file and configure your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENROUTER_API_KEY=your_openrouter_key_here
   OPENROUTER_MODEL=openrouter/free
   ```


---

## Deployment Option 1: Docker (Recommended)

Docker Compose builds custom images for the backend and frontend services. The backend container automatically pulls and caches the sentence embedding model during the build phase.

### 1. Build and Run Containers
```bash
docker compose up --build -d
```

### 2. Verify Deployment URLs
* **Frontend Web Client:** http://localhost:5173
* **Backend API Documentation:** http://localhost:8000/docs

### 3. Stopping the Application
```bash
docker compose down
```

---

## Deployment Option 2: Manual Setup (No Docker)

If running without containers, the backend and frontend must be started in separate terminals.

### Terminal 1: Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   * **macOS / Linux:**
     ```bash
     python3 -m venv .venv && source .venv/bin/activate
     ```
   * **Windows (Command Prompt):**
     ```cmd
     python -m venv .venv && .venv\Scripts\activate.bat
     ```
   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv && .venv\Scripts\Activate.ps1
     ```
3. Set the required environment variable:
   * **macOS / Linux:**
     ```bash
     export GEMINI_API_KEY="your_gemini_api_key_here"
     ```
   * **Windows (Command Prompt):**
     ```cmd
     set GEMINI_API_KEY=your_gemini_api_key_here
     ```
   * **Windows (PowerShell):**
     ```powershell
     $env:GEMINI_API_KEY="your_gemini_api_key_here"
     ```
4. Install dependencies and start the server:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
The backend API service will listen on `http://localhost:8000`.

### Terminal 2: Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages and start the development server:
   ```bash
   npm install
   ```
   ```bash
   npm run dev
   ```
The frontend web application will serve on `http://localhost:5173`.

---

## Troubleshooting

| Problem | Potential Cause | Resolution |
|---------|-----------------|------------|
| **Backend not reachable** | API service crash or failed initialization | Check backend service logs using `docker compose logs backend` or verify terminal output in manual execution. |
| **API key errors** | Missing or incorrect `GEMINI_API_KEY` | Ensure that `.env` is populated correctly and the environment variable is loaded in the running terminal context. |
| **Port conflict (5173 or 8000)** | Ports already in use on host | Identify processes occupying the ports and terminate them, or update the port mappings in `docker-compose.yml`. |
| **Docker Permission Denied** | Linux user lacks Docker group privileges | Run `sudo usermod -aG docker $USER`, log out of the system session, and log back in to apply changes. |
| **Script execution errors** | Windows PowerShell execution restriction | Set policies using `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and retry. |
