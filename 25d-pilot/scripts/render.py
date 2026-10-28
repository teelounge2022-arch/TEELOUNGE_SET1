#!/usr/bin/env python3
"""Rebuild and render the procedural 2.5D sets with Blender's Cycles CPU.

Examples:
  blender -b --python scripts/render.py -- --scene S1 --mode preview
  blender -b --python-exit-code 1 --python scripts/render.py -- --scene S1 --mode final --threads 4
  blender -b --python scripts/render.py -- --scene ALL --mode look

The script also accepts normal Python arguments when run by an interpreter with
the official bpy module installed. No graphics window, GPU, external textures,
or network request is needed by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct
import sys
import time
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = SCRIPT_DIR.parent
SCENES = ("S1", "S2", "S3", "S4")


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scene", type=str.upper, choices=(*SCENES, "ALL"), default="ALL")
    parser.add_argument("--mode", choices=("preview", "final", "look"), default="final")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--camera", type=str.upper, choices=("A", "B", "C", "D"), help="Render only one camera; C/D are look-sheet views only.")
    parser.add_argument("--skip-existing", action="store_true", help="Reuse complete PNGs of the expected dimensions and bit depth.")
    return parser.parse_args(argv)


def png_info(path: Path) -> dict[str, Any]:
    """Read PNG IHDR without depending on Pillow inside Blender."""
    with path.open("rb") as handle:
        header = handle.read(33)
        handle.seek(-12, 2)
        trailer = handle.read(12)
    if len(header) != 33 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Invalid PNG header: {path}")
    if trailer[4:8] != b"IEND":
        raise ValueError(f"Incomplete PNG: {path}")
    width, height, depth, color_type = struct.unpack(">IIBB", header[16:26])
    return {"width": width, "height": height, "bit_depth": depth, "color_type": color_type, "bytes": path.stat().st_size}


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def configure_render(scene: Any, mode: str, threads: int) -> None:
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16 if mode == "preview" else 64
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    if hasattr(scene.cycles, "denoising_use_gpu"):
        scene.cycles.denoising_use_gpu = False
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.02
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 4
    scene.cycles.transparent_max_bounces = 4
    scene.render.threads_mode = "FIXED"
    scene.render.threads = max(1, threads)
    scene.render.resolution_x = 2160 if mode == "final" else 540
    scene.render.resolution_y = 3840 if mode == "final" else 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.compression = 15
    scene.render.use_file_extension = True
    scene.render.film_transparent = False
    scene.render.use_persistent_data = True


def camera_info(camera: Any) -> dict[str, Any]:
    dof = camera.data.dof
    result = {
        "name": camera.name,
        "location": list(camera.location),
        "rotation_euler": list(camera.rotation_euler),
        "lens_mm": camera.data.lens,
        "sensor_width_mm": camera.data.sensor_width,
        "dof_enabled": dof.use_dof,
        "fstop": dof.aperture_fstop,
        "focus_distance": dof.focus_distance,
        "focus_object": dof.focus_object.name if dof.focus_object else None,
    }
    return result


def render_set(scene_id: str, args: argparse.Namespace, bpy: Any) -> None:
    root = args.output_root.resolve()
    for directory in ("scenes", "renders", "previews", "lookviews", "metadata"):
        (root / directory).mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    module_name = f"scene_{scene_id.lower()}"
    module = importlib.import_module(module_name)
    result = module.build()
    if not isinstance(result, dict):
        raise TypeError(f"{module_name}.build() must return a camera dictionary")
    hero_cameras = list(result.get("cameras", []))
    look_cameras = list(result.get("look_cameras", []))
    if len(hero_cameras) != 2 or any(camera.type != "CAMERA" for camera in hero_cameras):
        raise ValueError(f"{scene_id} must define exactly two hero cameras")
    if len(look_cameras) != 4 or any(camera.type != "CAMERA" for camera in look_cameras):
        raise ValueError(f"{scene_id} must define four actual look-sheet cameras")

    scene = bpy.context.scene
    scene["pilot_scene"] = scene_id
    scene["pilot_hero_cameras"] = json.dumps([camera.name for camera in hero_cameras])
    scene["pilot_look_cameras"] = json.dumps([camera.name for camera in look_cameras])
    scene["pilot_no_people_logos_or_text"] = True
    configure_render(scene, "final", args.threads)
    scene.camera = hero_cameras[0]
    # Keep the saved .blend portable when the repository is cloned elsewhere.
    scene.render.filepath = f"//../renders/{scene_id}_camera_A.png"
    scene.render.use_stamp = False
    bpy.context.preferences.filepaths.save_version = 0
    blend_path = root / "scenes" / f"{scene_id}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
    save_json(root / "metadata" / f"{scene_id}_scene.json", {
        "scene": scene_id,
        "blend_file": str(blend_path.relative_to(root)),
        "blender_version": bpy.app.version_string,
        "blender_version_tuple": list(bpy.app.version),
        "saved_render_defaults": {"engine": "CYCLES", "device": "CPU", "samples": 64, "denoiser": "OPENIMAGEDENOISE", "width": 2160, "height": 3840, "png_bit_depth": 16},
        "hero_cameras": [camera_info(camera) for camera in hero_cameras],
        "look_cameras": [camera_info(camera) for camera in look_cameras],
    })

    selected = look_cameras if args.mode == "look" else hero_cameras
    if args.camera and ord(args.camera) - ord("A") >= len(selected):
        raise ValueError("Cameras C and D can only be selected with --mode look")
    configure_render(scene, args.mode, args.threads)
    source_digest = hashlib.sha256()
    for source in (Path(__file__).resolve(), SCRIPT_DIR / "common.py", Path(module.__file__).resolve()):
        source_digest.update(source.name.encode("utf-8"))
        source_digest.update(source.read_bytes())
    source_fingerprint = source_digest.hexdigest()
    for index, camera in enumerate(selected):
        letter = chr(ord("A") + index)
        if args.camera and args.camera != letter:
            continue
        if args.mode == "look":
            relative = Path("lookviews") / f"{scene_id}_angle_{index + 1:02d}.png"
        else:
            relative = Path("renders" if args.mode == "final" else "previews") / f"{scene_id}_camera_{letter}.png"
        output = root / relative
        receipt = root / "metadata" / f"{scene_id}_{args.mode}_{letter}.json"
        if args.skip_existing and output.is_file():
            try:
                info = png_info(output)
                previous = json.loads(receipt.read_text(encoding="utf-8"))
                valid_source = previous.get("source_fingerprint") == source_fingerprint
                valid_runtime = previous.get("blender_version") == bpy.app.version_string
                valid_file = previous.get("sha256") == hashlib.sha256(output.read_bytes()).hexdigest()
                valid_size = (info["width"], info["height"], info["bit_depth"]) == (scene.render.resolution_x, scene.render.resolution_y, 16)
                if previous.get("status") == "complete" and valid_source and valid_runtime and valid_file and valid_size:
                    print(f"REUSE {relative}", flush=True)
                    continue
            except (OSError, ValueError, struct.error, json.JSONDecodeError):
                pass
        scene.camera = camera
        scene.render.filepath = str(output)
        metadata = {
            "scene": scene_id, "mode": args.mode, "camera": camera_info(camera),
            "file": str(relative), "blender_version": bpy.app.version_string,
            "engine": scene.render.engine, "device": scene.cycles.device,
            "samples": scene.cycles.samples, "denoiser": scene.cycles.denoiser,
            "threads": scene.render.threads,
            "adaptive_sampling": scene.cycles.use_adaptive_sampling,
            "adaptive_threshold": scene.cycles.adaptive_threshold,
            "source_fingerprint": source_fingerprint,
        }
        started = time.monotonic()
        print(f"RENDER {scene_id} {args.mode} camera {letter} -> {output}", flush=True)
        try:
            bpy.ops.render.render(write_still=True)
            info = png_info(output)
            if (info["width"], info["height"], info["bit_depth"]) != (scene.render.resolution_x, scene.render.resolution_y, 16):
                raise ValueError(f"Rendered PNG does not match configured output: {info}")
            metadata.update(status="complete", elapsed_seconds=round(time.monotonic() - started, 3), png=info, sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        except Exception as error:
            metadata.update(status="failed", elapsed_seconds=round(time.monotonic() - started, 3), error=str(error))
            save_json(receipt, metadata)
            raise
        save_json(receipt, metadata)
        print(f"COMPLETE {relative} ({metadata['elapsed_seconds']} seconds)", flush=True)


def main() -> None:
    args = parse_args()
    if args.threads < 1:
        raise ValueError("--threads must be a positive integer")
    sys.path.insert(0, str(SCRIPT_DIR))
    import bpy
    print(f"Runtime: Blender {bpy.app.version_string}; Cycles CPU; OIDN; mode={args.mode}", flush=True)
    for scene_id in SCENES if args.scene == "ALL" else (args.scene,):
        render_set(scene_id, args, bpy)


if __name__ == "__main__":
    main()
