# Web Architecture Guide

## Overview

This guide establishes the architectural patterns for adding a web interface to Vibe Coding projects. The goal is "Progressive Disclosure"—allowing simple scripts to evolve into full apps without rewrite.

## Core Rules

### 1. Headless-First
**Principle:** The API is the product; the UI is just a consumer.
-   Build your backend logic (FastAPI/Flask) as a standalone API first.
-   Ensure your model/logic can be run via CLI or Cron without the web server.
-   *Why?* Decoupling ensures your core logic remains portable and testable.

### 2. Component Silo
**Principle:** The Frontend must never touch the Database directly.
-   **Forbidden:** Importing `src.db` or `pd.read_csv` directly in a Next.js component.
-   **Required:** Fetch data via the API (`/api/v1/...`).
-   *Why?* Direct DB access from UI components creates a monolithic web of dependencies that is hard to refactor.

### 3. Server-Side State Strategy
**Principle:** Prefer Server State tools over complex Client State stores.
-   **Recommended:** TanStack Query (React Query) or SWR.
-   **Discouraged:** Redux, mobx, or heavy Zustand stores for simple data fetching.
-   *Why?* "Vibe coding" often leads to over-engineered state management. Keep it simple: invalidating a query is easier than managing a reducer.

## Recommended Stack

| Layer | Tool | Note |
|-------|------|------|
| **Backend** | FastAPI | Type-safe, auto-docs (OpenAPI) |
| **Frontend** | Vite + React | fast, simple build tool |
| **API Client** | TanStack Query | For caching and state |
| **Styling** | Tailwind | Utility-first (if preferred) |

## Directory Structure

```text
project/
├── src/                # Backend / Core Logic
│   ├── api/            # FastAPI Routers
│   └── processing/     # Data Logic
├── ui/                 # Frontend (New Directory)
│   ├── src/
│   │   ├── components/
│   │   └── hooks/      # useQuery hooks
│   └── package.json
└── docs/
    └── guides/
        └── web_architecture.md
```
