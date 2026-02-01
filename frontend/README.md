# Fluid Rower Monitor Frontend

SvelteKit + Tailwind scaffold that talks to the FastAPI backend.

## Prerequisites
- Node.js 18+

## Setup
```bash
npm install
```

## Run dev server
```bash
npm run dev -- --host --port 5173
```
Then open http://localhost:5173 (API defaults to http://localhost:8000).

## Configure API base
Create `.env` and set:
```
PUBLIC_API_BASE=http://localhost:8000
```

## Build
```bash
npm run build
```
