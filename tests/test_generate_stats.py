import unittest
from pathlib import Path
import re

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

    def test_marquee_assets_exist_for_all_tech_and_project_items(self):
        for label in generate_stats.TECH_STACK_ITEMS:
            asset = Path(generate_stats.TECH_ICON_FILES[label])
            self.assertTrue(asset.exists(), f"missing tech asset for {label}: {asset}")

        for label in generate_stats.PROJECT_ITEMS:
            asset = Path(generate_stats.PROJECT_EMOJI_FILES[label])
            self.assertTrue(asset.exists(), f"missing emoji asset for {label}: {asset}")

    def test_top_marquees_use_image_based_assets_and_no_shared_speed_label(self):
        left_svg = generate_stats.marquee_left_top_svg()
        right_svg = generate_stats.marquee_right_top_svg()

        self.assertIn('class="logo-icon"', left_svg)
        self.assertNotIn('class="logo-text"', left_svg)
        self.assertNotIn("Shared speed", left_svg)

        self.assertIn('class="emoji-icon"', right_svg)
        self.assertNotIn('class="emoji"', right_svg)
        self.assertNotIn("🧪", right_svg)
        self.assertNotIn("Shared speed", right_svg)

    def test_bottom_marquees_use_sparse_single_track_motion(self):
        left_svg = generate_stats.marquee_left_bottom_svg()
        right_svg = generate_stats.marquee_right_bottom_svg()

        self.assertEqual(left_svg.count('data-slot="0"'), 1)
        self.assertEqual(right_svg.count('data-slot="0"'), 1)
        self.assertNotIn('data-slot="1"', left_svg)
        self.assertNotIn('data-slot="1"', right_svg)

    def test_marquees_share_global_duration_and_compact_width(self):
        svgs = [
            generate_stats.marquee_left_top_svg(),
            generate_stats.marquee_right_top_svg(),
            generate_stats.marquee_left_bottom_svg(),
            generate_stats.marquee_right_bottom_svg(),
        ]

        self.assertGreater(generate_stats.MARQUEE_DURATION, 0)
        self.assertLessEqual(generate_stats.MARQUEE_WIDTH, 144)
        duration = f"{generate_stats.MARQUEE_DURATION}s"

        for svg in svgs:
            self.assertIn(duration, svg)

    def test_each_lane_keeps_only_one_item_visible_at_a_time(self):
        lane_specs = [
            (generate_stats.marquee_left_top_svg(), len(generate_stats.TECH_TOP_ITEMS)),
            (generate_stats.marquee_left_bottom_svg(), len(generate_stats.TECH_BOTTOM_ITEMS)),
            (generate_stats.marquee_right_top_svg(), len(generate_stats.PROJECT_TOP_ITEMS)),
            (generate_stats.marquee_right_bottom_svg(), len(generate_stats.PROJECT_BOTTOM_ITEMS)),
        ]

        for svg, item_count in lane_specs:
            keytimes_match = re.search(r'keyTimes="([^"]+)"', svg)
            self.assertIsNotNone(keytimes_match)
            keytimes = [float(value) for value in keytimes_match.group(1).split(";")]
            visible_until = keytimes[3] * generate_stats.MARQUEE_DURATION
            item_interval = generate_stats.MARQUEE_DURATION / item_count
            self.assertLessEqual(visible_until, item_interval)

    def test_readme_keeps_existing_center_assets_without_table_layout(self):
        readme = Path("README.md").read_text()

        self.assertIn("# Hi, I'm Matrix53 👋", readme)
        self.assertIn(
            "https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&pause=1000&color=FE428E&center=true&vCenter=true&width=435&lines=Always+learning%2C+always+building+%F0%9F%9A%80;BUAA+%7C+SenseTime+%7C+Baidu;Video+Generation+%7C+Diffusion+Model",
            readme,
        )
        self.assertIn("https://git.io/typing-svg", readme)
        self.assertIn("generated/overview.svg", readme)
        self.assertNotIn("<table", readme)
        self.assertIn("generated/marquee-left-top.svg", readme)
        self.assertIn("generated/marquee-left-bottom.svg", readme)
        self.assertIn("generated/marquee-right-top.svg", readme)
        self.assertIn("generated/marquee-right-bottom.svg", readme)


if __name__ == "__main__":
    unittest.main()
