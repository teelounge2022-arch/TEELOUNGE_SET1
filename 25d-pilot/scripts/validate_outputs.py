#!/usr/bin/env python3
"""Inventory actual pilot deliverables without importing or launching Blender.

Missing files, failed checks, and checks that cannot be completed are reported
separately. This is a file/settings check, not a substitute for visual review.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

from PIL import Image, ImageStat


SCENES = ("S1", "S2", "S3", "S4")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def inspect_png(path: Path, size: tuple[int, int], depth: int | None) -> dict:
    with path.open("rb") as handle:
        header = handle.read(33)
        handle.seek(-12, 2)
        trailer = handle.read(12)
    if len(header) != 33 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("Invalid PNG signature/IHDR")
    if trailer[4:8] != b"IEND":
        raise ValueError("PNG is incomplete: final IEND chunk missing")
    width, height, actual_depth, color_type = struct.unpack(">IIBB", header[16:26])
    if (width, height) != size:
        raise ValueError(f"Expected {size[0]}x{size[1]}, found {width}x{height}")
    if depth is not None and actual_depth != depth:
        raise ValueError(f"Expected {depth}-bit PNG, found {actual_depth}-bit")
    if color_type != 2:
        raise ValueError(f"Expected PNG RGB color type 2, found {color_type}")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        image.load()
        rgb = image.convert("RGB")
        statistics = ImageStat.Stat(rgb)
        if max(statistics.stddev) < 0.5:
            raise ValueError("Image is blank or nearly uniform")
        histogram = rgb.convert("L").histogram()
        pixels = width * height
        near_black = sum(histogram[:3]) / pixels
        near_white = sum(histogram[253:]) / pixels
        warnings = []
        # A black lunar sky is intentional; report dark fractions without
        # treating a largely dark composition as a failed render.
        if near_black > 0.98:
            warnings.append("More than 98% near black: inspect composition manually")
        if near_white > 0.98:
            warnings.append("More than 98% near white: inspect clipping manually")
        return {
            "width": width, "height": height, "bit_depth": actual_depth,
            "color_type": color_type, "bytes": path.stat().st_size,
            "rgb_stddev": [round(value, 4) for value in statistics.stddev],
            "near_black_fraction": round(near_black, 6),
            "near_white_fraction": round(near_white, 6),
            "sha256": digest(path), "warnings": warnings,
        }


def inspect_blend(path: Path) -> dict:
    with path.open("rb") as handle:
        magic = handle.read(12)
    container = "uncompressed"
    if magic.startswith(b"\x1f\x8b"):
        container = "gzip"
        with gzip.open(path, "rb") as handle:
            magic = handle.read(12)
    elif magic.startswith(b"\x28\xb5\x2f\xfd"):
        container = "zstd"
        if importlib.util.find_spec("zstandard") is None:
            return {
                "status": "unverified", "container": container,
                "bytes": path.stat().st_size, "sha256": digest(path),
                "reason": "Zstd .blend detected; zstandard decoder unavailable. File content not verified.",
            }
        import zstandard
        with path.open("rb") as handle:
            with zstandard.ZstdDecompressor().stream_reader(handle) as reader:
                magic = reader.read(12)
    if len(magic) != 12 or not magic.startswith(b"BLENDER"):
        raise ValueError("Missing Blender file header after decompression")
    if path.stat().st_size < 1024:
        raise ValueError("Implausibly small Blender file")
    file_version = magic[9:12].decode("ascii", errors="replace")
    if file_version != "402":
        raise ValueError(f"Requested Blender 4.2 file version 402, found {file_version}")
    return {
        "status": "passed", "container": container,
        "file_header_version": file_version,
        "bytes": path.stat().st_size, "sha256": digest(path),
        "scope": "Header/container verified; scene contents and opening in Blender not checked",
    }


def check_receipt(path: Path, image: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"status": "complete", "engine": "CYCLES", "device": "CPU", "samples": 64, "denoiser": "OPENIMAGEDENOISE"}
    errors = [f"{name}: expected {value!r}, found {data.get(name)!r}" for name, value in required.items() if data.get(name) != value]
    if not str(data.get("blender_version", "")).startswith("4.2."):
        errors.append(f"Requested Blender 4.2 LTS, found {data.get('blender_version')!r}")
    if not image.is_file():
        errors.append("The referenced image is missing")
    elif data.get("sha256") != digest(image):
        errors.append("Image SHA-256 differs from completed render receipt")
    if errors:
        raise ValueError("; ".join(errors))
    return {"blender_version": data.get("blender_version"), "elapsed_seconds": data.get("elapsed_seconds"), "settings": required, "receipt_sha256": digest(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.output_root.resolve()
    checks: list[dict] = []

    def check(relative: str, category: str, callback) -> None:
        path = root / relative
        item = {"file": relative, "category": category}
        if not path.is_file():
            checks.append({**item, "status": "missing"})
            return
        try:
            result = callback(path)
            checks.append({**item, "status": "passed", **result})
        except Exception as error:
            checks.append({**item, "status": "failed", "reason": f"{type(error).__name__}: {error}"})

    for scene_id in SCENES:
        for letter in ("A", "B"):
            relative = f"renders/{scene_id}_camera_{letter}.png"
            image = root / relative
            check(relative, "final_png", lambda path: inspect_png(path, (2160, 3840), 16))
            check(f"metadata/{scene_id}_final_{letter}.json", "render_receipt", lambda path, image=image: check_receipt(path, image))
        check(f"looksheets/{scene_id}_looksheet.png", "looksheet", lambda path: inspect_png(path, (1080, 1920), None))
        check(f"scenes/{scene_id}.blend", "blend", inspect_blend)
        check(f"scripts/scene_{scene_id.lower()}.py", "script", lambda path: {"bytes": path.stat().st_size, "sha256": digest(path)} if path.stat().st_size else (_ for _ in ()).throw(ValueError("Empty script")))
    for name in ("common.py", "render.py", "compose_looksheets.py", "validate_outputs.py"):
        check(f"scripts/{name}", "script", lambda path: {"bytes": path.stat().st_size, "sha256": digest(path)} if path.stat().st_size else (_ for _ in ()).throw(ValueError("Empty script")))

    expected = {f"{scene_id}_camera_{letter}.png" for scene_id in SCENES for letter in ("A", "B")}
    actual = {path.name for path in (root / "renders").glob("*.png")} if (root / "renders").is_dir() else set()
    unexpected = sorted(actual - expected)
    if unexpected:
        checks.append({"file": "renders/", "category": "final_inventory", "status": "failed", "reason": "Unexpected final PNGs", "unexpected_files": unexpected})
    counts = {status: sum(item["status"] == status for item in checks) for status in ("passed", "missing", "failed", "unverified")}
    status = "failed" if counts["failed"] else "incomplete" if counts["missing"] or counts["unverified"] else "passed"
    report = {
        "status": status, "counts": counts,
        "expected_final_pngs": 8, "present_final_pngs": len(actual & expected),
        "expected_looksheets": 4, "expected_blend_files": 4,
        "automated_scope": "Existing file inventory, PNG completeness/dimensions/depth, blank checks, completed render receipts/settings/checksums, blend headers where decodable",
        "visual_review_verified": False,
        "visual_review_note": "This script cannot establish absence of noise/artifacts, correct content/composition, or reserved character space. Human visual review is still required.",
        "checks": checks,
    }
    target = root / "metadata" / "validation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(json.dumps({"status": status, "counts": counts, "present_final_pngs": report["present_final_pngs"], "report": str(target)}, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
