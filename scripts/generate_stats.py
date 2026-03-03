#!/usr/bin/env python3
"""Generate GitHub stats SVG cards for the profile README.

Fetches stats from the GitHub API (GraphQL with REST fallback) and produces
two SVG files under assets/:
  - github-stats.svg  (stars, commits, PRs, issues, repos)
  - top-langs.svg     (top languages by code size)
"""

import json
import os
import sys
import urllib.request
import urllib.error

USERNAME = os.environ.get("GITHUB_USERNAME", "ElSakr")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Fallback palette for languages when the API doesn't return a color
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Java": "#b07219",
    "C#": "#178600",
    "C++": "#f34b7d",
    "C": "#555555",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Go": "#00ADD8",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "Dart": "#00B4AB",
    "Objective-C": "#438eff",
    "Scala": "#c22d40",
    "R": "#198CE7",
    "Lua": "#000080",
    "Vue": "#41b883",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "PowerShell": "#012456",
    "Perl": "#0298c3",
    "Haskell": "#5e5086",
    "Jupyter Notebook": "#DA5B0B",
}

DEFAULT_COLOR = "#8b949e"


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def github_rest(url):
    """GET from the GitHub REST API. Returns parsed JSON or None."""
    req = urllib.request.Request(url)
    if TOKEN:
        req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "github-stats-generator")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        print(f"REST error {exc.code}: {url}", file=sys.stderr)
        return None


def github_graphql(query):
    """Execute a GraphQL query. Returns the ``data`` dict or None."""
    req = urllib.request.Request("https://api.github.com/graphql")
    if TOKEN:
        req.add_header("Authorization", f"bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "github-stats-generator")
    body = json.dumps({"query": query}).encode()
    try:
        with urllib.request.urlopen(req, data=body, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if "errors" in result:
                print(f"GraphQL errors: {result['errors']}", file=sys.stderr)
            return result.get("data")
    except urllib.error.HTTPError as exc:
        print(f"GraphQL error {exc.code}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def _aggregate_languages(repos):
    """Aggregate language data from a list of repository nodes."""
    languages = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            color = edge["node"]["color"] or LANG_COLORS.get(name, DEFAULT_COLOR)
            size = edge["size"]
            if name in languages:
                languages[name]["size"] += size
            else:
                languages[name] = {"size": size, "color": color}

    sorted_langs = sorted(languages.items(), key=lambda x: x[1]["size"], reverse=True)[:8]
    total_size = sum(v["size"] for _, v in sorted_langs)
    return [
        {"name": n, "percentage": v["size"] / total_size * 100 if total_size else 0, "color": v["color"]}
        for n, v in sorted_langs
    ]


def fetch_stats_graphql():
    """Primary: fetch stats via the GraphQL API."""
    query = """
    {
      user(login: "%s") {
        name
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
          totalPullRequestContributions
          totalIssueContributions
        }
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
          totalCount
          nodes {
            stargazerCount
            forkCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
        pullRequests(first: 1) { totalCount }
        issues(first: 1) { totalCount }
      }
    }
    """ % USERNAME

    data = github_graphql(query)
    if not data or not data.get("user"):
        return None

    user = data["user"]
    repos = user["repositories"]["nodes"]
    contrib = user["contributionsCollection"]

    return {
        "name": user.get("name") or USERNAME,
        "total_stars": sum(r["stargazerCount"] for r in repos),
        "total_commits": contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"],
        "total_prs": user["pullRequests"]["totalCount"],
        "total_issues": user["issues"]["totalCount"],
        "total_repos": user["repositories"]["totalCount"],
        "languages": _aggregate_languages(repos),
    }


def fetch_stats_rest():
    """Fallback: fetch stats via the REST API."""
    user = github_rest(f"https://api.github.com/users/{USERNAME}")
    if not user:
        print("Failed to fetch user data", file=sys.stderr)
        sys.exit(1)

    # Paginate repos
    repos = []
    page = 1
    while True:
        batch = github_rest(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}"
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    # Language aggregation via REST (approximation by repo size)
    languages = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + repo.get("size", 0)

    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:8]
    total_size = sum(s for _, s in sorted_langs)

    return {
        "name": user.get("name") or USERNAME,
        "total_stars": total_stars,
        "total_commits": 0,
        "total_prs": 0,
        "total_issues": 0,
        "total_repos": user.get("public_repos", 0),
        "languages": [
            {
                "name": n,
                "percentage": s / total_size * 100 if total_size else 0,
                "color": LANG_COLORS.get(n, DEFAULT_COLOR),
            }
            for n, s in sorted_langs
        ],
    }


def fetch_stats():
    """Fetch stats, trying GraphQL first then falling back to REST."""
    stats = fetch_stats_graphql()
    if stats is None:
        print("GraphQL unavailable, falling back to REST API", file=sys.stderr)
        stats = fetch_stats_rest()
    return stats


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

CARD_WIDTH = 420


def _svg_header(height, extra_defs=""):
    return (
        f'<svg width="{CARD_WIDTH}" height="{height}" '
        f'viewBox="0 0 {CARD_WIDTH} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">\n'
        f"  <defs>\n{extra_defs}  </defs>\n"
        f'  <rect class="bg" x="0.5" y="0.5" '
        f'width="{CARD_WIDTH - 1}" height="{height - 1}" rx="6"/>\n'
    )


STATS_STYLE = """\
    <style>
      .bg  { fill: #0d1117; stroke: #30363d; stroke-width: 1; }
      .ttl { font: 600 18px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: #58a6ff; }
      .lbl { font: 400 14px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: #c9d1d9; }
      .val { font: 700 14px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: #f0f6fc; }
    </style>
"""

LANGS_STYLE_TPL = """\
    <style>
      .bg   {{ fill: #0d1117; stroke: #30363d; stroke-width: 1; }}
      .ttl  {{ font: 600 18px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: #58a6ff; }}
      .ln   {{ font: 400 13px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: #c9d1d9; }}
      .lp   {{ font: 400 13px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: #8b949e; }}
    </style>
    <mask id="bm">
      <rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="3" fill="white"/>
    </mask>
"""

# Icon paths (16×16 viewBox, from GitHub's Octicons)
ICON_STAR = "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"
ICON_COMMIT = "M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z"
ICON_PR = "M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"
ICON_ISSUE = "M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z"
ICON_REPO = "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8zm-8 11h8v2h-8a1 1 0 010-2z"


def generate_stats_svg(stats):
    """Produce the GitHub Stats card."""
    pad = 25
    row_h = 30
    items = [
        ("Total Stars",   stats["total_stars"],   "#ffa028", ICON_STAR),
        ("Total Commits", stats["total_commits"],  "#2ea043", ICON_COMMIT),
        ("Total PRs",     stats["total_prs"],      "#58a6ff", ICON_PR),
        ("Total Issues",  stats["total_issues"],   "#db61a2", ICON_ISSUE),
        ("Total Repos",   stats["total_repos"],    "#79c0ff", ICON_REPO),
    ]
    card_h = 65 + len(items) * row_h + 15

    rows = ""
    for i, (label, value, color, icon) in enumerate(items):
        y = 65 + i * row_h
        rows += (
            f'  <g transform="translate({pad}, {y})">\n'
            f'    <svg width="16" height="16" viewBox="0 0 16 16" fill="{color}">'
            f'<path d="{icon}"/></svg>\n'
            f'    <text x="24" y="12.5" class="lbl">{label}:</text>\n'
            f'    <text x="{CARD_WIDTH - pad * 2 - 10}" y="12.5" class="val" text-anchor="end">'
            f'{value:,}</text>\n'
            f"  </g>\n"
        )

    return (
        _svg_header(card_h, STATS_STYLE)
        + f'  <text x="{pad}" y="40" class="ttl">{stats["name"]}\'s GitHub Stats</text>\n'
        + rows
        + "</svg>\n"
    )


def generate_langs_svg(stats):
    """Produce the Top Languages card."""
    langs = stats["languages"]
    if not langs:
        return None

    pad = 25
    bar_h = 8
    bar_y = 55
    bar_w = CARD_WIDTH - pad * 2
    row_h = 32

    # Segmented progress bar
    segments = ""
    x = 0.0
    for lang in langs:
        w = lang["percentage"] / 100 * bar_w
        if w < 0.5:
            continue
        segments += (
            f'  <rect x="{pad + x:.1f}" y="{bar_y}" width="{w:.1f}" '
            f'height="{bar_h}" fill="{lang["color"]}" mask="url(#bm)"/>\n'
        )
        x += w

    # Two-column legend
    col_w = (CARD_WIDTH - pad * 2) // 2
    labels = ""
    for i, lang in enumerate(langs):
        lx = pad + (i % 2) * col_w
        ly = bar_y + bar_h + 24 + (i // 2) * row_h
        labels += (
            f'  <g transform="translate({lx}, {ly})">\n'
            f'    <circle cx="5" cy="5" r="5" fill="{lang["color"]}"/>\n'
            f'    <text x="16" y="9" class="ln">{lang["name"]}</text>\n'
            f'    <text x="{16 + len(lang["name"]) * 7.5 + 8:.0f}" y="9" class="lp">'
            f'{lang["percentage"]:.1f}%</text>\n'
            f"  </g>\n"
        )

    num_rows = (len(langs) + 1) // 2
    card_h = bar_y + bar_h + 24 + num_rows * row_h + 15

    style = LANGS_STYLE_TPL.format(pad=pad, bar_y=bar_y, bar_w=bar_w, bar_h=bar_h)
    return (
        _svg_header(card_h, style)
        + f'  <text x="{pad}" y="38" class="ttl">Most Used Languages</text>\n'
        + segments
        + labels
        + "</svg>\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs("assets", exist_ok=True)

    print(f"Fetching GitHub stats for {USERNAME} ...")
    stats = fetch_stats()

    print("Generating GitHub Stats card ...")
    with open("assets/github-stats.svg", "w") as fh:
        fh.write(generate_stats_svg(stats))
    print("  -> assets/github-stats.svg")

    print("Generating Top Languages card ...")
    langs_svg = generate_langs_svg(stats)
    if langs_svg:
        with open("assets/top-langs.svg", "w") as fh:
            fh.write(langs_svg)
        print("  -> assets/top-langs.svg")
    else:
        print("  (no language data)")

    print("Done!")


if __name__ == "__main__":
    main()
