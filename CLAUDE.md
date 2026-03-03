# CLAUDE.md

## Repository Overview

This is the **GitHub Profile README** repository for [Amr Sakr](https://github.com/ElSakr) (`ElSakr/ElSakr`). It is a special GitHub repository whose `README.md` is displayed on the owner's GitHub profile page.

The repo includes a self-hosted stats generation system that replaces third-party services with a GitHub Actions workflow and a Python script.

## Repository Structure

```
.
├── .github/
│   └── workflows/
│       └── update-stats.yml   # Scheduled workflow to regenerate SVG stats
├── assets/
│   ├── github-stats.svg       # Generated — GitHub stats card
│   └── top-langs.svg          # Generated — top languages card
├── scripts/
│   └── generate_stats.py      # Fetches GitHub API data and produces SVGs
├── CLAUDE.md
└── README.md                  # Profile page (references local SVGs)
```

## Tech Stack

- **Profile page**: HTML + Markdown in `README.md`, centered layout using `align="center"`
- **Stats generation**: Python 3 script (`scripts/generate_stats.py`) using only the standard library (`urllib`, `json`)
- **CI/CD**: GitHub Actions workflow (`.github/workflows/update-stats.yml`)
- **Data source**: GitHub GraphQL API (primary) with REST API fallback
- **Output**: Static SVG files committed to `assets/` — no external service dependencies

## How Stats Generation Works

1. The GitHub Actions workflow runs **daily at midnight UTC**, on **manual dispatch**, or when `scripts/generate_stats.py` is modified on `main`.
2. The Python script authenticates with `GITHUB_TOKEN` and queries the GitHub GraphQL API for:
   - Stars, commits, PRs, issues, and repo count (stats card)
   - Language breakdown by code size across all owned repos (languages card)
3. If GraphQL fails, it falls back to the REST API (with reduced data — no commit/PR/issue counts).
4. Two SVG files are generated with a dark theme (#0d1117 background) and committed to `assets/`.
5. `README.md` references these local SVG files — no external image URLs.

### Environment Variables

| Variable           | Source                          | Purpose                       |
| ------------------ | ------------------------------- | ----------------------------- |
| `GITHUB_TOKEN`     | Provided by Actions             | API authentication            |
| `GITHUB_USERNAME`  | Set in workflow (default: ElSakr) | Target GitHub user to query |

## Key Conventions

- The README uses raw HTML (`<h1>`, `<p>`, `<div>`) for layout control
- Stats cards use the GitHub dark theme palette (`#0d1117` bg, `#58a6ff` titles, `#c9d1d9` text)
- SVG icons are from GitHub's Octicons set (16x16 viewBox)
- The script uses only Python standard library — no pip dependencies

## Git Workflow

- **Default branch**: `main`
- Commits are made directly to `main`
- The Actions bot auto-commits updated SVGs with message `chore: update GitHub stats`
- Human commit messages are short and descriptive (e.g., "Update README.md")

## Development Guidelines

1. **`README.md`** — Preserve the `<div align="center">` structure. SVG references use relative paths (`./assets/*.svg`)
2. **`scripts/generate_stats.py`** — Keep stdlib-only (no pip install step in the workflow). Dark theme colors are defined as constants at the top of the file
3. **`assets/`** — Do not manually edit SVGs here; they are overwritten by the workflow. Edit the generation script instead
4. **SVG design** — Card width is fixed at 420px. Styles use the `.bg`, `.ttl`, `.lbl`, `.val` CSS classes

## Running Locally

```bash
export GITHUB_TOKEN="ghp_..."       # A PAT with public_repo scope
export GITHUB_USERNAME="ElSakr"
python3 scripts/generate_stats.py   # Writes to assets/
```

## Build / Test / Lint

No test suite or linter is configured. To validate changes:

- **Script**: Run locally and inspect the generated SVGs in a browser
- **README**: Push to a branch and preview on GitHub
- **Workflow**: Trigger manually via Actions tab → "Run workflow"
