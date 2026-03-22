"""
Generate GitHub stats SVG card and README marquee assets for Matrix53's profile.
Outputs: generated/overview.svg and generated/marquee-*.svg
"""

import base64
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import requests

TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("USERNAME", "Matrix53")

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"bearer {TOKEN}"}

MARQUEE_DURATION = float(os.environ.get("MARQUEE_DURATION", "18"))
MARQUEE_WIDTH = 132
MARQUEE_TOP_HEIGHT = 54
MARQUEE_BOTTOM_HEIGHT = 200
MARQUEE_CHIP_WIDTH = 120
MARQUEE_CHIP_HEIGHT = 22
MARQUEE_ICON_SIZE = 14
MARQUEE_PADDING_X = 6
MARQUEE_LABEL_WIDTH = 84

TECH_STACK_ITEMS = [
    "PyTorch",
    "CUDA",
    "Diffusers",
    "Transformers",
    "OpenCV",
    "Python",
    "Rust",
    "Go",
    "Electron",
    "Vue 3",
    "MPI",
    "OpenMP",
]

PROJECT_ITEMS = [
    "ELBO-T2IAlign",
    "DiffSegmenter",
    "PhoeniX",
    "PhoeniX Server",
    "Parallel Programming",
    "Calcium",
    "Mario",
    "Match Maltese",
    "Algo",
    "Gobang",
    "Calendar",
    "Hazelnut React",
]

TECH_ICON_FILES = {
    "PyTorch": "assets/readme/tech/pytorch.svg",
    "CUDA": "assets/readme/tech/cuda.svg",
    "Diffusers": "assets/readme/tech/diffusers.svg",
    "Transformers": "assets/readme/tech/transformers.svg",
    "OpenCV": "assets/readme/tech/opencv.svg",
    "Python": "assets/readme/tech/python.svg",
    "Rust": "assets/readme/tech/rust.svg",
    "Go": "assets/readme/tech/go.svg",
    "Electron": "assets/readme/tech/electron.svg",
    "Vue 3": "assets/readme/tech/vue3.svg",
    "MPI": "assets/readme/tech/mpi.png",
    "OpenMP": "assets/readme/tech/openmp.svg",
}

TECH_ICON_TINTS = {
    "PyTorch": "#EE4C2C",
    "CUDA": "#76B900",
    "Diffusers": "#FFD21E",
    "Transformers": "#FFD21E",
    "OpenCV": "#5C3EE8",
    "Python": "#3776AB",
    "Rust": "#000000",
    "Go": "#00ADD8",
    "Electron": "#47848F",
    "Vue 3": "#4FC08D",
}

PROJECT_EMOJI_FILES = {
    "ELBO-T2IAlign": "assets/readme/emoji/elbo.svg",
    "DiffSegmenter": "assets/readme/emoji/diffsegmenter.svg",
    "PhoeniX": "assets/readme/emoji/phoenix.svg",
    "PhoeniX Server": "assets/readme/emoji/phoenix-server.svg",
    "Parallel Programming": "assets/readme/emoji/parallel.svg",
    "Calcium": "assets/readme/emoji/calcium.svg",
    "Mario": "assets/readme/emoji/mario.svg",
    "Match Maltese": "assets/readme/emoji/match-maltese.svg",
    "Algo": "assets/readme/emoji/algo.svg",
    "Gobang": "assets/readme/emoji/gobang.svg",
    "Calendar": "assets/readme/emoji/calendar.svg",
    "Hazelnut React": "assets/readme/emoji/hazelnut-react.svg",
}

TECH_TOP_ITEMS = TECH_STACK_ITEMS[:6]
TECH_BOTTOM_ITEMS = TECH_STACK_ITEMS[6:]
PROJECT_TOP_ITEMS = PROJECT_ITEMS[:6]
PROJECT_BOTTOM_ITEMS = PROJECT_ITEMS[6:]


class InsufficientScopesError(RuntimeError):
    pass


def run_query(query, variables=None):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    if "errors" in result:
        if any(e.get("type") == "INSUFFICIENT_SCOPES" for e in result["errors"]):
            scopes_needed = set()
            for e in result["errors"]:
                msg = e.get("message", "")
                if "read:org" in msg:
                    scopes_needed.add("read:org")
            raise InsufficientScopesError(
                f"Token missing scopes: {scopes_needed}. "
                "Add them at https://github.com/settings/tokens"
            )
        raise RuntimeError(f"GraphQL errors: {result['errors']}")
    return result["data"]


# ── Queries ───────────────────────────────────────────────────────────────────

USER_BASE_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    pullRequests(first: 1) { totalCount }
    openIssues:   issues(states: OPEN)   { totalCount }
    closedIssues: issues(states: CLOSED) { totalCount }
    repositories(ownerAffiliations: [OWNER], isFork: false, first: 1) {
      totalCount
    }
  }
}
"""

COMMITS_YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
"""

OWN_REPOS_STARS_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(ownerAffiliations: [OWNER], first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount }
    }
  }
}
"""

ORGS_QUERY = """
{
  viewer {
    organizations(first: 20) {
      nodes {
        login
        viewerCanAdminister
      }
    }
  }
}
"""

ORG_REPOS_QUERY = """
query($org: String!, $after: String) {
  organization(login: $org) {
    repositories(first: 100, after: $after, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount }
    }
  }
}
"""

CONTRIB_REPOS_YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      commitContributionsByRepository(maxRepositories: 100) {
        repository { nameWithOwner }
      }
      pullRequestContributionsByRepository(maxRepositories: 100) {
        repository { nameWithOwner }
      }
      issueContributionsByRepository(maxRepositories: 100) {
        repository { nameWithOwner }
      }
    }
  }
}
"""


# ── Data fetching ─────────────────────────────────────────────────────────────

def get_all_time_commits(created_at: str) -> int:
    """Sum commits year-by-year from account creation to today."""
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    total = 0
    year = created.year
    while year <= now.year:
        from_dt = f"{year}-01-01T00:00:00Z"
        to_dt = (
            now.strftime("%Y-%m-%dT%H:%M:%SZ")
            if year == now.year
            else f"{year}-12-31T23:59:59Z"
        )
        data = run_query(COMMITS_YEAR_QUERY, {
            "login": USERNAME, "from": from_dt, "to": to_dt
        })
        cc = data["user"]["contributionsCollection"]
        year_total = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
        print(f"    {year}: {year_total} commits")
        total += year_total
        year += 1
    return total


def get_admin_orgs() -> list[str]:
    """Return org logins where viewer can administer. Requires read:org scope."""
    try:
        orgs_data = run_query(ORGS_QUERY)
        orgs = [
            org["login"]
            for org in orgs_data["viewer"]["organizations"]["nodes"]
            if org["viewerCanAdminister"]
        ]
        print(f"  Admin orgs: {orgs or 'none'}")
        return orgs
    except InsufficientScopesError as e:
        print(f"  WARNING: Cannot fetch orgs — {e}")
        print("  To include org data, add 'read:org' scope to your PAT.")
        return []


def get_org_stats(admin_orgs: list[str]) -> tuple[int, int]:
    """Paginate non-fork repos in admin orgs. Returns (total_stars, repo_count)."""
    stars, repo_count = 0, 0
    for org_login in admin_orgs:
        after = None
        while True:
            data = run_query(ORG_REPOS_QUERY, {"org": org_login, "after": after})
            repos = data["organization"]["repositories"]
            for r in repos["nodes"]:
                stars += r["stargazerCount"]
                repo_count += 1
            if not repos["pageInfo"]["hasNextPage"]:
                break
            after = repos["pageInfo"]["endCursor"]
    return stars, repo_count


def get_personal_stars() -> int:
    """Stars from personal repos (paginated)."""
    stars, after = 0, None
    while True:
        data = run_query(OWN_REPOS_STARS_QUERY, {"login": USERNAME, "after": after})
        repos = data["user"]["repositories"]
        for r in repos["nodes"]:
            stars += r["stargazerCount"]
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    return stars


def get_all_time_contributed_repos(created_at: str) -> int:
    """Count unique repos (not owned by user) contributed to across all years."""
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    all_repos: set[str] = set()
    year = created.year
    while year <= now.year:
        from_dt = f"{year}-01-01T00:00:00Z"
        to_dt = (
            now.strftime("%Y-%m-%dT%H:%M:%SZ")
            if year == now.year
            else f"{year}-12-31T23:59:59Z"
        )
        data = run_query(CONTRIB_REPOS_YEAR_QUERY, {
            "login": USERNAME, "from": from_dt, "to": to_dt,
        })
        cc = data["user"]["contributionsCollection"]
        for category in (
            "commitContributionsByRepository",
            "pullRequestContributionsByRepository",
            "issueContributionsByRepository",
        ):
            for item in cc[category]:
                name = item["repository"]["nameWithOwner"]
                # Exclude user's own personal repos (they're counted in "Total Repos")
                if not name.lower().startswith(f"{USERNAME.lower()}/"):
                    all_repos.add(name)
        year += 1
    print(f"  All-time contributed repos: {len(all_repos)}")
    return len(all_repos)


# ── SVG ───────────────────────────────────────────────────────────────────────

def fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def esc(s) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


@lru_cache(maxsize=None)
def asset_data_uri(asset_path: str, tint: str = "") -> str:
    path = Path(asset_path)
    mime_type = "image/png" if path.suffix.lower() == ".png" else "image/svg+xml"
    data = path.read_bytes()
    if tint and path.suffix.lower() == ".svg":
        svg_text = data.decode("utf-8")
        if ' fill="' not in svg_text:
            svg_text = svg_text.replace("<svg ", f'<svg fill="{tint}" ', 1)
        data = svg_text.encode("utf-8")
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def marquee_track_y(height: int) -> int:
    return (height - MARQUEE_CHIP_HEIGHT) // 2


def marquee_style() -> str:
    return """\
    <style>
      .lane-shell { fill: transparent; }
      .lane-chip rect.chip-bg {
        fill: #ffffff;
        fill-opacity: 0.94;
        stroke: #d7dbe8;
        stroke-width: 1;
      }
      .lane-chip circle.icon-ring {
        fill: #f5f7fd;
        stroke: #dbe3f1;
        stroke-width: 0.9;
      }
      .lane-chip image.logo-icon,
      .lane-chip image.emoji-icon {
        overflow: visible;
      }
      .lane-chip text.label {
        font: 600 8.6px 'Segoe UI', Ubuntu, sans-serif;
        fill: #1f2937;
        dominant-baseline: middle;
      }
    </style>"""


def tech_chip(y: int, label: str) -> str:
    icon_href = asset_data_uri(TECH_ICON_FILES[label], TECH_ICON_TINTS.get(label, ""))
    return f"""\
    <g transform="translate(0 {y})" class="chip-content">
      <rect class="chip-bg" rx="11" ry="11" width="{MARQUEE_CHIP_WIDTH}" height="{MARQUEE_CHIP_HEIGHT}" />
      <circle class="icon-ring" cx="14" cy="11" r="8" />
      <image class="logo-icon" href="{icon_href}" x="7" y="4" width="{MARQUEE_ICON_SIZE}" height="{MARQUEE_ICON_SIZE}" preserveAspectRatio="xMidYMid meet" />
      <text class="label" x="28" y="11.2" textLength="{MARQUEE_LABEL_WIDTH}" lengthAdjust="spacingAndGlyphs">{esc(label)}</text>
    </g>"""


def project_chip(y: int, label: str) -> str:
    emoji_href = asset_data_uri(PROJECT_EMOJI_FILES[label])
    return f"""\
    <g transform="translate(0 {y})" class="chip-content">
      <rect class="chip-bg" rx="11" ry="11" width="{MARQUEE_CHIP_WIDTH}" height="{MARQUEE_CHIP_HEIGHT}" />
      <circle class="icon-ring" cx="14" cy="11" r="8" />
      <image class="emoji-icon" href="{emoji_href}" x="7" y="4" width="{MARQUEE_ICON_SIZE}" height="{MARQUEE_ICON_SIZE}" preserveAspectRatio="xMidYMid meet" />
      <text class="label" x="28" y="11.2" textLength="{MARQUEE_LABEL_WIDTH}" lengthAdjust="spacingAndGlyphs">{esc(label)}</text>
    </g>"""


def marquee_item_group(
    *,
    index: int,
    item_count: int,
    item_svg: str,
) -> str:
    start_x = -(MARQUEE_CHIP_WIDTH + 12)
    end_x = MARQUEE_WIDTH - MARQUEE_CHIP_WIDTH - MARQUEE_PADDING_X
    begin = -(index * (MARQUEE_DURATION / item_count))
    duration = f"{MARQUEE_DURATION}s"
    return f"""\
  <g class="lane-chip" data-index="{index}" opacity="0">
    <animateTransform attributeName="transform"
                      type="translate"
                      values="{start_x} 0; {end_x} 0"
                      dur="{duration}"
                      begin="{begin}s"
                      repeatCount="indefinite" />
    <animate attributeName="opacity"
             values="0;1;1;0.18;0"
             keyTimes="0;0.16;0.72;0.88;1"
             dur="{duration}"
             begin="{begin}s"
             repeatCount="indefinite" />
    {item_svg}
  </g>"""


def marquee_svg(items: list[str], *, kind: str, height: int, label: str) -> str:
    if kind not in {"tech", "project"}:
        raise ValueError(f"Unsupported marquee kind: {kind}")

    track_y = marquee_track_y(height)
    item_builder = tech_chip if kind == "tech" else project_chip
    groups = [
        marquee_item_group(
            index=index,
            item_count=len(items),
            item_svg=item_builder(track_y, item),
        )
        for index, item in enumerate(items)
    ]
    groups_svg = "\n".join(groups)
    clip_id = label.lower().replace(" ", "-")

    return f"""<svg width="{MARQUEE_WIDTH}" height="{height}"
     viewBox="0 0 {MARQUEE_WIDTH} {height}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="{label}">
  <defs>
{marquee_style()}
    <clipPath id="lane-clip-{clip_id}">
      <rect width="{MARQUEE_WIDTH}" height="{height}" rx="12" ry="12" />
    </clipPath>
  </defs>

  <g class="lane-shell" data-slot="0" clip-path="url(#lane-clip-{clip_id})">
{groups_svg}
  </g>
</svg>"""


def marquee_left_top_svg() -> str:
    return marquee_svg(TECH_TOP_ITEMS, kind="tech", height=MARQUEE_TOP_HEIGHT, label="Tech stack marquee top")


def marquee_left_bottom_svg() -> str:
    return marquee_svg(TECH_BOTTOM_ITEMS, kind="tech", height=MARQUEE_BOTTOM_HEIGHT, label="Tech stack marquee bottom")


def marquee_right_top_svg() -> str:
    return marquee_svg(PROJECT_TOP_ITEMS, kind="project", height=MARQUEE_TOP_HEIGHT, label="Project marquee top")


def marquee_right_bottom_svg() -> str:
    return marquee_svg(PROJECT_BOTTOM_ITEMS, kind="project", height=MARQUEE_BOTTOM_HEIGHT, label="Project marquee bottom")


def stat_block(x, y, icon, label, value):
    """Render one stat: icon circle + label + big value."""
    return f"""\
  <g transform="translate({x},{y})">
    <circle cx="14" cy="14" r="14" fill="#fe428e" fill-opacity="0.12"/>
    <text x="14" y="19" text-anchor="middle" font-size="15" font-family="'Segoe UI Emoji',sans-serif">{icon}</text>
    <text x="36" y="11" class="lbl">{esc(label)}</text>
    <text x="36" y="29" class="val">{esc(value)}</text>
  </g>"""


def overview_svg(stars, commits, prs, issues, repos, contributed) -> str:
    W, H = 495, 200

    blocks = [
        (22,  60, "⭐", "Total Stars",     fmt(stars)),
        (187, 60, "🔀", "Total Commits",   fmt(commits)),
        (352, 60, "🔖", "Total PRs",       fmt(prs)),
        (22, 130, "🐛", "Total Issues",    fmt(issues)),
        (187,130, "📦", "Total Repos",     fmt(repos)),
        (352,130, "🤝", "Contributed to",  fmt(contributed)),
    ]

    blocks_svg = "\n".join(stat_block(*b) for b in blocks)

    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- card border gradient -->
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#fe428e"/>
      <stop offset="50%"  stop-color="#a9fef7"/>
      <stop offset="100%" stop-color="#f8d847"/>
    </linearGradient>
    <!-- title text gradient -->
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#fe428e"/>
      <stop offset="100%" stop-color="#a9fef7"/>
    </linearGradient>
    <!-- soft glow filter -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <style>
      .lbl {{ font: 11px 'Segoe UI',Ubuntu,sans-serif; fill:#a9fef7; opacity:.8; }}
      .val {{ font: bold 20px 'Segoe UI',Ubuntu,sans-serif; fill:#f8d847; }}
    </style>
  </defs>

  <!-- gradient border -->
  <rect width="{W}" height="{H}" rx="13" ry="13" fill="url(#grad)"/>
  <!-- dark card body -->
  <rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="12" ry="12" fill="#141321"/>
  <!-- subtle top highlight -->
  <rect x="1.5" y="1.5" width="{W-3}" height="40" rx="12" ry="12" fill="#ffffff" fill-opacity="0.03"/>

  <!-- title with glow -->
  <text x="{W//2}" y="36"
        text-anchor="middle"
        font="bold 15px 'Segoe UI',Ubuntu,sans-serif"
        fill="url(#titleGrad)"
        filter="url(#glow)">{esc(USERNAME)}'s GitHub Stats</text>

  <!-- title underline -->
  <line x1="22" y1="46" x2="{W-22}" y2="46"
        stroke="url(#grad)" stroke-opacity="0.25" stroke-width="1"/>

  <!-- stat blocks -->
{blocks_svg}

  <!-- footer -->
  <line x1="22" y1="{H-22}" x2="{W-22}" y2="{H-22}"
        stroke="#a9fef7" stroke-opacity="0.1" stroke-width="1"/>
  <text x="{W//2}" y="{H-8}"
        text-anchor="middle"
        font="10px 'Segoe UI',Ubuntu,sans-serif"
        fill="#a9fef7" opacity="0.35">All-time stats · Updated by GitHub Actions</text>
</svg>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Fetching stats for {USERNAME}...")

    base = run_query(USER_BASE_QUERY, {"login": USERNAME})["user"]
    created_at = base["createdAt"]
    prs = base["pullRequests"]["totalCount"]
    issues = base["openIssues"]["totalCount"] + base["closedIssues"]["totalCount"]
    personal_repos = base["repositories"]["totalCount"]

    print(f"  Account created: {created_at}")

    # Org stats (stars + repo count) — requires read:org scope
    print("  Fetching org admin repos...")
    admin_orgs = get_admin_orgs()
    org_stars, org_repos = get_org_stats(admin_orgs)

    print("  Counting personal stars...")
    personal_stars = get_personal_stars()

    stars = personal_stars + org_stars
    repos = personal_repos + org_repos

    print("  Counting all-time commits...")
    commits = get_all_time_commits(created_at)

    print("  Counting all-time contributed repos...")
    contributed = get_all_time_contributed_repos(created_at)

    print(f"  stars={fmt(stars)}, commits={fmt(commits)}, prs={fmt(prs)}, "
          f"issues={fmt(issues)}, repos={repos}, contributed={contributed}")

    out = Path("generated")
    out.mkdir(exist_ok=True)
    (out / "overview.svg").write_text(
        overview_svg(stars, commits, prs, issues, repos, contributed),
        encoding="utf-8",
    )
    (out / "marquee-left-top.svg").write_text(
        marquee_left_top_svg(),
        encoding="utf-8",
    )
    (out / "marquee-left-bottom.svg").write_text(
        marquee_left_bottom_svg(),
        encoding="utf-8",
    )
    (out / "marquee-right-top.svg").write_text(
        marquee_right_top_svg(),
        encoding="utf-8",
    )
    (out / "marquee-right-bottom.svg").write_text(
        marquee_right_bottom_svg(),
        encoding="utf-8",
    )
    print("Done → generated/overview.svg")
    print("Done → generated/marquee-left-top.svg")
    print("Done → generated/marquee-left-bottom.svg")
    print("Done → generated/marquee-right-top.svg")
    print("Done → generated/marquee-right-bottom.svg")


if __name__ == "__main__":
    main()
