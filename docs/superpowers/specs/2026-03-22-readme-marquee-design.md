# README Marquee Design

Date: 2026-03-22
Status: Approved in discussion, pending written-spec review

## Goal

Improve the visual balance of the profile README header by filling the left and right whitespace around the existing typing slogan and GitHub stats with animated marquee lanes.

The center content must keep the current visual identity. The marquee should add motion and density around it without redesigning it.

## Accepted Constraints

- Do not change the current typing slogan copy.
- Do not change the current `generated/overview.svg` card design.
- Do not redraw the center content into a new custom hero card.
- Use the accepted `A`-style boundary treatment: content fades out before colliding with the center boundary.
- Both marquee lanes move left-to-right in screen coordinates.
- Left lane items use `Logo + Name`.
- Right lane items use `Emoji + Project Name`.
- Left and right lanes must stay visually symmetric.
- Marquee speed is controlled by a single global parameter shared by both lanes.
- Hover-to-pause and per-item click-through are explicitly out of scope for the GitHub README implementation.

## Design Summary

The README header becomes a symmetric composition with three visual regions:

1. Left marquee lane
2. Existing center content
3. Right marquee lane

The center region continues to use the current title, typing SVG, and stats SVG exactly as they already exist in the repository. The new work only adds animated side lanes and the surrounding layout needed to place them.

## Layout

### Visual Structure

- The header reads as a single centered composition with equal-weight motion on both sides.
- The center column keeps:
  - `# Hi, I'm Matrix53 👋`
  - the existing typing SVG
  - the existing `generated/overview.svg`
- The marquee lanes occupy the whitespace to the left and right of the center column.
- The left and right lanes use mirrored spacing, mirrored fade masks, equal chip sizes, equal vertical rhythm, and the same animation duration.

### Recommended Implementation Shape

Preferred approach:

- Use an HTML table or equivalent README-safe layout with three columns:
  - left marquee asset
  - center stacked content
  - right marquee asset
- The center column stacks the existing title, typing SVG, and stats card without re-rendering them.
- The left and right columns render animated SVG marquee assets sized to visually wrap the center stack.

Fallback if GitHub rendering makes the preferred layout unstable:

- Use two synchronized three-column rows:
  - row 1 wraps the typing SVG
  - row 2 wraps the stats card
- The two rows must still read as one symmetric marquee system.

Acceptance rule:

- The user should still recognize the center slogan and stats block as the same assets from the current repository, not as recreated approximations.

## Motion Design

### Left Lane

- Items enter from the far left of the visible lane.
- Items move toward the center.
- Items fade out shortly before the center boundary.
- Motion is continuous and calm rather than aggressive.

### Right Lane

- Items appear at the left edge of the right-side whitespace area, near the center-right boundary.
- Items continue moving toward the far right edge.
- Items fade out before or at the outer right boundary.
- This preserves the approved left-to-right motion while still filling the right-side blank area.

### Shared Motion Rules

- One global speed parameter controls both lanes.
- Both lanes use the same duration, row spacing, and cadence.
- Delays between rows are staggered but deterministic.
- Motion should feel readable at a glance, not fast enough to become flicker.

## Tunable Parameters

These should be implementation parameters, not hardcoded magic numbers scattered across the SVGs.

- `MARQUEE_DURATION`
  - Single global duration for both left and right lanes.
- `LANE_WIDTH`
  - Shared visible width for each marquee lane.
- `CHIP_HEIGHT`
  - Shared pill height.
- `ROW_OFFSETS`
  - Vertical positions for each marquee row.
- `CENTER_FADE_WIDTH`
  - Fade-mask width near the center boundary.
- `EDGE_FADE_WIDTH`
  - Fade-mask width near the far outer boundary.
- `ROW_STAGGER_DELAYS`
  - Offsets used to stagger row start times while keeping symmetry.

## Content Lists

### Left Lane: Tech Stack

Final approved default list:

- PyTorch
- CUDA
- Diffusers
- Transformers
- OpenCV
- Python
- Rust
- Go
- Electron
- Vue 3
- MPI
- OpenMP

Approved backup replacements:

- TypeScript
- Gin
- Pthread
- JavaFX

### Right Lane: Projects

Final approved default list:

- ELBO-T2IAlign
- DiffSegmenter
- PhoeniX
- PhoeniX Server
- Parallel Programming
- Calcium
- Mario
- Match Maltese
- Algo
- Gobang
- Calendar
- Hazelnut React

Approved backup replacements:

- Matrix53 Blog
- Matrix53 Homepage

## Visual Styling

### Tech Chips

- Form: `Logo + Name`
- Logos should be clean and minimal.
- Use official-style logos where practical and visually readable at small size.
- If an official logo is unavailable or visually noisy, use a consistent lettermark badge instead.
- Logo treatment must remain consistent across the whole lane.

### Project Chips

- Form: `Emoji + Project Name`
- Emoji should be lightweight, readable, and varied.
- Emoji choice should reinforce the project’s character without becoming silly or noisy.
- Project names should use short display labels where needed for lane readability.

### Color and Density

- The side lanes should visually support the existing center palette rather than compete with it.
- Chip contrast must remain readable against GitHub light and dark surfaces as much as possible within the SVG design.
- Motion density should be enough to solve the whitespace problem, but not so dense that it distracts from the center.

## Non-Goals

- No interactive hover behavior.
- No per-chip hyperlinks.
- No redesign of the center typing SVG.
- No redesign of the existing stats SVG.
- No attempt to turn the README into a full landing page.

## Source Basis For Content Selection

The approved lists were derived from the user’s public GitHub presence and representative repositories, with emphasis on research, systems, and a smaller amount of frontend work.

Primary public sources reviewed:

- `https://github.com/Matrix53`
- `https://github.com/VCG-team/elbo-t2ialign`
- `https://github.com/VCG-team/DiffSegmenter`
- `https://github.com/phoenix-next/phoenix`
- `https://github.com/phoenix-next/phoenix-server`
- `https://github.com/Matrix53/parallel-programming`
- `https://github.com/Matrix53/calcium`
- `https://github.com/Matrix53/Match-Maltese`
- `https://github.com/Matrix53/Mario`
- `https://github.com/Matrix53/hazelnut-frontend-react`

## Acceptance Criteria

- The center slogan and stats remain visually identical to the current repository versions.
- The left lane reads as `Logo + Name`.
- The right lane reads as `Emoji + Project Name`.
- Both lanes are symmetric in structure and timing.
- Both lanes move left-to-right.
- The left lane fades before hitting the center boundary.
- The right lane enters near the center-right edge and exits toward the far right.
- One global speed parameter can speed up or slow down both lanes together.
- The whitespace problem is visibly improved without making the center feel crowded.
