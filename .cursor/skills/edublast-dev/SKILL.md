---
name: edublast-dev
description: >-
  Multi-project development, testing, and operations runbook for the EduBlast repository.
  Use this skill when developing, building, testing, linting, syncing environment variables,
  or managing Supabase configurations across EduBlast subprojects (Web, EduDeca, and EduBite).
---

# EduBlast Multi-Project Development Runbook

EduBlast is composed of three interconnected Next.js applications sharing a single Supabase backend and user authentication pool:

| Project | Port | Framework | Role |
|---------|------|-----------|------|
| **`Web`** | `3000` | Next.js 16 (React 19) | Main Edublast platform, curriculum, exams, and shared Supabase migration source. |
| **`EduDeca`** | `3001` | Next.js 16 (React 19) | Gamified challenge platform for Class 11 & 12 students, level timeline, leaderboards. |
| **`EduBite`** | `3000` / `dev:clean` | Next.js 15 (React 19) | Daily learning companion (DailyDose, FunBrain, Brain Gym, Puzzles, AI pledges). |

---

## 1. Environment Synchronization (`sync:sibling-env`)

`Web/.env` acts as the source of truth for the shared Supabase project credentials and outbound email settings. Whenever Supabase credentials or email variables change, synchronize them to sibling projects:

```bash
cd Web
npm run sync:sibling-env
```

### What this does
- Reads `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` from `Web/.env`.
- Generates/updates `.env` and `.env.local` inside `EduBite/` and `EduDeca/`.
- Propagates shared email server credentials to `EduDeca/`.
- Ensures `EDUDECA_INTERNAL_API_SECRET` is synchronized for internal service-to-service communication.
- Validates that the keys are in parity across all three environments (`URL=linked`, `ANON=linked`, `SERVICE=linked`, etc.).

---

## 2. Running Development Servers

### Standalone Servers
- **Main Web Platform**:
  ```bash
  cd Web
  npm run dev          # Uses custom Webpack launcher (scripts/dev-webpack.cjs)
  # or
  npm run dev:turbo    # Runs next dev --turbopack on port 3000
  ```

- **EduDeca Platform**:
  ```bash
  cd EduDeca
  npm run dev          # Runs on port 3001 with Turbopack (--turbopack -p 3001)
  ```

- **EduBite**:
  ```bash
  cd EduBite
  npm run dev          # Runs on port 3000 (ensure Web is on a different port or stopped)
  # or
  npm run dev:clean    # Kills stuck ports and cleans .next cache before launching
  ```

### Resolving Port & Cache Conflicts
- If port 3000 or 3001 is stuck:
  ```bash
  node EduBite/scripts/kill-dev-ports.mjs
  ```
- If `.next` build cache is corrupted:
  - In `Web`: `npm run clean:next` or `npm run dev:fresh`
  - In `EduBite`: `npm run dev:clean`
- If SQLite native binding fails in `Web`:
  ```bash
  cd Web
  npm run rebuild:sqlite
  ```

---

## 3. Supabase Migrations & Content Seeding

### Supabase Schema Management
The primary Supabase schema migrations reside in `Web/supabase/`:
- Push migrations to the remote database:
  ```bash
  cd Web
  npm run supabase:push
  ```
- Regenerate TypeScript types from database schema:
  ```bash
  cd Web
  npm run supabase:types
  ```

### EduBite Content Banks & Seeds
EduBite questions and game states are housed in dedicated tables prefixed with `edubite_*` (never mixed with Edublast `play_questions`):
- Import Class 11 & 12 PCM Daily Dose banks:
  ```bash
  cd EduBite
  npm run import:pcm-daily-dose
  ```
- Import FunBrain questions:
  ```bash
  cd EduBite
  npm run import:funbrain
  ```
- Seed AI pledges and inspiration quotes:
  ```bash
  cd EduBite
  npm run seed:pledges:am
  npm run seed:pledges:pm
  npm run seed:inspiration
  npm run seed:role-models
  ```

### EduDeca Seeding & Question Extraction
EduDeca contains DOCX parsing and seed generation scripts in `EduDeca/scripts/`:
- Test parsing docx question pools:
  ```bash
  python EduDeca/scripts/parse_discipline_bank_docx_test.py
  ```

---

## 4. Testing & Verification

Run project-specific test suites before opening PRs or merging code:

### Web
- **Vitest Unit & Integration Tests**:
  ```bash
  cd Web
  npm test
  ```
- **Linting & Code Formatting**:
  ```bash
  cd Web
  npm run lint
  npm run format:check
  ```

### EduDeca
- **Node Test Runner Suite**:
  ```bash
  cd EduDeca
  npm test
  ```
- **TypeScript Verification**:
  ```bash
  cd EduDeca
  npm run typecheck
  npm run lint
  ```

### EduBite
- **Feature Tests**:
  ```bash
  cd EduBite
  npm run test:brain-gym
  npm run test:puzzles
  npm run test:inspiration
  npm run test:role-models
  ```

---

## 5. Git, build, and push (Web)

- Only `Web/` is a git repo (`testbeeai-ui/TestBee`). The EduBlast root (skills, rules) and `Downloads\files` (ingest scripts) are **not** in git.
- Commit or push only when the user asks. Never force-push, never change git config. Push to the current branch.
- Several agents edit `Web/` at once. Before committing, read `git status`: the working tree usually holds other people's WIP. Code they depend on (e.g. an untracked `lib/` folder imported by a modified file) must go in the same commit. Leave one-off `scripts/_*` probes out and say so.
- `npm run build` in `Web/` before any push. It runs fine while `npm run dev:turbo` is up (Next 16 dev writes `.next/dev`).
- Concurrent edits drop imports. A missing `isPyqSourcedCatalogSlug` import in `app/api/chapter-pyq/questions/route.ts` made every chapter paper show "Questions Coming Soon — … is not defined". A red error string in a UI empty-state is a code bug, not missing data: `git diff HEAD -- <file>` first.

## 6. Coding & Architecture Conventions

- **Tailwind CSS v4**: Both `Web` and `EduDeca` use Tailwind v4 (`@tailwindcss/postcss`).
- **Auth Consistency**: Google OAuth runs through Supabase. In development, always navigate via `http://localhost:3000` or `http://localhost:3001` (avoid `127.0.0.1` to maintain consistent cookie sessions across auth callbacks).
- **Node Engine**: Node.js **>= 22.5.0** is required across the projects.
