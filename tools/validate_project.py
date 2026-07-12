#!/usr/bin/env python3
"""Complete static validation for Beneath the Peel's Godot project."""
from __future__ import annotations

import re
import hashlib
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS: list[str] = []
ERRORS: list[str] = []


def ok(message: str) -> None:
    CHECKS.append("PASS  " + message)


def fail(message: str) -> None:
    ERRORS.append("FAIL  " + message)


def run_tool(command: list[str], label: str) -> None:
    if shutil.which(command[0]) is None:
        CHECKS.append(f"SKIP  {label} ({command[0]} not installed)")
        return
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        ok(label)
    else:
        fail(label + "\n" + (result.stdout + result.stderr).strip())


def validate_resource_references() -> None:
    references: set[str] = set()
    paths = [ROOT / "project.godot"]
    for extension in ("*.gd", "*.tscn", "*.tres"):
        paths.extend(ROOT.rglob(extension))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        references.update(re.findall(r'res://[^"\s\)\],]+', text))
    missing = [ref for ref in sorted(references) if not (ROOT / ref.removeprefix("res://")).exists()]
    if missing:
        fail("Missing res:// references: " + ", ".join(missing))
    else:
        ok(f"All {len(references)} Godot resource references resolve")


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        if file.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG")
        length = struct.unpack(">I", file.read(4))[0]
        if file.read(4) != b"IHDR" or length < 8:
            raise ValueError("missing IHDR")
        return struct.unpack(">II", file.read(8))


CHARACTER_SHA256 = {
    "banana_sheet.png": "ab2c514592ce0703fe9654842364a5828cc948d968501c3f2ce7053ee9bd7a41",
    "cavendish_sheet.png": "a1b2bc8a6c13f752532b7415f52285e87252d2119f3952771e1daaf42337cce5",
    "cult_leader_sheet.png": "4ed03b39bf5212f082e6f64fa85b00a9cb0447641e9dd10a88b22307e3171dbd",
    "cultist_sheet.png": "0769115543a9f79e0690104a7534a5954ccc499d3b5c061815f0212cacfbad9d",
    "guard_sheet.png": "2bf34c93e0bbe274ffc60c9564390a6cf1e0214b41d64563a8a5658012f2bcdc",
    "player_robed_sheet.png": "40f262a4d51ea0699e1412ceedbcaea633c007f3ddacd3e7e4a0cfa31e89a480",
    "player_sheet.png": "71d18644854d1e9de64ab9a4f37bdd1402a1473e1f031cf54489b8ca1c50de84",
}


def validate_images() -> None:
    pngs = sorted(ROOT.rglob("*.png"))
    bad: list[str] = []
    for path in pngs:
        try:
            width, height = png_size(path)
            if width <= 0 or height <= 0:
                bad.append(str(path.relative_to(ROOT)))
        except Exception as exc:  # noqa: BLE001
            bad.append(f"{path.relative_to(ROOT)} ({exc})")
    for name, expected_hash in CHARACTER_SHA256.items():
        path = ROOT / "assets/characters" / name
        if not path.exists() or png_size(path) != (64, 64):
            bad.append(f"assets/characters/{name} must exist at 64x64")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            bad.append(f"assets/characters/{name} was modified")
    atlas = ROOT / "assets/tiles/btp_environment_tiles.png"
    if not atlas.exists() or png_size(atlas) != (256, 96):
        bad.append("assets/tiles/btp_environment_tiles.png must be a 16x6 atlas at 256x96")
    if bad:
        fail("PNG validation: " + "; ".join(bad))
    else:
        ok(f"All {len(pngs)} PNG files and unchanged character sheets are valid")


def validate_audio() -> None:
    wavs = sorted((ROOT / "assets/audio").glob("*.wav"))
    bad: list[str] = []
    seconds = 0.0
    for path in wavs:
        try:
            with wave.open(str(path), "rb") as audio:
                if audio.getnframes() <= 0 or audio.getframerate() <= 0 or audio.getnchannels() not in (1, 2):
                    bad.append(path.name)
                seconds += audio.getnframes() / audio.getframerate()
        except Exception as exc:  # noqa: BLE001
            bad.append(f"{path.name} ({exc})")
    if bad:
        fail("WAV validation: " + "; ".join(bad))
    else:
        ok(f"All {len(wavs)} WAV files decode ({seconds:.1f}s total audio)")


def validate_aseprite_sources() -> None:
    expected = {
        "Grian.ase": (16, 16),
        "Mumbo-Vampire.ase": (16, 16),
        "Grian-PickleHarry-Detective.ase": (32, 32),
    }
    missing = []
    for name, size in expected.items():
        path = ROOT / "assets/source" / name
        if not path.exists():
            missing.append(name)
            continue
        raw = path.read_bytes()[:16]
        if len(raw) < 16 or struct.unpack_from("<H", raw, 4)[0] != 0xA5E0 or struct.unpack_from("<HH", raw, 8) != size:
            missing.append(name + " invalid")
    if missing:
        fail("Aseprite source validation: " + ", ".join(missing))
    else:
        ok("All three supplied Aseprite sources are preserved and valid")


def validate_no_legacy_room_images() -> None:
    background_dir = ROOT / "assets/backgrounds"
    remaining = sorted(path.name for path in background_dir.glob("*.png"))
    if remaining != ["banana_earth.png"]:
        fail("Legacy room images remain in assets/backgrounds: " + ", ".join(remaining))
    else:
        ok("No legacy full-room images remain; only the special Banana Earth ending artwork is retained")


def run_python_validator(script: str, label: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        lines = [line for line in result.stdout.splitlines() if line.startswith("PASS:")]
        ok(label + (f" ({len(lines)} subchecks)" if lines else ""))
    else:
        fail(label + "\n" + (result.stdout + result.stderr).strip())




def validate_export_annotations() -> None:
    bad: list[str] = []
    enum_pattern = re.compile(r"@export_enum\(([^)]*)\)")
    for path in sorted((ROOT / "scripts").glob("*.gd")):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = enum_pattern.search(line)
            if match is None:
                continue
            values = [part.strip() for part in match.group(1).split(",")]
            if any(value in ('""', "''") for value in values):
                bad.append(f"{path.name}:{line_number}")
    if bad:
        fail("Empty @export_enum arguments: " + ", ".join(bad))
    else:
        ok("All @export_enum declarations use non-empty editor labels")


def validate_title_menu_polish() -> None:
    scene_path = ROOT / "scenes/ui/title_menu.tscn"
    script_path = ROOT / "scripts/title_menu.gd"
    rain_path = ROOT / "scripts/menu_rain.gd"
    if not scene_path.exists() or not script_path.exists() or not rain_path.exists():
        fail("Suspense title menu scene or scripts are missing")
        return
    scene = scene_path.read_text(encoding="utf-8")
    script = script_path.read_text(encoding="utf-8")
    required_scene = (
        "BeginButton", "OptionsButton", "CreditsButton", "QuitButton",
        "OptionsOverlay", "MasterSlider", "FullscreenToggle", "VSyncToggle",
        "InfoOverlay", "Selector", "RainOverlay", "NarratorAccent",
    )
    required_script = (
        "_load_settings", "_save_settings", "_show_overlay",
        "window_set_mode", "window_set_vsync_mode", "set_bus_volume_db",
    )
    forbidden = ("ContinueButton", "SaveStatus", "NewStoryConfirm", "ControlsButton")
    missing = [token for token in required_scene if token not in scene]
    missing += [token for token in required_script if token not in script]
    present_forbidden = [token for token in forbidden if token in scene or token in script]
    if missing:
        fail("Title menu polish is incomplete: " + ", ".join(missing))
    elif present_forbidden:
        fail("Removed title controls still present: " + ", ".join(present_forbidden))
    else:
        ok("Title menu is a spoiler-free four-button scene with options, credits, rain and narrator accent")


def validate_ui_scenes() -> None:
    required = {
        "title menu": ROOT / "scenes/ui/title_menu.tscn",
        "pause menu": ROOT / "scenes/ui/pause_menu.tscn",
        "ending menu": ROOT / "scenes/ui/ending_menu.tscn",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    title = required["title menu"].read_text(encoding="utf-8") if required["title menu"].exists() else ""
    pause = required["pause menu"].read_text(encoding="utf-8") if required["pause menu"].exists() else ""
    ending = required["ending menu"].read_text(encoding="utf-8") if required["ending menu"].exists() else ""
    if missing:
        fail("Missing editable UI scenes: " + ", ".join(missing))
    elif not all(token in title for token in ("BeginButton", "OptionsButton", "CreditsButton", "QuitButton")):
        fail("title_menu.tscn is missing primary editable controls")
    elif "ResumeButton" not in pause or "ReplayButton" not in ending:
        fail("pause or ending scene is missing its primary control")
    else:
        ok("Title, pause and ending interfaces are separate editable container-based scenes")


def validate_suspense_and_state_model() -> None:
    title_scene = (ROOT / "scenes/ui/title_menu.tscn").read_text(encoding="utf-8")
    title_text = "\n".join(re.findall(r'^text = "(.*)"$', title_scene, re.MULTILINE)).lower()
    spoilers = [word for word in ("cult", "banana", "potassium", "manhole", "sewer", "ripening", "smoothie") if word in title_text]
    state = (ROOT / "scripts/game_state.gd").read_text(encoding="utf-8")
    game = (ROOT / "scripts/game.gd").read_text(encoding="utf-8")
    story = (ROOT / "scripts/story_text.gd").read_text(encoding="utf-8")
    dialogue = (ROOT / "scripts/dialogue_ui.gd").read_text(encoding="utf-8")
    narrator_png = ROOT / "assets/characters/narrator_detective.png"
    narrator_ase = ROOT / "assets/source/Grian-PickleHarry-Detective.ase"
    errors = []
    if spoilers:
        errors.append("title spoilers: " + ", ".join(spoilers))
    for token in ("SAVE_PATH", "FileAccess", "func save_game", "func load_game", "func has_save"):
        if token in state:
            errors.append("persistent state token remains: " + token)
    for token in ("continue_requested", "_on_continue_game"):
        if token in game or token in (ROOT / "scripts/title_menu.gd").read_text(encoding="utf-8"):
            errors.append("continue flow remains: " + token)
    if not narrator_png.exists() or png_size(narrator_png) != (32, 32):
        errors.append("narrator_detective.png must exist at 32x32")
    if not narrator_ase.exists():
        errors.append("detective Aseprite source is missing")
    if not re.search(r'"narrator"\s*:\s*\{\s*"path"\s*:\s*"res://assets/characters/narrator_detective\.png"', dialogue, re.MULTILINE):
        errors.append("dialogue UI does not register the narrator portrait")
    if story.count('"portrait": "narrator"') < 6:
        errors.append("too few narrator portrait beats")
    if "The temple had been abandoned for years." not in story or "At least, that is what everyone believed." not in story:
        errors.append("approved opening narration is missing")
    if errors:
        fail("Suspense opening/state validation: " + "; ".join(errors))
    else:
        ok("Opening remains suspenseful, detective narration is integrated, and progression is session-only")


def main() -> int:
    run_tool(["gdformat", "--check", "scripts"], "GDScript formatter/parser check")
    run_tool(["gdlint", "scripts"], "GDScript lint check")
    run_python_validator("validate_gdscript_structure.py", "Offline GDScript structural scan")
    validate_export_annotations()
    validate_resource_references()
    validate_images()
    validate_audio()
    validate_aseprite_sources()
    validate_no_legacy_room_images()
    validate_ui_scenes()
    validate_title_menu_polish()
    validate_suspense_and_state_model()
    run_python_validator("validate_tilemaps.py", "TileMap architecture, hidden collision and reachability")
    run_python_validator("validate_scene_runtime.py", "Scene runtime, progression and placement integration")

    report = ["BENEATH THE PEEL - SUSPENSE NARRATOR EDITION VALIDATION", "=" * 48, *CHECKS]
    if ERRORS:
        report += ["", "ERRORS", "-" * 48, *ERRORS]
    report += ["", f"RESULT: {'PASS' if not ERRORS else 'FAIL'} ({len(CHECKS)} checks, {len(ERRORS)} errors)"]
    output = "\n".join(report) + "\n"
    print(output, end="")
    (ROOT / "docs/VALIDATION_REPORT.txt").write_text(output, encoding="utf-8")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
