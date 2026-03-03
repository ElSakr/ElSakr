# CLAUDE.md

## Repository Overview

This is the **GitHub Profile README** repository for [Amr Sakr](https://github.com/ElSakr) (`ElSakr/ElSakr`). It is a special GitHub repository whose `README.md` is displayed on the owner's GitHub profile page.

## Repository Structure

```
.
└── README.md    # GitHub profile page content (HTML + Markdown)
```

This is a minimal, single-file repository. The only meaningful file is `README.md`.

## Tech Stack

- **Markup**: HTML with inline Markdown, centered layout using `align="center"`
- **Dynamic Content**: Third-party badge/stats services embedded as images:
  - [github-readme-stats](https://github.com/anuraghazra/github-readme-stats) — GitHub stats card and top languages
  - [github-readme-streak-stats](https://github.com/DenverCoder1/github-readme-streak-stats) — Contribution streak
  - [gpvc](https://github.com/arturssmirnovs/github-profile-views-counter) — Profile view counter

## Key Conventions

- The README uses raw HTML (`<h1>`, `<p>`, `<div>`) for precise alignment and layout control rather than pure Markdown
- Stats widgets are embedded as Markdown image links (`![alt](url)`) with the `dark` theme
- The `html` language is hidden from stats via the `&hide=html` query parameter

## Git Workflow

- **Default branch**: `master`
- Commits are made directly to `master` — no branching strategy or PR workflow is in use
- Commit messages are short and descriptive (e.g., "Update README.md")

## Development Guidelines

When editing this repository:

1. **Only modify `README.md`** — this is the sole content file
2. **Preserve HTML structure** — the centered layout depends on `<div align="center">` wrappers
3. **Keep the dark theme consistent** — all stats widgets use `&theme=dark`
4. **Test image URLs** — ensure third-party badge URLs are valid before committing, as broken images degrade the profile page
5. **Do not add unnecessary files** — this repository should remain minimal as a profile README

## Build / Test / Lint

There is no build system, test suite, or linter configured. Changes are validated visually on the GitHub profile page after pushing.
