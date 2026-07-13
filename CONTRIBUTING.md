# Contributing to DownTube

Thanks for your interest in improving DownTube! This document explains how to
get set up and what we expect from contributions.

## Code of conduct

Be respectful and constructive. We want DownTube to be a welcoming project.

## Development setup

1. Fork & clone the repo.
2. Backend (Python 3.10+):

   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. Frontend (Node 18+):

   ```bash
   cd frontend
   npm install
   ```

4. Copy `.env.example` to `.env` and adjust paths / credentials.

## Project conventions

- **Backend** is a FastAPI app using a `src`-layout package (`downtube`).
  - Route handlers (under `downtube/api`) must **not** contain business logic;
    put logic in `downtube/services`.
  - Providers are swappable behind a protocol in `downtube/providers`.
- **Frontend** is a Vue 3 + Vite + Tailwind SPA. Keep components small and
  presentational where possible; data access lives in `src/api`.
- Keep it provider-agnostic: YouTube / YouTube Music / Spotify are all
  "providers".
- Follow the existing style (Black for Python, Prettier for TS/Vue).

## Pull requests

- Keep PRs focused on a single concern.
- Add/extend tests for behavior changes (`backend/tests`).
- Ensure CI passes (`lint`, `type-check`, frontend `build`).
- Reference any related issue.

## Reporting issues

Open an issue with: steps to reproduce, expected vs actual behavior, and your
environment (`yt-dlp --version`, `ffmpeg --version`, OS).

## License

By contributing, you agree your contributions are licensed under
[GPL-3.0](./LICENSE).
