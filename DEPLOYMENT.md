# Deployment Guide — AuraPrice Dynamic Price Optimization Engine

This document provides complete, step-by-step instructions for deploying the **AuraPrice Platform** to production platforms: **Vercel** and **Render**.

---

## 1. Prerequisites & Environment Variables

### Required Environment Variables
| Variable Name | Description | Default / Example |
|---|---|---|
| `JWT_SECRET_KEY` | Secret key for signing JWT auth tokens. | `generate-a-secure-random-64-char-string` |
| `DATABASE_URL` | Database connection string. | Defaults to SQLite (`sqlite:///./sql_app.db`). Set to PostgreSQL URL on production (e.g. `postgresql://user:pass@host:5432/dbname`). |
| `ENVIRONMENT` | Environment type (`development` or `production`). | `production` |

---

## 2. Deploying to Render (Recommended for Full Backend & Websockets)

Render supports Python FastAPI natively using Docker or native Python runtime with background tasks and persistent database connections.

### Option A: Using `render.yaml` (Infrastructure as Code)
1. Push your code to GitHub / GitLab repository.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **Blueprints** → **New Blueprint Instance**.
4. Connect your GitHub repository.
5. Render will automatically detect `render.yaml` and configure:
   - **Environment**: Python 3.11+
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Auto-generated JWT Secret Key**.
6. Click **Apply**. Render will build and deploy your application.

### Option B: Manual Render Web Service Creation
1. Go to Render Dashboard → **New +** → **Web Service**.
2. Connect your repository.
3. Set the following settings:
   - **Name**: `auraprice-dynamic-pricing`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables under **Advanced**:
   - `JWT_SECRET_KEY`: `<your-secure-random-key>`
   - `DATABASE_URL`: `<your-postgresql-db-url>` (or attach a Render PostgreSQL instance)
5. Click **Create Web Service**.

---

## 3. Deploying to Vercel (Serverless Deployment)

Vercel provides instant global serverless deployment with automated Python API routing.

### Step 1: Pre-configured Files
The repository includes pre-configured Vercel routing:
- `vercel.json` (defines serverless Python routes for `/api/` and static routes for frontend)
- `api/index.py` (WSGI/ASGI entry point exporting the FastAPI app)

### Step 2: Deploy via Vercel CLI
```bash
# 1. Install Vercel CLI globally (if not already installed)
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy to preview environment
vercel

# 4. Deploy to production
vercel --prod
```

### Step 3: Deploy via Vercel Web Dashboard
1. Go to [Vercel Dashboard](https://vercel.com/dashboard) → **Add New Project**.
2. Import your GitHub repository.
3. Leave Framework Preset as **Other**.
4. In **Environment Variables**, add:
   - `JWT_SECRET_KEY` = `<your-secure-random-64-char-key>`
5. Click **Deploy**. Vercel will host your static frontend on CDN and route `/api/*` to the serverless FastAPI backend.

---

## 4. Post-Deployment Verification

Once deployed:
1. Open your production URL (e.g. `https://auraprice.onrender.com` or `https://auraprice.vercel.app`).
2. Register a new merchant store account.
3. Add custom products in the **Product Analyzer**.
4. Run AI optimization inference and simulate dynamic pricing curves!
