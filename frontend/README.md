# StratOS AI — Frontend

React + TypeScript foundation for the StratOS AI enterprise UI. See the root [README.md](../README.md) for how to run this alongside the backend.

## Stack

- React 19 + TypeScript
- Vite (build tool / dev server)
- React Router (page navigation)
- Tailwind CSS v4 (styling)

## Structure

```
src/
├── api/            # Backend API calls (fetch wrappers)
├── components/
│   ├── layout/      # Sidebar, page layout/shell
│   └── engineers/    # Engineers-page-specific components
├── pages/           # Route-level pages (Dashboard, Engineers, Projects)
├── types/           # Shared TypeScript types
├── App.tsx          # Route definitions
└── main.tsx          # Entry point
```

## Environment

Copy `.env.example` to `.env` and point `VITE_API_BASE_URL` at your running FastAPI backend (defaults to `http://localhost:8000`).

## Scripts

```bash
npm install     # install dependencies
npm run dev     # start the dev server (http://localhost:5173)
npm run build   # type-check and build for production
npm run preview # preview the production build locally
```
