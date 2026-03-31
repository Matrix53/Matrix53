"""
Generate GitHub stats SVG card and README marquee assets for Matrix53's profile.
Outputs: generated/overview.svg and generated/marquee-*.gif
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import requests
from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFont, ImageOps

TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("USERNAME", "Matrix53")

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"bearer {TOKEN}"}

MARQUEE_DURATION = float(os.environ.get("MARQUEE_DURATION", "18"))
MARQUEE_RENDER_SCALE = 2
MARQUEE_DISPLAY_WIDTH = 148
MARQUEE_DISPLAY_HEIGHT = 276
MARQUEE_GIF_WIDTH = MARQUEE_DISPLAY_WIDTH * MARQUEE_RENDER_SCALE
MARQUEE_GIF_HEIGHT = MARQUEE_DISPLAY_HEIGHT * MARQUEE_RENDER_SCALE
MARQUEE_FRAME_COUNT = 144
MARQUEE_FRAME_MS = int(MARQUEE_DURATION * 1000 / MARQUEE_FRAME_COUNT)
MARQUEE_MAX_ACTIVE = 2
MARQUEE_CHIP_WIDTH = 132 * MARQUEE_RENDER_SCALE
MARQUEE_CHIP_HEIGHT = 24 * MARQUEE_RENDER_SCALE
MARQUEE_ICON_BOX_WIDTH = 22 * MARQUEE_RENDER_SCALE
MARQUEE_ICON_BOX_HEIGHT = 16 * MARQUEE_RENDER_SCALE
MARQUEE_PADDING_X = 6
MARQUEE_LABEL_WIDTH = 104 * MARQUEE_RENDER_SCALE
MARQUEE_START_X = -52 * MARQUEE_RENDER_SCALE
MARQUEE_END_X = 66 * MARQUEE_RENDER_SCALE
MARQUEE_VISIBLE_FRAMES = 24
MARQUEE_FADE_IN_FRAMES = 5
MARQUEE_FADE_OUT_FRAMES = 0
MARQUEE_ENTRY_FADE_WIDTH = 18 * MARQUEE_RENDER_SCALE
MARQUEE_EXIT_FADE_WIDTH = 72 * MARQUEE_RENDER_SCALE
MARQUEE_EXIT_ALPHA_START_X = 24 * MARQUEE_RENDER_SCALE
MARQUEE_TEXT_COLOR = "#1f2937"
MARQUEE_STROKE_COLOR = "#d7dbe8"
MARQUEE_RING_FILL = "#f5f7fd"
MARQUEE_RING_STROKE = "#dbe3f1"
MARQUEE_PLACEHOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" viewBox="0 0 0 0"></svg>
"""

README_TYPING_SVG_WIDTH = 435
README_OVERVIEW_SVG_WIDTH = 495
README_CENTER_STACK_WIDTH = max(README_TYPING_SVG_WIDTH, README_OVERVIEW_SVG_WIDTH)
README_REQUIRED_MAIN_WIDTH = README_CENTER_STACK_WIDTH + (2 * MARQUEE_DISPLAY_WIDTH)

GITHUB_LARGE_BREAKPOINT = 1012
GITHUB_XLARGE_BREAKPOINT = 1280
GITHUB_LARGE_CONTENT_PADDING = 16
GITHUB_XLARGE_CONTENT_PADDING = 24
GITHUB_PROFILE_LAYOUT_GUTTER = 24
GITHUB_PROFILE_LARGE_NARROWEST_SIDEBAR = 256
GITHUB_PROFILE_XLARGE_WIDEST_SIDEBAR = 336
GITHUB_PROFILE_LARGE_MAIN_WIDTH_MAX = (
    GITHUB_LARGE_BREAKPOINT
    - (2 * GITHUB_LARGE_CONTENT_PADDING)
    - GITHUB_PROFILE_LARGE_NARROWEST_SIDEBAR
    - GITHUB_PROFILE_LAYOUT_GUTTER
)
GITHUB_PROFILE_XLARGE_MAIN_WIDTH_MIN = (
    GITHUB_XLARGE_BREAKPOINT
    - (2 * GITHUB_XLARGE_CONTENT_PADDING)
    - GITHUB_PROFILE_XLARGE_WIDEST_SIDEBAR
    - GITHUB_PROFILE_LAYOUT_GUTTER
)
# GitHub's large desktop layout tops out at 700px for the README main column,
# which cannot fit 148 + 495 + 148 = 791px of marquee + center content.
# The first GitHub breakpoint that always leaves enough room is xlarge:
# 1280 - 48 - 336 - 24 = 872px.
README_MARQUEE_MIN_WIDTH = GITHUB_XLARGE_BREAKPOINT

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

MARQUEE_INTERVAL_FRAMES = MARQUEE_FRAME_COUNT // len(TECH_STACK_ITEMS)

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

TECH_ICON_RASTER_FILES = {
    "PyTorch": "assets/readme/tech-png/pytorch.png",
    "CUDA": "assets/readme/tech-png/cuda.png",
    "Diffusers": "assets/readme/tech-png/diffusers.png",
    "Transformers": "assets/readme/tech-png/transformers.png",
    "OpenCV": "assets/readme/tech-png/opencv.png",
    "Python": "assets/readme/tech-png/python.png",
    "Rust": "assets/readme/tech-png/rust.png",
    "Go": "assets/readme/tech-png/go.png",
    "Electron": "assets/readme/tech-png/electron.png",
    "Vue 3": "assets/readme/tech-png/vue3.png",
    "MPI": "assets/readme/tech-png/mpi.png",
    "OpenMP": "assets/readme/tech-png/openmp.png",
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
PROJECT_EMOJI_RASTER_FILES = {
    "ELBO-T2IAlign": "assets/readme/emoji-png/elbo.png",
    "DiffSegmenter": "assets/readme/emoji-png/diffsegmenter.png",
    "PhoeniX": "assets/readme/emoji-png/phoenix.png",
    "PhoeniX Server": "assets/readme/emoji-png/phoenix-server.png",
    "Parallel Programming": "assets/readme/emoji-png/parallel.png",
    "Calcium": "assets/readme/emoji-png/calcium.png",
    "Mario": "assets/readme/emoji-png/mario.png",
    "Match Maltese": "assets/readme/emoji-png/match-maltese.png",
    "Algo": "assets/readme/emoji-png/algo.png",
    "Gobang": "assets/readme/emoji-png/gobang.png",
    "Calendar": "assets/readme/emoji-png/calendar.png",
    "Hazelnut React": "assets/readme/emoji-png/hazelnut-react.png",
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


FONT_REGULAR_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "Arial.ttf",
    "Helvetica.ttc",
    "DejaVuSans.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "Arial Bold.ttf",
    "Helvetica Bold.ttf",
    "DejaVuSans-Bold.ttf",
]

LEFT_START_YS = [18, 174, 44, 202, 78, 146, 26, 188, 96, 226, 60, 126]
LEFT_END_YS = [40, 140, 16, 214, 104, 118, 54, 160, 72, 238, 30, 100]
RIGHT_START_YS = [32, 190, 62, 218, 86, 150, 20, 176, 110, 234, 48, 132]
RIGHT_END_YS = [14, 162, 92, 194, 58, 124, 44, 210, 82, 246, 26, 108]


@dataclass(frozen=True)
class MarqueeMotion:
    label: str
    asset_path: str
    start_frame: int
    start_y: int
    end_y: int
    tint: Optional[str] = None


def lane_items(lane: str) -> list[str]:
    if lane == "left":
        return TECH_STACK_ITEMS
    if lane == "right":
        return PROJECT_ITEMS
    raise ValueError(f"Unsupported lane: {lane}")


def fallback_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


@lru_cache(maxsize=None)
def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_REGULAR_CANDIDATES
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return fallback_font(size)


@lru_cache(maxsize=None)
def load_icon_image(path: str, box_width: int, box_height: int, tint: str = "") -> Image.Image:
    icon = Image.open(path).convert("RGBA")
    alpha = icon.getchannel("A")

    # qlmanage-generated PNGs can be fully opaque with a white background.
    # Derive a mask from luminance in that case so tinting does not turn the
    # whole thumbnail into a colored square.
    if alpha.getextrema() == (255, 255):
        grayscale = ImageOps.grayscale(icon.convert("RGB"))
        alpha = ImageOps.invert(grayscale).point(
            lambda value: 0 if value < 12 else min(255, int(value * 1.7))
        )

    if tint:
        colored = Image.new("RGBA", icon.size, ImageColor.getrgb(tint) + (255,))
        colored.putalpha(alpha)
        icon = colored
    else:
        icon.putalpha(alpha)

    scale = min(box_width / icon.width, box_height / icon.height)
    target_width = max(1, int(round(icon.width * scale)))
    target_height = max(1, int(round(icon.height * scale)))
    resized = icon.resize((target_width, target_height), Image.LANCZOS)
    canvas = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    canvas.alpha_composite(
        resized,
        ((box_width - target_width) // 2, (box_height - target_height) // 2),
    )
    return canvas


@lru_cache(maxsize=None)
def build_lane_edge_mask() -> Image.Image:
    mask = Image.new("L", (MARQUEE_GIF_WIDTH, MARQUEE_GIF_HEIGHT), 255)
    pixels = mask.load()
    for x in range(MARQUEE_GIF_WIDTH):
        alpha = 255
        if x < MARQUEE_ENTRY_FADE_WIDTH:
            progress = x / max(1, MARQUEE_ENTRY_FADE_WIDTH)
            alpha = int(255 * ease_in_out(progress))
        elif x > MARQUEE_GIF_WIDTH - MARQUEE_EXIT_FADE_WIDTH:
            progress = (MARQUEE_GIF_WIDTH - x) / max(1, MARQUEE_EXIT_FADE_WIDTH)
            alpha = int(255 * ease_in_out(max(0.0, progress)))
        for y in range(MARQUEE_GIF_HEIGHT):
            pixels[x, y] = alpha
    return mask


def fit_label_font(text: str) -> ImageFont.ImageFont:
    for size in (20, 18, 16, 14):
        font = load_font(size, bold=True)
        if font.getbbox(text)[2] <= MARQUEE_LABEL_WIDTH:
            return font
    return load_font(14, bold=True)


@lru_cache(maxsize=None)
def build_chip_image(lane: str, label: str) -> Image.Image:
    chip = Image.new("RGBA", (MARQUEE_CHIP_WIDTH, MARQUEE_CHIP_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(chip)
    draw.rounded_rectangle(
        (0, 0, MARQUEE_CHIP_WIDTH - 1, MARQUEE_CHIP_HEIGHT - 1),
        radius=MARQUEE_CHIP_HEIGHT // 2,
        fill=(255, 255, 255, 240),
        outline=ImageColor.getrgb(MARQUEE_STROKE_COLOR),
        width=2,
    )
    icon_box_x = 10 * MARQUEE_RENDER_SCALE
    icon_box_y = 4 * MARQUEE_RENDER_SCALE
    draw.rounded_rectangle(
        (
            icon_box_x,
            icon_box_y,
            icon_box_x + MARQUEE_ICON_BOX_WIDTH,
            icon_box_y + MARQUEE_ICON_BOX_HEIGHT,
        ),
        radius=MARQUEE_ICON_BOX_HEIGHT // 2,
        fill=ImageColor.getrgb(MARQUEE_RING_FILL),
        outline=ImageColor.getrgb(MARQUEE_RING_STROKE),
        width=2,
    )

    if lane == "left":
        icon = load_icon_image(
            TECH_ICON_RASTER_FILES[label],
            MARQUEE_ICON_BOX_WIDTH - (6 * MARQUEE_RENDER_SCALE),
            MARQUEE_ICON_BOX_HEIGHT - (6 * MARQUEE_RENDER_SCALE),
            TECH_ICON_TINTS.get(label, ""),
        )
    else:
        icon = load_icon_image(
            PROJECT_EMOJI_RASTER_FILES[label],
            MARQUEE_ICON_BOX_WIDTH - (4 * MARQUEE_RENDER_SCALE),
            MARQUEE_ICON_BOX_HEIGHT - (4 * MARQUEE_RENDER_SCALE),
        )
    chip.alpha_composite(
        icon,
        (
            icon_box_x + ((MARQUEE_ICON_BOX_WIDTH - icon.width) // 2),
            icon_box_y + ((MARQUEE_ICON_BOX_HEIGHT - icon.height) // 2),
        ),
    )

    font = fit_label_font(label)
    bbox = font.getbbox(label)
    text_x = icon_box_x + MARQUEE_ICON_BOX_WIDTH + (8 * MARQUEE_RENDER_SCALE)
    text_y = ((MARQUEE_CHIP_HEIGHT - (bbox[3] - bbox[1])) // 2) - bbox[1] - 1
    draw.text(
        (text_x, text_y),
        label,
        font=font,
        fill=ImageColor.getrgb(MARQUEE_TEXT_COLOR),
    )
    return chip


def ease_in_out(progress: float) -> float:
    return progress * progress * (3 - 2 * progress)


def motion_alpha(delta_frame: int) -> float:
    if delta_frame < MARQUEE_FADE_IN_FRAMES:
        progress = (delta_frame + 1) / MARQUEE_FADE_IN_FRAMES
        return ease_in_out(progress)
    fade_start = MARQUEE_VISIBLE_FRAMES - MARQUEE_FADE_OUT_FRAMES
    if MARQUEE_FADE_OUT_FRAMES > 0 and delta_frame >= fade_start:
        remaining = MARQUEE_VISIBLE_FRAMES - delta_frame - 1
        progress = max(0.0, remaining / MARQUEE_FADE_OUT_FRAMES)
        return ease_in_out(progress)
    return 1.0


def exit_alpha_for_x(x: float) -> float:
    if x <= MARQUEE_EXIT_ALPHA_START_X:
        return 1.0
    progress = (x - MARQUEE_EXIT_ALPHA_START_X) / max(
        1,
        MARQUEE_END_X - MARQUEE_EXIT_ALPHA_START_X,
    )
    return max(0.0, 1.0 - ease_in_out(min(1.0, progress)))


def build_marquee_motions(lane: str) -> list[MarqueeMotion]:
    items = lane_items(lane)
    start_ys = LEFT_START_YS if lane == "left" else RIGHT_START_YS
    end_ys = LEFT_END_YS if lane == "left" else RIGHT_END_YS
    raster_files = TECH_ICON_RASTER_FILES if lane == "left" else PROJECT_EMOJI_RASTER_FILES
    tints = TECH_ICON_TINTS if lane == "left" else {}
    lane_phase = 0 if lane == "left" else MARQUEE_INTERVAL_FRAMES // 2

    motions = []
    for index, label in enumerate(items):
        motions.append(
            MarqueeMotion(
                label=label,
                asset_path=raster_files[label],
                start_frame=(lane_phase + index * MARQUEE_INTERVAL_FRAMES)
                % MARQUEE_FRAME_COUNT,
                start_y=start_ys[index] * MARQUEE_RENDER_SCALE,
                end_y=end_ys[index] * MARQUEE_RENDER_SCALE,
                tint=tints.get(label),
            )
        )
    return motions


def motion_state_for_frame(
    motion: MarqueeMotion,
    frame_index: int,
    frame_count: int,
) -> Optional[Dict[str, float]]:
    delta = (frame_index - motion.start_frame) % frame_count
    if delta >= MARQUEE_VISIBLE_FRAMES:
        return None

    alpha = motion_alpha(delta)
    if alpha <= 0:
        return None

    progress = ease_in_out(delta / max(1, MARQUEE_VISIBLE_FRAMES - 1))
    x = MARQUEE_START_X + (MARQUEE_END_X - MARQUEE_START_X) * progress
    y = motion.start_y + (motion.end_y - motion.start_y) * progress
    alpha *= exit_alpha_for_x(x)
    if alpha <= 0:
        return None
    return {"x": x, "y": y, "alpha": alpha}


def apply_chip_alpha(chip: Image.Image, alpha: float) -> Image.Image:
    if alpha >= 0.999:
        return chip
    faded = chip.copy()
    faded_alpha = faded.getchannel("A").point(lambda value: int(value * alpha))
    faded.putalpha(faded_alpha)
    return faded


def render_marquee_frames(lane: str) -> list[Image.Image]:
    motions = build_marquee_motions(lane)
    edge_mask = build_lane_edge_mask()
    frames = []

    for frame_index in range(MARQUEE_FRAME_COUNT):
        frame = Image.new(
            "RGBA",
            (MARQUEE_GIF_WIDTH, MARQUEE_GIF_HEIGHT),
            (0, 0, 0, 0),
        )
        active = []
        for motion in motions:
            state = motion_state_for_frame(motion, frame_index, MARQUEE_FRAME_COUNT)
            if state is not None:
                active.append((state["y"], motion, state))

        for _, motion, state in sorted(active):
            chip = apply_chip_alpha(build_chip_image(lane, motion.label), state["alpha"])
            frame.alpha_composite(chip, (int(state["x"]), int(state["y"])))
        frame_alpha = ImageChops.multiply(frame.getchannel("A"), edge_mask)
        frame.putalpha(frame_alpha)
        frames.append(frame)
    return frames


def frames_to_gif(frames: list[Image.Image], output_path: Path) -> None:
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=MARQUEE_FRAME_MS,
        disposal=2,
        optimize=False,
    )


def resize_marquee_frames_for_readme(frames: list[Image.Image]) -> list[Image.Image]:
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    return [
        frame.resize(
            (MARQUEE_DISPLAY_WIDTH, MARQUEE_DISPLAY_HEIGHT),
            resampling,
        )
        for frame in frames
    ]


def write_hidden_marquee_placeholder(out_dir: Path) -> None:
    (out_dir / "marquee-hidden.svg").write_text(
        MARQUEE_PLACEHOLDER_SVG,
        encoding="utf-8",
    )


def write_marquee_gifs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for lane in ("left", "right"):
        frames = render_marquee_frames(lane)
        frames_to_gif(frames, out_dir / f"marquee-{lane}.gif")
        frames_to_gif(
            resize_marquee_frames_for_readme(frames),
            out_dir / f"marquee-{lane}-display.gif",
        )
    write_hidden_marquee_placeholder(out_dir)


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
    write_marquee_gifs(out)
    print("Done → generated/overview.svg")
    print("Done → generated/marquee-left.gif")
    print("Done → generated/marquee-right.gif")
    print("Done → generated/marquee-left-display.gif")
    print("Done → generated/marquee-right-display.gif")
    print("Done → generated/marquee-hidden.svg")


if __name__ == "__main__":
    main()
