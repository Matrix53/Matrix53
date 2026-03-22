import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import mock

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

    def test_raster_assets_exist_for_all_tech_and_project_items(self):
        for label in generate_stats.TECH_STACK_ITEMS:
            asset = Path(generate_stats.TECH_ICON_RASTER_FILES[label])
            self.assertTrue(asset.exists(), f"missing tech raster for {label}: {asset}")

        for label in generate_stats.PROJECT_ITEMS:
            asset = Path(generate_stats.PROJECT_EMOJI_RASTER_FILES[label])
            self.assertTrue(
                asset.exists(),
                f"missing project emoji raster for {label}: {asset}",
            )

    def test_marquee_motion_is_sparse_and_uses_varied_paths(self):
        for lane in ("left", "right"):
            motions = generate_stats.build_marquee_motions(lane)

            self.assertEqual(len(motions), 12)
            unique_paths = {(m.start_y, m.end_y) for m in motions}
            self.assertGreaterEqual(len(unique_paths), 8)

            max_active = 0
            for frame_index in range(generate_stats.MARQUEE_FRAME_COUNT):
                active = sum(
                    1
                    for motion in motions
                    if generate_stats.motion_state_for_frame(
                        motion,
                        frame_index,
                        generate_stats.MARQUEE_FRAME_COUNT,
                    )
                    is not None
                )
                max_active = max(max_active, active)

            self.assertLessEqual(max_active, 2)

    def test_marquee_uses_high_resolution_rendering(self):
        self.assertGreater(generate_stats.MARQUEE_RENDER_SCALE, 1)
        self.assertGreater(
            generate_stats.MARQUEE_GIF_WIDTH,
            generate_stats.MARQUEE_DISPLAY_WIDTH,
        )
        self.assertGreater(
            generate_stats.MARQUEE_GIF_HEIGHT,
            generate_stats.MARQUEE_DISPLAY_HEIGHT,
        )

    def test_motion_alpha_has_multi_frame_fade_in(self):
        fade_values = [
            generate_stats.motion_alpha(i)
            for i in range(generate_stats.MARQUEE_VISIBLE_FRAMES)
        ]
        partials = [value for value in fade_values if 0 < value < 1]
        self.assertGreaterEqual(len(set(partials)), 4)
        self.assertGreater(fade_values[1], fade_values[0])
        self.assertEqual(fade_values[-1], 1.0)

    def test_exit_alpha_for_x_decreases_near_exit(self):
        self.assertEqual(
            generate_stats.exit_alpha_for_x(generate_stats.MARQUEE_EXIT_ALPHA_START_X),
            1.0,
        )
        mid = (
            generate_stats.MARQUEE_EXIT_ALPHA_START_X
            + generate_stats.MARQUEE_END_X
        ) / 2
        self.assertLess(generate_stats.exit_alpha_for_x(mid), 1.0)
        self.assertLess(
            generate_stats.exit_alpha_for_x(generate_stats.MARQUEE_END_X),
            0.05,
        )

    def test_lane_edge_mask_fades_near_boundaries(self):
        mask = generate_stats.build_lane_edge_mask()
        middle_y = generate_stats.MARQUEE_GIF_HEIGHT // 2

        self.assertLess(mask.getpixel((0, middle_y)), 8)
        self.assertGreater(
            mask.getpixel((generate_stats.MARQUEE_GIF_WIDTH // 2, middle_y)),
            240,
        )
        self.assertLess(
            mask.getpixel((generate_stats.MARQUEE_GIF_WIDTH - 1, middle_y)),
            16,
        )
        self.assertLess(
            mask.getpixel((generate_stats.MARQUEE_GIF_WIDTH - 72, middle_y)),
            240,
        )

    def test_load_icon_image_removes_opaque_white_background_before_tint(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "icon.png"
            source = generate_stats.Image.new("RGBA", (8, 8), (255, 255, 255, 255))
            for x in range(2, 6):
                for y in range(2, 6):
                    source.putpixel((x, y), (0, 0, 0, 255))
            source.save(path)

            generate_stats.load_icon_image.cache_clear()
            icon = generate_stats.load_icon_image(str(path), 8, 8, "#ff0000")

        self.assertEqual(icon.getpixel((0, 0))[3], 0)
        self.assertGreater(icon.getpixel((4, 4))[3], 200)

    def test_rendered_frames_have_expected_dimensions(self):
        left_frames = generate_stats.render_marquee_frames("left")
        right_frames = generate_stats.render_marquee_frames("right")

        self.assertEqual(len(left_frames), generate_stats.MARQUEE_FRAME_COUNT)
        self.assertEqual(len(right_frames), generate_stats.MARQUEE_FRAME_COUNT)
        self.assertEqual(
            left_frames[0].size,
            (generate_stats.MARQUEE_GIF_WIDTH, generate_stats.MARQUEE_GIF_HEIGHT),
        )
        self.assertEqual(
            right_frames[0].size,
            (generate_stats.MARQUEE_GIF_WIDTH, generate_stats.MARQUEE_GIF_HEIGHT),
        )

    def test_readme_references_existing_center_assets_and_gif_marquees(self):
        readme = Path("README.md").read_text()

        self.assertIn('<h1 align="center">Hi, I\'m Matrix53 👋</h1>', readme)
        self.assertIn(
            "https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&pause=1000&color=FE428E&center=true&vCenter=true&width=435&lines=Always+learning%2C+always+building+%F0%9F%9A%80;BUAA+%7C+SenseTime+%7C+Baidu;Video+Generation+%7C+Diffusion+Model",
            readme,
        )
        self.assertIn("https://git.io/typing-svg", readme)
        self.assertIn("generated/overview.svg", readme)
        self.assertIn("generated/marquee-left.gif", readme)
        self.assertIn("generated/marquee-right.gif", readme)
        self.assertNotIn("generated/marquee-left-top.svg", readme)
        self.assertNotIn("generated/marquee-right-top.svg", readme)
        self.assertNotIn("<table", readme)
        self.assertNotIn("<div align=\"center\">", readme)

    def test_generated_gifs_keep_transparent_background(self):
        for path in ("generated/marquee-left.gif", "generated/marquee-right.gif"):
            with generate_stats.Image.open(path) as image:
                self.assertIn("transparency", image.info, path)

    def test_load_font_tries_multiple_candidates_before_fallback(self):
        sentinel = object()
        generate_stats.load_font.cache_clear()
        with mock.patch.object(
            generate_stats,
            "FONT_BOLD_CANDIDATES",
            ["missing-bold.ttf", "fallback-bold.ttf"],
        ), mock.patch.object(
            generate_stats.ImageFont,
            "truetype",
            side_effect=[OSError("missing"), sentinel],
        ) as mocked_truetype:
            font = generate_stats.load_font(10, bold=True)

        self.assertIs(font, sentinel)
        self.assertEqual(
            mocked_truetype.call_args_list,
            [
                mock.call("missing-bold.ttf", size=10),
                mock.call("fallback-bold.ttf", size=10),
            ],
        )

    def test_load_font_uses_default_when_no_candidates_work(self):
        sentinel = object()
        generate_stats.load_font.cache_clear()
        with mock.patch.object(
            generate_stats,
            "FONT_REGULAR_CANDIDATES",
            ["missing-regular.ttf"],
        ), mock.patch.object(
            generate_stats.ImageFont,
            "truetype",
            side_effect=OSError("missing"),
        ) as mocked_truetype, mock.patch.object(
            generate_stats.ImageFont,
            "load_default",
            return_value=sentinel,
        ) as mocked_default:
            font = generate_stats.load_font(9, bold=False)

        self.assertIs(font, sentinel)
        mocked_truetype.assert_called_once_with("missing-regular.ttf", size=9)
        mocked_default.assert_called_once()


if __name__ == "__main__":
    unittest.main()
