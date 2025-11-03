# Semantic Terrain - Setup Guide

Get started with the Semantic Terrain system in minutes.

## Prerequisites

- **Python 3.10+** ([uv](https://github.com/astral-sh/uv) recommended or pip)
- **Node.js 18+** with npm

## Quick Start

### 1. Backend Setup

**Easiest way (uses uv):**
```bash
.\start-backend-uv.ps1
```

Server runs on `http://localhost:8001`

**Manual setup:** See [server/README.md](server/README.md) for detailed instructions (uv or pip).

### 2. Frontend Setup

```bash
cd web
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

## Troubleshooting

**Backend won't start:**
- Install uv: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
- Or use pip: See [server/README.md](server/README.md)

**Frontend shows black screen:**
- Check backend is running on port 8001
- Check browser console for errors
- Textures auto-generate on first backend run

**Module not found errors:**
- Make sure you run from repo root, not inside `server/`
- Use the provided launcher scripts
