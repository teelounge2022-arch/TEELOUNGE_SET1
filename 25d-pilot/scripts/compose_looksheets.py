#!/usr/bin/env python3
"""Compose real camera renders into text-free, four-angle portrait look sheets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps, ImageStat


SCENES = ("S1", "S2", "S3", "S4")


def inspect_image(path: Path) -> dict:
    with Image.open(path) as image:
        image.load()
        if image.size != (540, 960):
            raise ValueError(f"Expected a 540x960 real look view, got {image.size}: {path}")
        rgb = image.convert("RGB")
        stat = ImageStat.Stat(rgb)
        if max(stat.stddev) < 0.5:
            raise ValueError(f"Blank or nearly uniform look view: {path}")
        gray = rgb.convert("L")
        histogram = gray.histogram()
        pixels = gray.width * gray.height
        return {
            "file": path.name, "width": image.width, "height": image.height,
            "rgb_mean": [round(value, 3) for value in stat.mean],
            "rgb_stddev": [round(value, 3) for value in stat.stddev],
            "near_black_fraction": round(sum(histogram[:3]) / pixels, 5),
            "near_white_fraction": round(sum(histogram[253:]) / pixels, 5),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }


def compose(root: Path, scene_id: str) -> dict:
    sources = [root / "lookviews" / f"{scene_id}_angle_{index:02d}.png" for index in range(1, 5)]
    metrics = [inspect_image(path) for path in sources]
    canvas = Image.new("RGB", (1080, 1920), (0, 0, 0))
    gap = 6
    cell_width = (canvas.width - 3 * gap) // 2
    cell_height = (canvas.height - 3 * gap) // 2
    for index, path in enumerate(sources):
        with Image.open(path) as image:
            # Preserve the entire camera frame; no crops, labels, or annotations.
            thumbnail = ImageOps.contain(image.convert("RGB"), (cell_width, cell_height), Image.Resampling.LANCZOS)
            column, row = index % 2, index // 2
            left = gap + column * (cell_width + gap) + (cell_width - thumbnail.width) // 2
            top = gap + row * (cell_height + gap) + (cell_height - thumbnail.height) // 2
            canvas.paste(thumbnail, (left, top))
    output = root / "looksheets" / f"{scene_id}_looksheet.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", compress_level=6)
    return {
        "scene": scene_id, "file": str(output.relative_to(root)),
        "width": 1080, "height": 1920,
        "layout": "top-left=01, top-right=02, bottom-left=03, bottom-right=04",
        "labels_or_logos_added": False,
        "source_metrics": metrics,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--scene", type=str.upper, choices=(*SCENES, "ALL"), default="ALL")
    args = parser.parse_args()
    root = args.output_root.resolve()
    scenes = SCENES if args.scene == "ALL" else (args.scene,)
    for scene_id in scenes:
        report = compose(root, scene_id)
        report_path = root / "metadata" / f"{scene_id}_looksheet.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"COMPLETE {report['file']} ({report['width']}x{report['height']})")


if __name__ == "__main__":
    main()
