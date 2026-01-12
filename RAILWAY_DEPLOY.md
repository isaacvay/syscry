# Deploying Syscry to Railway

Since your project is a **monorepo** containing both a Next.js frontend (root) and a Python FastAPI backend (`/backend`), you need to create **two separate services** in Railway from the same repository.

## Prerequisites

1.  Make sure your code is pushed to GitHub.
2.  I have already created a `Procfile` in `backend/` to help Railway detect the start command.

## Step 1: Deploy the Backend (Python)

1.  On Railway, click **"New Project"** -> **"Deploy from GitHub repo"**.
2.  Select your `syscry` repository.
3.  Click **"Add Variables"** (or settings usually appear after the first failed build, or you can configure it immediately).
4.  Go to the **Settings** tab of the new service:
    *   **Root Directory**: Set this to `/backend`.
    *   **Watch Paths** (optional): Set to `/backend/**`.
5.  Go to the **Variables** tab and add your environment variables from `backend/.env`:
    *   `BINANCE_API_KEY`
    *   `BINANCE_SECRET_KEY`
    *   `TELEGRAM_BOT_TOKEN`
    *   `TELEGRAM_CHAT_ID`
    *   Any others needed.
6.  Railway should automatically detect the `Procfile` I just added (`web: uvicorn main:app --host 0.0.0.0 --port $PORT`) and start the service.
7.  Once deployed, go to **Settings** -> **Networking** and initialize a domain (e.g., `syscry-backend.up.railway.app`).

## Step 2: Deploy the Frontend (Next.js)

1.  In the same Railway project, click **"New"** -> **"GitHub Repo"**.
2.  Select the **same** `syscry` repository again.
3.  Go to the **Settings** tab of this new service:
    *   **Root Directory**: Leave it as `/` (default).
    *   **Build Command**: Railway usually detects `next build` automatically (`pnpm build`).
    *   **Start Command**: Railway usually detects `next start` automatically (`pnpm start`).
4.  Go to the **Variables** tab and add:
    *   `NEXT_PUBLIC_API_URL`: Set this to the backend domain you created in Step 1 (e.g., `https://syscry-backend.up.railway.app`).
5.  Go to **Settings** -> **Networking** and initialize a domain for your frontend.

## Summary

You will have two services in your Railway project:
1.  **Frontend Service**: Root `/`, calls the backend via `NEXT_PUBLIC_API_URL`.
2.  **Backend Service**: Root `/backend`, handles API requests.

The `Procfile` I added to `backend/` ensures the Python app starts correctly with `uvicorn`.
