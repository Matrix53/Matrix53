# README Marquee Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add symmetric left/right marquee lanes to the profile README header while preserving the current typing slogan and GitHub stats visuals unchanged in the center.

**Architecture:** Keep the center content as the existing README title, typing SVG URL, and `generated/overview.svg`. Generate two new SVG assets from Python for the left and right marquee lanes, then place them around the existing center content using a README-safe three-column layout. Use one shared marquee-duration constant so both lanes stay visually symmetric.

**Tech Stack:** Python 3, built-in `unittest`, SVG generation, GitHub Actions, GitHub profile README HTML/Markdown

---

## File Structure

### Existing files to modify

- `README.md`
  - Replace the single centered stack with a README-safe multi-column layout that keeps the existing center assets untouched and adds left/right marquee assets around them.
- `generate_stats.py`
  - Refactor the generator so it can emit:
    - the existing `generated/overview.svg`
    - new `generated/marquee-left.svg`
    - new `generated/marquee-right.svg`
  - Add explicit constants for the approved content lists and the single global marquee speed parameter.
- `.github/workflows/github-stats.yml`
  - Keep using the same generator entrypoint while ensuring all generated SVG assets are committed.

### Files to create

- `tests/test_generate_stats.py`
  - Regression and behavior tests for SVG generation and approved marquee invariants.
- `tests/__init__.py`
  - Make the test package importable for `python3 -m unittest`.

## Chunk 1: Generator Test Harness And Refactor Boundary

### Task 1: Add generator-focused tests before changing production code

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_generate_stats.py`
- Modify: `generate_stats.py`

- [ ] **Step 1: Write the failing tests for marquee generation helpers**

Add tests that expect `generate_stats.py` to expose or support:
- a shared marquee duration constant
- a left marquee SVG function
- a right marquee SVG function
- current overview SVG generation still available

Include assertions for:
- left and right marquee outputs contain the approved content names
- both marquee outputs include the same duration value
- left and right outputs contain distinct directional animation markers
- overview SVG still contains the existing title and footer content

- [ ] **Step 2: Run the tests to verify they fail for the right reason**

Run:

```bash
python3 -m unittest -v tests.test_generate_stats
```

Expected:
- failure because marquee constants/functions do not exist yet
- no unrelated import or syntax errors

- [ ] **Step 3: Refactor `generate_stats.py` just enough to support testable generation units**

Add focused helpers and constants without changing output behavior yet:
- content lists for tech stack and project names
- single marquee speed constant
- small helper functions for SVG escaping and chip generation
- a shape that allows generating the overview SVG separately from marquee SVGs

- [ ] **Step 4: Re-run the targeted tests**

Run:

```bash
python3 -m unittest -v tests.test_generate_stats
```

Expected:
- some tests still fail because marquee output details are not implemented yet
- import and helper-level failures are resolved

- [ ] **Step 5: Commit the test harness and refactor boundary**

```bash
git add tests/__init__.py tests/test_generate_stats.py generate_stats.py
git commit -m "test: add marquee svg generator coverage"
```

## Chunk 2: Implement Symmetric Marquee SVG Assets

### Task 2: Generate `marquee-left.svg` and `marquee-right.svg`

**Files:**
- Modify: `generate_stats.py`
- Test: `tests/test_generate_stats.py`

- [ ] **Step 1: Extend the failing tests with exact approved marquee requirements**

Add or tighten tests for:
- left lane uses the approved 12 tech stack names
- right lane uses the approved 12 project names
- left lane items render as `Logo + Name`
- right lane items render as `Emoji + Project Name`
- both lanes move left-to-right in screen coordinates
- left lane fades before the center boundary
- right lane enters near the center-right boundary and exits to the far right
- left and right SVGs share width, height, row offsets, and duration

- [ ] **Step 2: Run tests and confirm RED**

Run:

```bash
python3 -m unittest -v tests.test_generate_stats
```

Expected:
- failures specifically tied to missing or incorrect marquee SVG behavior

- [ ] **Step 3: Implement the minimal marquee SVG generators**

Implement in `generate_stats.py`:
- `MARQUEE_DURATION`
- approved tech stack and project content lists
- a mirrored lane layout with shared dimensions and row spacing
- left-lane fade mask near the center
- right-lane entry near center-right plus fade near the outer edge
- compact, readable logo badges for tech stack items
- emoji-prefixed project chips
- writing of:
  - `generated/marquee-left.svg`
  - `generated/marquee-right.svg`

Keep `generated/overview.svg` visually unchanged.

- [ ] **Step 4: Run tests and confirm GREEN**

Run:

```bash
python3 -m unittest -v tests.test_generate_stats
```

Expected:
- all tests pass

- [ ] **Step 5: Run the generator locally**

Run:

```bash
python3 generate_stats.py
```

Expected:
- `generated/overview.svg` regenerated
- `generated/marquee-left.svg` created
- `generated/marquee-right.svg` created

- [ ] **Step 6: Commit the marquee asset generation**

```bash
git add generate_stats.py tests/test_generate_stats.py generated/marquee-left.svg generated/marquee-right.svg generated/overview.svg
git commit -m "feat: generate symmetric readme marquee svgs"
```

## Chunk 3: Integrate New SVGs Into README Without Redrawing The Center

### Task 3: Update the README layout

**Files:**
- Modify: `README.md`
- Test: `tests/test_generate_stats.py`

- [ ] **Step 1: Write a failing README integration test**

Add assertions that `README.md`:
- still contains the exact current typing SVG URL
- still references `generated/overview.svg`
- adds references to `generated/marquee-left.svg`
- adds references to `generated/marquee-right.svg`
- uses a README-safe symmetric layout rather than replacing the center assets

- [ ] **Step 2: Run tests and confirm RED**

Run:

```bash
python3 -m unittest -v tests.test_generate_stats
```

Expected:
- README integration assertions fail before the layout is updated

- [ ] **Step 3: Update `README.md` with the minimal symmetric layout**

Implement a GitHub-safe three-column composition or two synchronized rows if needed, with these rules:
- preserve the existing title text
- preserve the existing typing SVG URL string unchanged
- preserve the existing overview SVG asset reference unchanged
- place the left marquee asset in the left whitespace region
- place the right marquee asset in the right whitespace region
- keep layout centered and symmetric

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
python3 -m unittest -v tests.test_generate_stats
```

Expected:
- README layout assertions pass

- [ ] **Step 5: Commit the README integration**

```bash
git add README.md tests/test_generate_stats.py
git commit -m "feat: integrate marquee lanes into profile readme"
```

## Chunk 4: Workflow Verification And Final Checks

### Task 4: Verify the end-to-end generation path

**Files:**
- Modify: `.github/workflows/github-stats.yml` if needed
- Modify: `generate_stats.py` if final cleanup is required
- Test: `tests/test_generate_stats.py`

- [ ] **Step 1: Add any final regression checks needed for workflow compatibility**

If the current workflow already runs `python3 generate_stats.py` successfully without changes, keep the workflow file unchanged. If any assumptions changed, add the smallest workflow adjustment necessary.

- [ ] **Step 2: Run the full local verification set**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 generate_stats.py
```

Expected:
- all tests pass
- all three generated SVGs are produced without error

- [ ] **Step 3: Manually inspect the generated SVG references**

Check:
- `generated/overview.svg` still matches the existing visual design intent
- `generated/marquee-left.svg` and `generated/marquee-right.svg` are present
- README references point at the generated assets

- [ ] **Step 4: Commit any final workflow or cleanup changes**

```bash
git add .github/workflows/github-stats.yml generate_stats.py README.md tests generated/
git commit -m "chore: finalize readme marquee generation"
```

## Notes For Execution

- Do not change the current typing slogan copy.
- Do not redesign `generated/overview.svg`.
- Do not introduce README interactions that GitHub cannot support.
- Keep the implementation DRY: shared constants for dimensions, rows, and duration.
- Prefer a small number of focused helper functions in `generate_stats.py` over one giant SVG string builder.

Plan complete and saved to `docs/superpowers/plans/2026-03-22-readme-marquee-implementation.md`. Ready to execute.
