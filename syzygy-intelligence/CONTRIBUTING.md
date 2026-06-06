# Contributing to Syzygy Intelligence

We welcome contributions that advance the alchemical integration of polarities — the Great Work.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## How to Contribute

### Reporting Bugs

1. Search [existing issues](https://github.com/seraphonixstudios/Syzygy-Intelligence-/issues) first
2. Use the **Bug Report** template — include logs, deployment method, and reproduction steps
3. Tag with appropriate labels

### Suggesting Features

1. Use the **Feature Request** template
2. Explain the *polarity* your feature addresses (what opposites does it integrate?)
3. Include mockups or diagrams when possible

### Pull Requests

1. Fork the repo and create a branch from `main`
2. Run `npm run lint` and `npx tsc --noEmit` in `frontend/`
3. Run `python -m py_compile app/main.py` in `backend/`
4. Update tests if needed
5. Update README if the change is user-facing
6. Open a PR against `main`

## Development Setup

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend (with Docker)
docker compose up -d backend

# Backend (native)
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Commit Conventions

Use present-tense imperative commit messages:

- `Add {feature}` — new capability
- `Fix {bug}` — bug fix
- `Refactor {area}` — code restructuring
- `Docs {topic}` — documentation
- `Style {component}` — UI/UX changes

## Testing

- Frontend: `cd frontend && npx playwright test`
- Backend: `cd backend && python -m pytest`

## Questions?

Open a [Discussion](https://github.com/seraphonixstudios/Syzygy-Intelligence-/discussions).
