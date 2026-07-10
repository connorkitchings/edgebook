---
name: web-init
description: "Initialize a new web project structure with frontend and backend scaffolding."
metadata:
  trigger-keywords: "init web, create web app, setup frontend, web project, frontend setup"
  trigger-patterns: "^init.*web, ^create.*web, ^setup.*frontend"
---

# Web Project Initialization Skill

Use this skill when creating a new web application project from scratch.

---

## When to Use

- Starting a new web application project
- Need both frontend and backend structure
- Want consistent project layout from the start

**Do NOT use when:**
- Extending an existing web project (use feature development instead)
- Only need API changes without frontend

---

## Inputs

### Required
- **Project name**: Name of the web application
- **Frontend framework**: React, Vue, Svelte, or vanilla JS
- **Backend framework**: FastAPI, Flask, Express, or other

### Optional
- **Authentication**: Include auth setup (default: False)
- **Database**: Include database config (default: False)
- **CSS framework**: Tailwind, Bootstrap, or custom (default: Tailwind)

---

## Steps

### Step 1: Create Project Structure

**What to do:**
Set up the directory structure for the web project.

**Commands:**
```bash
mkdir -p {project_name}/{frontend,backend,shared}
cd {project_name}
git init
```

**Directory layout:**
```
{project_name}/
├── frontend/          # Frontend application
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/           # Backend API
│   ├── src/
│   ├── tests/
│   └── requirements.txt
├── shared/            # Shared types/configs
│   └── types/
├── docs/              # Documentation
└── README.md
```

**Validation:**
- [ ] Directory structure created
- [ ] Git initialized

---

### Step 2: Initialize Frontend

**What to do:**
Set up the frontend framework with basic configuration.

**Commands (React example):**
```bash
cd frontend
npx create-react-app . --template typescript
# OR for Vite:
npm create vite@latest . -- --template react-ts
```

**Add CSS framework (Tailwind):**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Update tailwind.config.js:**
```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

**Validation:**
- [ ] Frontend builds without errors: `npm run build`
- [ ] CSS framework configured
- [ ] Development server runs: `npm start` or `npm run dev`

---

### Step 3: Initialize Backend

**What to do:**
Set up the backend API with FastAPI (Python) or Express (Node).

**Commands (FastAPI example):**
```bash
cd ../backend
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
EOF

pip install -r requirements.txt
```

**Create main.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{project_name} API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Validation:**
- [ ] Backend starts: `uvicorn main:app --reload`
- [ ] Health endpoint returns 200: `curl http://localhost:8000/health`

---

### Step 4: Configure CORS

**What to do:**
Ensure frontend can communicate with backend during development.

**Backend (already done in Step 3):**
- CORS middleware configured for localhost:3000

**Frontend:**
Create `src/api/client.ts`:
```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
}
```

**Validation:**
- [ ] Frontend can call backend endpoint successfully
- [ ] No CORS errors in browser console

---

### Step 5: Add Shared Types (Optional)

**What to do:**
Create shared type definitions for consistency.

**Create shared/types/index.ts:**
```typescript
export interface User {
  id: string;
  email: string;
  name: string;
}

export interface ApiResponse<T> {
  data: T;
  status: string;
}
```

**Backend (Pydantic models):**
```python
from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    name: str

class ApiResponse(BaseModel):
    data: dict
    status: str
```

**Validation:**
- [ ] Types are consistent between frontend and backend
- [ ] No TypeScript errors in frontend
- [ ] Pydantic models validate correctly

---

### Step 6: Setup Development Scripts

**What to do:**
Create convenient scripts for running both services.

**Create root package.json:**
```json
{
  "name": "{project_name}",
  "version": "1.0.0",
  "scripts": {
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
    "dev:frontend": "cd frontend && npm start",
    "dev:backend": "cd backend && uvicorn main:app --reload",
    "build": "cd frontend && npm run build",
    "test": "npm run test:frontend && npm run test:backend",
    "test:frontend": "cd frontend && npm test",
    "test:backend": "cd backend && pytest"
  },
  "devDependencies": {
    "concurrently": "^8.0.0"
  }
}
```

**Validation:**
- [ ] `npm install` installs dependencies
- [ ] `npm run dev` starts both services
- [ ] Both services are accessible

---

## Validation

### Success Criteria
- [ ] Frontend builds and runs on localhost:3000
- [ ] Backend runs on localhost:8000
- [ ] Frontend can successfully call backend API
- [ ] No CORS errors
- [ ] Both services have health check endpoints
- [ ] README.md documents how to run the project

### Verification Commands
```bash
# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000  # Should return HTML

# Test CORS
curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

---

## Common Mistakes

1. **Forgetting CORS**: Always configure CORS for development
2. **Port conflicts**: Ensure frontend (3000) and backend (8000) don't clash
3. **Missing .gitignore**: Add node_modules, __pycache__, .venv to .gitignore
4. **No README**: Document how to run the project

---

## Links

- Context: `.agent/CONTEXT.md`
- Agent Guidance: `.agent/AGENTS.md`
- API Development: `.agent/skills/api-endpoint/SKILL.md`
- Frontend Development: `.agent/skills/CATALOG.md` (if available)
