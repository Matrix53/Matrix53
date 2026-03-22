import re
import unittest
from pathlib import Path

import generate_stats


class GenerateStatsTest(unittest.TestCase):
    def test_overview_svg_keeps_existing_title_and_footer(self):
        svg = generate_stats.overview_svg(
            stars=130,
            commits=1600,
            prs=28,
            issues=18,
            repos=24,
            contributed=31,
        )

        self.assertIn("Matrix53's GitHub Stats", svg)
        self.assertIn("All-time stats · Updated by GitHub Actions", svg)
        self.assertIn("Total Stars", svg)
        self.assertIn("Total Repos", svg)

    def test_marquee_lists_match_approved_defaults(self):
        self.assertEqual(
            generate_stats.TECH_STACK_ITEMS,
            [
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
            ],
        )
        self.assertEqual(
            generate_stats.PROJECT_ITEMS,
            [
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
            ],
        )

    def test_left_marquee_uses_logo_name_and_fades_before_center(self):
        svg = generate_stats.marquee_left_svg()

        self.assertIn("PyTorch", svg)
        self.assertIn("OpenMP", svg)
        self.assertIn('class="logo-badge"', svg)
        self.assertIn("left-to-right-left", svg)
        self.assertIn("center-fade-stop", svg)
        self.assertNotIn("emoji-badge", svg)

    def test_right_marquee_uses_emoji_name_and_moves_left_to_right(self):
        svg = generate_stats.marquee_right_svg()

        self.assertIn("ELBO-T2IAlign", svg)
        self.assertIn("Hazelnut React", svg)
        self.assertIn('class="emoji-badge"', svg)
        self.assertIn("left-to-right-right", svg)
        self.assertIn("outer-fade-stop", svg)
        self.assertNotIn("logo-badge", svg)

    def test_marquees_share_global_duration_and_dimensions(self):
        left_svg = generate_stats.marquee_left_svg()
        right_svg = generate_stats.marquee_right_svg()

        self.assertGreater(generate_stats.MARQUEE_DURATION, 0)
        duration = f"{generate_stats.MARQUEE_DURATION}s"
        self.assertIn(duration, left_svg)
        self.assertIn(duration, right_svg)

        expected_viewbox = (
            f'viewBox="0 0 {generate_stats.MARQUEE_WIDTH} '
            f'{generate_stats.MARQUEE_HEIGHT}"'
        )
        self.assertIn(expected_viewbox, left_svg)
        self.assertIn(expected_viewbox, right_svg)

    def test_readme_references_existing_center_assets_and_new_marquees(self):
        readme = Path("README.md").read_text()

        self.assertIn("# Hi, I'm Matrix53 👋", readme)
        self.assertIn(
            "https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&pause=1000&color=FE428E&center=true&vCenter=true&width=435&lines=Always+learning%2C+always+building+%F0%9F%9A%80;BUAA+%7C+SenseTime+%7C+Baidu;Video+Generation+%7C+Diffusion+Model",
            readme,
        )
        self.assertIn(
            "https://git.io/typing-svg",
            readme,
        )
        self.assertIn("generated/overview.svg", readme)
        self.assertIn("generated/marquee-left.svg", readme)
        self.assertIn("generated/marquee-right.svg", readme)
        self.assertRegex(readme, r"<table[^>]*align=\"center\"")

    def test_marquee_rows_are_symmetric(self):
        left_svg = generate_stats.marquee_left_svg()
        right_svg = generate_stats.marquee_right_svg()

        left_rows = re.findall(r'data-row="(\d+)"', left_svg)
        right_rows = re.findall(r'data-row="(\d+)"', right_svg)
        self.assertEqual(left_rows, right_rows)
        self.assertEqual(len(left_rows), len(generate_stats.TECH_STACK_ITEMS))


if __name__ == "__main__":
    unittest.main()
