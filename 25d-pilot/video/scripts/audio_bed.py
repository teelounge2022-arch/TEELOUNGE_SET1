#!/usr/bin/env python3
"""Synthesize an original, quiet 34-second lunar-golf music/SFX bed.

Uses only local NumPy/SciPy synthesis and the standard-library WAV writer.
No borrowed samples, recorded voices, network calls, or external instruments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import wave

import numpy as np
from scipy.signal import butter, sosfilt


RATE = 48_000
DURATION = 34.0
BPM = 96.0
BEAT = 60.0 / BPM
BAR = 4.0 * BEAT
SEED = 19710206


def hz(midi: float) -> float:
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


def add_event(bus: np.ndarray, samples: np.ndarray, start: float, pan: float = 0.0, gain: float = 1.0) -> None:
    offset = round(start * RATE)
    first = max(0, -offset)
    offset = max(0, offset)
    count = min(len(samples) - first, len(bus) - offset)
    if count <= 0:
        return
    source = samples[first : first + count]
    if source.ndim == 1:
        pan = np.clip(pan, -1.0, 1.0)
        bus[offset : offset + count, 0] += source * np.sqrt((1.0 - pan) / 2.0) * gain
        bus[offset : offset + count, 1] += source * np.sqrt((1.0 + pan) / 2.0) * gain
    else:
        bus[offset : offset + count] += source * gain


def envelope(length: int, attack: float, release: float) -> np.ndarray:
    result = np.ones(length)
    attack_n = min(length, round(attack * RATE))
    release_n = min(length - attack_n, round(release * RATE))
    if attack_n:
        result[:attack_n] = np.sin(np.linspace(0, np.pi / 2, attack_n)) ** 2
    if release_n:
        result[-release_n:] = np.sin(np.linspace(np.pi / 2, 0, release_n)) ** 2
    return result


def pad(note: float, duration: float, phase: float, detune: float) -> np.ndarray:
    t = np.arange(round(duration * RATE)) / RATE
    frequency = hz(note)
    fundamental = np.sin(2 * np.pi * frequency * t + phase)
    chorus = np.sin(2 * np.pi * frequency * (1 + detune) * t + phase + 0.45)
    harmonic = 0.12 * np.sin(2 * np.pi * frequency * 2 * t + phase * 0.7)
    breathing = 0.94 + 0.06 * np.sin(2 * np.pi * 0.17 * t + phase)
    return (0.68 * fundamental + 0.28 * chorus + harmonic) * breathing * envelope(len(t), 0.72, 0.85)


def pluck(note: float, velocity: float) -> np.ndarray:
    t = np.arange(round(1.15 * RATE)) / RATE
    frequency = hz(note)
    signal = (
        np.sin(2 * np.pi * frequency * t)
        + 0.18 * np.sin(2 * np.pi * frequency * 2.002 * t)
        + 0.045 * np.sin(2 * np.pi * frequency * 3.997 * t)
    )
    return signal * np.exp(-t / 0.23) * envelope(len(t), 0.008, 0.12) * velocity


def bass(note: float) -> np.ndarray:
    t = np.arange(round(1.12 * RATE)) / RATE
    frequency = hz(note)
    signal = np.sin(2 * np.pi * frequency * t) + 0.13 * np.sin(2 * np.pi * frequency * 2 * t)
    return signal * envelope(len(t), 0.028, 0.3) * np.exp(-t / 0.65)


def kick() -> np.ndarray:
    t = np.arange(round(0.24 * RATE)) / RATE
    phase = 2 * np.pi * (44 * t + 71 * 0.018 * (1 - np.exp(-t / 0.018)))
    return np.sin(phase) * np.exp(-t / 0.053) * envelope(len(t), 0.0015, 0.05)


def light_tick(rng: np.random.Generator, variation: float) -> np.ndarray:
    t = np.arange(round(0.095 * RATE)) / RATE
    noise = sosfilt(butter(2, (3500, 9500), btype="bandpass", fs=RATE, output="sos"), rng.normal(size=len(t)))
    wood = 0.12 * np.sin(2 * np.pi * (1180 + variation * 90) * t)
    return (noise * 0.18 + wood) * np.exp(-t / 0.012) * envelope(len(t), 0.001, 0.02)


def whoosh(rng: np.random.Generator, duration: float = 0.7, direction: int = 1) -> np.ndarray:
    t = np.arange(round(duration * RATE)) / RATE
    air = sosfilt(butter(3, (420, 3200), btype="bandpass", fs=RATE, output="sos"), rng.normal(size=len(t)))
    air /= max(float(np.std(air)), 1e-12)
    shape = np.sin(np.pi * t / duration) ** 2.4
    moving_pan = direction * np.linspace(-0.58, 0.58, len(t))
    air = air * shape * 0.029
    return np.column_stack((air * np.sqrt((1 - moving_pan) / 2), air * np.sqrt((1 + moving_pan) / 2)))


def golf_impact(rng: np.random.Generator, variant: int) -> np.ndarray:
    """A short, stylized club/ball thwack, not an explosion or gunshot."""
    t = np.arange(round(0.23 * RATE)) / RATE
    snap = sosfilt(butter(3, (750, 8200), btype="bandpass", fs=RATE, output="sos"), rng.normal(size=len(t)))
    snap /= max(float(np.max(np.abs(snap))), 1e-12)
    body = 0.19 * np.sin(2 * np.pi * (270 + variant * 23) * t) * np.exp(-t / 0.024)
    face = 0.16 * np.sin(2 * np.pi * ((1850 + variant * 120) * t - 1500 * t * t)) * np.exp(-t / 0.012)
    signal = snap * np.exp(-t / 0.007) + body + face
    signal *= envelope(len(t), 0.0007, 0.05)
    signal /= max(float(np.max(np.abs(signal))), 1e-12)
    return signal * (0.72 if variant == 0 else 0.64)


def synthesize() -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(SEED)
    length = round(DURATION * RATE)
    music = np.zeros((length, 2), dtype=np.float64)
    effects = np.zeros_like(music)
    chords = (
        (50, 53, 57, 60, 64),  # D minor 9
        (46, 53, 57, 62),      # B-flat major 7
        (53, 57, 60, 64),      # F major 7
        (48, 55, 62, 64),      # C add 9
    )
    roots = (38, 34, 41, 36)
    melody = ((74, 77, 72), (74, 69, 77), (76, 72, 69), (74, 79, 76))
    event_log: list[dict] = []

    # A slow-moving pad supports the edit without a continuous harsh drone.
    for bar_index in range(int(np.ceil(DURATION / BAR))):
        start = bar_index * BAR
        chord = chords[bar_index % len(chords)]
        strength = 0.026 * (0.86 if start < 5 or start > 29 else 1.0)
        for voice_index, note in enumerate(chord):
            pan = np.linspace(-0.7, 0.7, len(chord))[voice_index]
            tone = pad(note, BAR + 0.8, float(rng.uniform(0, 2 * np.pi)), float(rng.uniform(-0.0012, 0.0012)))
            add_event(music, tone, start - 0.2, float(pan), strength)
        if bar_index:
            add_event(music, bass(roots[bar_index % 4]), start + 0.025, 0.0, 0.055)
            if bar_index % 2:
                add_event(music, bass(roots[bar_index % 4] + 7), start + 2 * BEAT, 0.0, 0.035)
        if start >= 2.5 and start < 30:
            for beat in (0, 2):
                add_event(music, kick(), start + beat * BEAT, 0.0, 0.061 if beat == 0 else 0.043)
            for beat in (1.0, 2.5, 3.0):
                add_event(music, light_tick(rng, bar_index % 3), start + beat * BEAT, -0.22 if beat < 2 else 0.25, 0.13)
        if bar_index % 2 == 0 and start > 2:
            for index, note in enumerate(melody[(bar_index // 2) % 4]):
                time = start + (0.5 + index * 1.0) * BEAT
                voice = pluck(note, 0.021 if index != 1 else 0.016)
                pan = (-0.32, 0.2, -0.12)[index]
                add_event(music, voice, time, pan)
                add_event(music, voice, time + BEAT * 0.75, -pan, 0.22)
                add_event(music, voice, time + BEAT * 1.5, pan * 0.4, 0.085)

    # Sparse, softened reflections provide space without muddy long tails.
    dry = music.copy()
    for delay, gain, swapped in ((0.089, 0.075, True), (0.153, 0.05, False), (0.241, 0.032, True)):
        offset = round(delay * RATE)
        reflection = dry[:-offset, ::-1] if swapped else dry[:-offset]
        music[offset:] += reflection * gain
    music = sosfilt(butter(2, 6500, btype="lowpass", fs=RATE, output="sos"), music, axis=0)
    music_rms_before = float(np.sqrt(np.mean(music * music)))
    music *= 0.054 / max(music_rms_before, 1e-12)

    # Subtle ducking at incoming subtitle beats, deeper beneath the two hits.
    timeline = np.arange(length) / RATE
    duck = np.ones(length)
    for time in (3.4, 8.0, 13.0, 24.0, 29.0):
        duck *= 1 - 0.20 * np.exp(-0.5 * ((timeline - time - 0.08) / 0.31) ** 2)
    for time in (16.0, 20.0):
        duck *= 1 - 0.47 * np.exp(-0.5 * ((timeline - time) / 0.28) ** 2)
    music *= duck[:, None]

    for index, time in enumerate((3.4, 8.0, 13.0, 24.0, 29.0)):
        add_event(effects, whoosh(rng, direction=1 if index % 2 == 0 else -1), time - 0.32)
        event_log.append({"type": "soft_whoosh", "center_seconds": time, "duration_seconds": 0.7})
    for variant, time in enumerate((16.0, 20.0)):
        add_event(effects, whoosh(rng, 0.22, direction=1 if variant == 0 else -1), time - 0.21, gain=0.6)
        impact = golf_impact(rng, variant)
        add_event(effects, impact, time, -0.08 if variant == 0 else 0.08)
        add_event(effects, impact, time + 0.038, 0.15 if variant == 0 else -0.15, 0.055)
        event_log.append({"type": "golf_impact", "time_seconds": time, "duration_seconds": 0.23})

    master = music + effects
    master = sosfilt(butter(2, 24, btype="highpass", fs=RATE, output="sos"), master, axis=0)
    master = sosfilt(butter(2, 12_500, btype="lowpass", fs=RATE, output="sos"), master, axis=0)
    master *= envelope(length, 0.95, 1.65)[:, None]
    target_peak = 10 ** (-1.0 / 20)
    gain = target_peak / max(float(np.max(np.abs(master))), 1e-12)
    master *= gain
    # Quiet TPDF dither before the single final 16-bit quantization.
    master += (rng.random(master.shape) - rng.random(master.shape)) / 65_536
    pcm = np.rint(np.clip(master, -0.999, 0.999) * 32767).astype("<i2")
    decoded = pcm.astype(np.float64) / 32768.0
    peak = float(np.max(np.abs(decoded)))
    rms = float(np.sqrt(np.mean(decoded * decoded)))
    info = {
        "duration_seconds": len(pcm) / RATE,
        "sample_rate_hz": RATE, "channels": 2, "sample_width_bits": 16,
        "sample_frames": len(pcm), "tempo_bpm": BPM, "seed": SEED,
        "peak_linear": peak, "peak_dbfs": round(20 * np.log10(max(peak, 1e-15)), 4),
        "rms_linear": rms, "rms_dbfs": round(20 * np.log10(max(rms, 1e-15)), 4),
        "clipped_sample_count": int(np.count_nonzero(np.abs(pcm.astype(np.int32)) >= 32767)),
        "intro_fade_seconds": 0.95, "outro_fade_seconds": 1.65,
        "music": "Original D-minor/minor-9 warm pad, restrained pluck, soft bass, light kick/ticks with sparse stereo reflections",
        "effects": sorted(event_log, key=lambda event: event.get("time_seconds", event.get("center_seconds", 0))),
        "subtitle_duck_centers_seconds": [3.4, 8.0, 13.0, 16.0, 20.0, 24.0, 29.0],
        "source": "Local original procedural synthesis; no borrowed music, samples, voices, TTS or external downloads",
        "voiceover_present": False,
        "scientific_note": "Impact and whoosh cues are stylized editorial effects, not a claim that sound propagates through the lunar vacuum.",
    }
    return pcm, info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.output_root.resolve()
    output = root / "audio" / "music_sfx.wav"
    metadata = root / "metadata" / "audio_info.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    pcm, info = synthesize()
    with wave.open(str(output), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(pcm.tobytes())
    # Verify the actual saved header, length and numeric samples, not just intent.
    with wave.open(str(output), "rb") as handle:
        if (handle.getnchannels(), handle.getsampwidth(), handle.getframerate(), handle.getnframes()) != (2, 2, RATE, round(DURATION * RATE)):
            raise RuntimeError("Saved WAV does not match the requested format/duration")
        actual = np.frombuffer(handle.readframes(handle.getnframes()), dtype="<i2")
        if not np.array_equal(actual, pcm.reshape(-1)):
            raise RuntimeError("Saved WAV sample data differs from the synthesized master")
    if info["peak_dbfs"] >= -0.8 or info["clipped_sample_count"]:
        raise RuntimeError("Master peak/clipping requirement failed")
    info["file"] = str(output.relative_to(root))
    info["file_bytes"] = output.stat().st_size
    info["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    info["saved_wav_verified"] = True
    metadata.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"file": str(output), "metadata": str(metadata), "duration_seconds": info["duration_seconds"], "peak_dbfs": info["peak_dbfs"], "rms_dbfs": info["rms_dbfs"], "clipped_sample_count": info["clipped_sample_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
