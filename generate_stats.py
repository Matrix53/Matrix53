"""
Generate GitHub stats SVG cards for Matrix53's profile README.
Outputs:
  generated/overview.svg  — overall GitHub statistics
  generated/languages.svg — top programming languages
"""

import os
import requests
from collections import defaultdict
from pathlib import Path

TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("USERNAME", "Matrix53")

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"bearer {TOKEN}"}

STATS_QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
    pullRequests(first: 1) { totalCount }
    openIssues:   issues(states: OPEN)   { totalCount }
    closedIssues: issues(states: CLOSED) { totalCount }
    repositoriesContributedTo(
      first: 1
      includeUserRepositories: false
    ) { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
  }
}
"""


def run_query(query, variables):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    if "errors" in result:
        raise RuntimeError(f"GraphQL errors: {result['errors']}")
    return result["data"]


def fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


# ── SVG helpers ──────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def overview_svg(stars, commits, prs, issues, repos, contributed) -> str:
    W, H = 450, 195
    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
  xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <linearGradient id="border" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#fe428e"/>
      <stop offset="100%" stop-color="#a9fef7"/>
    </linearGradient>
    <style>
      text {{ font-family: 'Segoe UI', Ubuntu, Sans-Serif; fill: #a9fef7; }}
      .title {{ font-size: 14px; font-weight: 700; fill: #fe428e; }}
      .label {{ font-size: 11px; fill: #a9fef7; opacity: .85; }}
      .value {{ font-size: 20px; font-weight: 700; fill: #f8d847; }}
      .small  {{ font-size: 11px; fill: #a9fef7; }}
    </style>
  </defs>

  <!-- border gradient -->
  <rect width="{W}" height="{H}" rx="10" ry="10" fill="url(#border)"/>
  <!-- inner background -->
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="9" ry="9" fill="#141321"/>

  <!-- title -->
  <text x="25" y="35" class="title">{esc(USERNAME)}'s GitHub Stats</text>

  <!-- row 1 -->
  <text x="25"  y="65"  class="label">⭐ Total Stars</text>
  <text x="25"  y="88"  class="value">{esc(fmt(stars))}</text>

  <text x="175" y="65"  class="label">🔀 Total Commits</text>
  <text x="175" y="88"  class="value">{esc(fmt(commits))}</text>

  <text x="320" y="65"  class="label">🔖 Total PRs</text>
  <text x="320" y="88"  class="value">{esc(fmt(prs))}</text>

  <!-- row 2 -->
  <text x="25"  y="120" class="label">🐛 Total Issues</text>
  <text x="25"  y="143" class="value">{esc(fmt(issues))}</text>

  <text x="175" y="120" class="label">📦 Repos</text>
  <text x="175" y="143" class="value">{esc(fmt(repos))}</text>

  <text x="320" y="120" class="label">🤝 Contributed to</text>
  <text x="320" y="143" class="value">{esc(fmt(contributed))}</text>

  <!-- footer line -->
  <line x1="25" y1="162" x2="{W-25}" y2="162" stroke="#fe428e" stroke-opacity=".3" stroke-width="1"/>
  <text x="25" y="178" class="small" opacity=".6">Updated by GitHub Actions</text>
</svg>"""


def languages_svg(top_langs: list[tuple[str, int, str]]) -> str:
    """top_langs: [(name, size, color), ...]"""
    W, H = 300, 30 + 28 * len(top_langs) + 30
    total = sum(s for _, s, _ in top_langs)

    bars = ""
    for i, (name, size, color) in enumerate(top_langs):
        pct = size / total
        y = 60 + i * 28
        bar_w = int(pct * 220)
        bars += f"""
  <text x="25"  y="{y}" class="label">{esc(name)}</text>
  <rect x="25" y="{y+6}" width="220" height="8" rx="4" fill="#2d2b3d"/>
  <rect x="25" y="{y+6}" width="{bar_w}" height="8" rx="4" fill="{esc(color or '#58a6ff')}"/>
  <text x="255" y="{y+13}" class="pct">{pct*100:.1f}%</text>"""

    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
  xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="border" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#fe428e"/>
      <stop offset="100%" stop-color="#a9fef7"/>
    </linearGradient>
    <style>
      text {{ font-family: 'Segoe UI', Ubuntu, Sans-Serif; fill: #a9fef7; }}
      .title {{ font-size: 14px; font-weight: 700; fill: #fe428e; }}
      .label {{ font-size: 12px; fill: #a9fef7; }}
      .pct   {{ font-size: 11px; fill: #f8d847; font-weight: 700; }}
    </style>
  </defs>
  <rect width="{W}" height="{H}" rx="10" ry="10" fill="url(#border)"/>
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="9" ry="9" fill="#141321"/>

  <text x="25" y="35" class="title">Most Used Languages</text>
  {bars}
</svg>"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Fetching stats for {USERNAME}...")
    data = run_query(STATS_QUERY, {"login": USERNAME})["user"]

    stars = sum(r["stargazerCount"] for r in data["repositories"]["nodes"])
    commits = (data["contributionsCollection"]["totalCommitContributions"]
               + data["contributionsCollection"]["restrictedContributionsCount"])
    prs = data["pullRequests"]["totalCount"]
    issues = (data["openIssues"]["totalCount"]
              + data["closedIssues"]["totalCount"])
    repos = data["repositories"]["totalCount"]
    contributed = data["repositoriesContributedTo"]["totalCount"]

    # Aggregate language sizes across all repos
    lang_sizes: dict[str, int] = defaultdict(int)
    lang_colors: dict[str, str] = {}
    for repo in data["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            node = edge["node"]
            lang_sizes[node["name"]] += edge["size"]
            lang_colors[node["name"]] = node["color"] or "#58a6ff"

    top_langs = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:6]
    top_langs_colored = [(name, size, lang_colors[name]) for name, size in top_langs]

    # Write output
    out = Path("generated")
    out.mkdir(exist_ok=True)

    (out / "overview.svg").write_text(
        overview_svg(stars, commits, prs, issues, repos, contributed)
    )
    print(f"  overview.svg: stars={fmt(stars)}, commits={fmt(commits)}, "
          f"prs={fmt(prs)}, issues={fmt(issues)}")

    (out / "languages.svg").write_text(languages_svg(top_langs_colored))
    print(f"  languages.svg: {[n for n,_,_ in top_langs_colored]}")

    print("Done.")


if __name__ == "__main__":
    main()
