"""
Generate GitHub stats SVG card for Matrix53's profile README.
Outputs: generated/overview.svg

Features:
- All-time commits (loops year-by-year since account creation)
- Stars from own repos + org repos where viewer is owner/admin
- Beautiful radical-themed card with gradient border & glow
"""

import os
import requests
from pathlib import Path
from datetime import datetime, timezone

TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("USERNAME", "Matrix53")

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"bearer {TOKEN}"}

MARQUEE_DURATION = float(os.environ.get("MARQUEE_DURATION", "18"))
MARQUEE_WIDTH = 220
MARQUEE_HEIGHT = 332
MARQUEE_CHIP_HEIGHT = 20
MARQUEE_ROW_START = 14
MARQUEE_ROW_GAP = 26
MARQUEE_PADDING_X = 8

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

TECH_BADGES = {
    "PyTorch": ("PT", "#EE4C2C", "#FFFFFF"),
    "CUDA": ("CU", "#76B900", "#102111"),
    "Diffusers": ("Df", "#6E7DFF", "#FFFFFF"),
    "Transformers": ("Tr", "#F6D04D", "#231A00"),
    "OpenCV": ("CV", "#4F46E5", "#FFFFFF"),
    "Python": ("Py", "#3776AB", "#FFFFFF"),
    "Rust": ("Rs", "#B7410E", "#FFFFFF"),
    "Go": ("Go", "#00ADD8", "#032531"),
    "Electron": ("El", "#47848F", "#FFFFFF"),
    "Vue 3": ("V3", "#42B883", "#0B1F18"),
    "MPI": ("MP", "#8B5CF6", "#FFFFFF"),
    "OpenMP": ("OM", "#F97316", "#FFFFFF"),
}

PROJECT_EMOJIS = {
    "ELBO-T2IAlign": "🧪",
    "DiffSegmenter": "🧩",
    "PhoeniX": "🛰️",
    "PhoeniX Server": "🗄️",
    "Parallel Programming": "⚙️",
    "Calcium": "🦀",
    "Mario": "🍄",
    "Match Maltese": "🐶",
    "Algo": "📐",
    "Gobang": "⚫",
    "Calendar": "🗓️",
    "Hazelnut React": "🌰",
}


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


def approx_text_width(text: str) -> int:
    return 46 + len(text) * 7


def row_y(row_index: int) -> int:
    return MARQUEE_ROW_START + row_index * MARQUEE_ROW_GAP


def marquee_style(lane: str) -> str:
    badge_style = ""
    text_style = ""
    if lane == "left":
        badge_style = """\
      .lane-chip circle.logo-badge {
        stroke: rgba(255,255,255,0.35);
        stroke-width: 0.8;
      }"""
        text_style = """\
      .lane-chip text.logo-text {
        font: 700 8px 'Segoe UI', Ubuntu, sans-serif;
        dominant-baseline: middle;
        text-anchor: middle;
      }"""
    else:
        badge_style = """\
      .lane-chip circle.emoji-badge {
        fill: #eef4ff;
        stroke: #d8dfef;
        stroke-width: 1;
      }"""
        text_style = """\
      .lane-chip text.emoji {
        font: 13px 'Segoe UI Emoji', 'Apple Color Emoji', sans-serif;
        dominant-baseline: middle;
        text-anchor: middle;
      }"""

    return f"""\
    <style>
      .lane-shell {{ fill: transparent; }}
      .lane-chip rect.chip-bg {{
        fill: #ffffff;
        fill-opacity: 0.92;
        stroke: #d7dbe8;
        stroke-width: 1;
      }}
      .lane-chip text.label {{
        font: 600 11px 'Segoe UI', Ubuntu, sans-serif;
        fill: #1f2937;
        dominant-baseline: middle;
      }}
{text_style}
{badge_style}
      .guide-label {{
        font: 700 9px 'Segoe UI', Ubuntu, sans-serif;
        fill: #8d98ad;
        letter-spacing: 0.08em;
      }}
      .speed-note {{
        font: 600 8px 'Segoe UI', Ubuntu, sans-serif;
        fill: #b0bacb;
      }}
    </style>"""


def tech_chip(x: int, y: int, label: str) -> str:
    badge_text, badge_fill, badge_text_fill = TECH_BADGES[label]
    chip_width = approx_text_width(label) + 24
    return f"""\
    <g transform="translate({x} {y})" class="chip-content">
      <rect class="chip-bg" rx="10" ry="10" width="{chip_width}" height="{MARQUEE_CHIP_HEIGHT}" />
      <circle class="logo-badge" cx="10" cy="10" r="9" fill="{badge_fill}" />
      <text class="logo-text" x="10" y="10.5" fill="{badge_text_fill}">{esc(badge_text)}</text>
      <text class="label" x="24" y="10.5">{esc(label)}</text>
    </g>"""


def project_chip(x: int, y: int, label: str) -> str:
    chip_width = approx_text_width(label) + 28
    emoji = PROJECT_EMOJIS[label]
    return f"""\
    <g transform="translate({x} {y})" class="chip-content">
      <rect class="chip-bg" rx="10" ry="10" width="{chip_width}" height="{MARQUEE_CHIP_HEIGHT}" />
      <circle class="emoji-badge" cx="10" cy="10" r="9" />
      <text class="emoji" x="10" y="10.5">{esc(emoji)}</text>
      <text class="label" x="24" y="10.5">{esc(label)}</text>
    </g>"""


def marquee_item_group(
    *,
    row_index: int,
    item_svg: str,
    chip_width: int,
    animation_class: str,
    start_x: int,
    end_x: int,
) -> str:
    y = row_y(row_index)
    begin = -(row_index * 1.35)
    duration = f"{MARQUEE_DURATION}s"
    return f"""\
  <g class="lane-chip {animation_class}" data-row="{row_index}" opacity="0">
    <animateTransform attributeName="transform"
                      type="translate"
                      values="{start_x} 0; {end_x} 0"
                      dur="{duration}"
                      begin="{begin}s"
                      repeatCount="indefinite" />
    <animate attributeName="opacity"
             values="0;1;1;0.16;0"
             keyTimes="0;0.12;0.74;0.9;1"
             dur="{duration}"
             begin="{begin}s"
             repeatCount="indefinite" />
    {item_svg.format(x=0, y=y, width=chip_width)}
  </g>"""


def marquee_svg(items: list[str], lane: str) -> str:
    if lane not in {"left", "right"}:
        raise ValueError(f"Unsupported lane: {lane}")

    animation_class = (
        "left-to-right-left center-fade-stop"
        if lane == "left"
        else "left-to-right-right outer-fade-stop"
    )
    lane_label = "TECH STACK" if lane == "left" else "PROJECTS"
    fade_marker = "center-fade-stop" if lane == "left" else "outer-fade-stop"
    clip_id = f"lane-clip-{lane}"
    groups = []

    for row_index, label in enumerate(items):
        y = row_y(row_index)
        if lane == "left":
            chip_width = approx_text_width(label) + 24
            item_svg = tech_chip("{x}", y, label)
            start_x = -(chip_width + 20)
            end_x = MARQUEE_WIDTH - chip_width - MARQUEE_PADDING_X
        else:
            chip_width = approx_text_width(label) + 28
            item_svg = project_chip("{x}", y, label)
            start_x = -14
            end_x = MARQUEE_WIDTH - chip_width - MARQUEE_PADDING_X

        groups.append(
            marquee_item_group(
                row_index=row_index,
                item_svg=item_svg,
                chip_width=chip_width,
                animation_class=animation_class,
                start_x=start_x,
                end_x=end_x,
            )
        )

    groups_svg = "\n".join(groups)

    return f"""<svg width="{MARQUEE_WIDTH}" height="{MARQUEE_HEIGHT}"
     viewBox="0 0 {MARQUEE_WIDTH} {MARQUEE_HEIGHT}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="{lane_label.title()} marquee">
  <defs>
{marquee_style(lane)}
    <clipPath id="{clip_id}">
      <rect width="{MARQUEE_WIDTH}" height="{MARQUEE_HEIGHT}" rx="14" ry="14" />
    </clipPath>
  </defs>

  <g class="lane-shell {fade_marker}" data-fade="{fade_marker}" data-duration="{MARQUEE_DURATION}s" clip-path="url(#{clip_id})">
    <text class="guide-label" x="{MARQUEE_PADDING_X}" y="10">{lane_label}</text>
    <text class="speed-note" x="{MARQUEE_PADDING_X}" y="{MARQUEE_HEIGHT - 6}">Shared speed · {MARQUEE_DURATION}s</text>
{groups_svg}
  </g>
</svg>"""


def marquee_left_svg() -> str:
    return marquee_svg(TECH_STACK_ITEMS, lane="left")


def marquee_right_svg() -> str:
    return marquee_svg(PROJECT_ITEMS, lane="right")


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
    (out / "marquee-left.svg").write_text(marquee_left_svg(), encoding="utf-8")
    (out / "marquee-right.svg").write_text(marquee_right_svg(), encoding="utf-8")
    print("Done → generated/overview.svg")
    print("Done → generated/marquee-left.svg")
    print("Done → generated/marquee-right.svg")


if __name__ == "__main__":
    main()
