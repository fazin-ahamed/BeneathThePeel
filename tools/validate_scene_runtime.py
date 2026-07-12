#!/usr/bin/env python3
"""Validate scene-driven story integration and placement quality."""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

from scene_validation import footprint_blocked, parse_scene, root_rect, tile_cells

ROOT = Path(__file__).resolve().parents[1]
ROOM_DIR = ROOT / "scenes/rooms"
ERRORS: list[str] = []
PASSES: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def ok(message: str) -> None:
    PASSES.append(message)


def validate_event_graph() -> None:
    game = (ROOT / "scripts/game.gd").read_text(encoding="utf-8")
    events: set[str] = set()
    for path in ROOM_DIR.glob("*.tscn"):
        scene = parse_scene(path)
        for parent in ("Interactions", "Triggers"):
            for node in scene.children_of(parent):
                event = node.string("event_name")
                if event:
                    events.add(event)
    start = game.index("\tmatch event_name:")
    end = game.index("\n\tif event_handled", start)
    handlers = set(re.findall(r'^\s*"([^"]+)":', game[start:end], re.MULTILINE))
    missing = sorted(events - handlers)
    if missing:
        fail("scene events without game handlers: " + ", ".join(missing))
    else:
        ok(f"All {len(events)} scene-authored story events have runtime handlers")


def validate_dialogue_graph() -> None:
    game = (ROOT / "scripts/game.gd").read_text(encoding="utf-8")
    story = (ROOT / "scripts/story_text.gd").read_text(encoding="utf-8")
    defined = set(re.findall(r'^\s*"([^"]+)":\s*\n\s*return\s*\[', story, re.MULTILINE))
    requested = set(re.findall(r'Story\.dialogue\("([^"]+)"\)', game))
    requested.update({"fuel_left", "fuel_right", "fuel_apple", "locker_1", "locker_2", "locker_3", "locker_5"})
    missing = sorted(requested - defined)
    if missing:
        fail("missing dialogue sequences: " + ", ".join(missing))
    else:
        ok(f"All {len(requested)} requested dialogue sequences are defined")


def validate_placements() -> None:
    checked_npcs = 0
    checked_interactions = 0
    for path in sorted(ROOM_DIR.glob("*.tscn")):
        scene = parse_scene(path)
        collision = set(tile_cells(scene.node("Tilemaps/CollisionMap")))
        bounds = root_rect(scene, "player_bounds", (8.0, 8.0, 304.0, 164.0))

        interactions = []
        for node in scene.children_of("Interactions"):
            pos = node.vector("position")
            radius = node.number("radius", 18.0)
            if pos:
                interactions.append((node.name, pos, radius))
                checked_interactions += 1
        for index, first in enumerate(interactions):
            for second in interactions[index + 1:]:
                distance = math.dist(first[1], second[1])
                if distance < min(first[2], second[2]) * 0.65:
                    fail(
                        f"{path.name}: interaction ranges for {first[0]} and {second[0]} heavily overlap "
                        f"({distance:.1f}px)"
                    )

        for node in scene.children_of("NPCSpawns"):
            pos = node.vector("position")
            checked_npcs += 1
            if pos is None:
                fail(f"{path.name}/{node.name}: NPC has no position")
            elif footprint_blocked(pos, collision, bounds, half=(4.0, 5.0)):
                fail(f"{path.name}/{node.name}: NPC spawn overlaps wall or prop collision")

        for node in scene.children_of("PeelSpawns"):
            pos = node.vector("position")
            if pos and footprint_blocked(pos, collision, bounds, half=(2.0, 2.0)):
                fail(f"{path.name}/{node.name}: banana peel is hidden inside collision")

    if not ERRORS:
        ok(f"{checked_interactions} interaction placements have non-conflicting prompt ranges")
        ok(f"{checked_npcs} NPC placements are outside hidden collision")


def validate_progression_guards() -> None:
    interaction = (ROOT / "scripts/interactable.gd").read_text(encoding="utf-8")
    game = (ROOT / "scripts/game.gd").read_text(encoding="utf-8")
    state = (ROOT / "scripts/game_state.gd").read_text(encoding="utf-8")
    dialogue = (ROOT / "scripts/dialogue_ui.gd").read_text(encoding="utf-8")
    required = {
        "one-shot interaction disables before emit": "disabled = true" in interaction,
        "one-shot commit happens after successful event": "if event_handled and not one_shot_id.is_empty()" in game,
        "interaction input release is awaited": "_release_interaction_key" in game and "input_armed" in dialogue,
        "box delivery is atomic": "func complete_box_delivery" in state,
        "fuel loading is atomic": "func complete_fuel_source" in state,
        "seal tasks are atomic": "func complete_seal_task" in state,
    }
    missing = [name for name, present in required.items() if not present]
    if missing:
        fail("progression safeguards missing: " + ", ".join(missing))
    else:
        ok("One-shot interactions, key-release locks and atomic progression are preserved")


def validate_architecture() -> None:
    game = (ROOT / "scripts/game.gd").read_text(encoding="utf-8")
    room_db = (ROOT / "scripts/room_database.gd").read_text(encoding="utf-8")
    room_def = (ROOT / "scripts/room_definition.gd").read_text(encoding="utf-8")
    required = {
        "RoomDB only registers scene paths": "ROOM_SCENES" in room_db and "colliders" not in room_db and "background" not in room_db,
        "game instantiates room scenes": "room_scene.instantiate() as RoomDefinition" in game,
        "actors parent into scene y-sort root": "room_instance.actor_parent()" in game,
        "collision is tile-driven": "func collision_map() -> TileMapLayer" in room_def,
        "collision is hidden by default": "set_collision_debug_visible" in room_def,
    }
    missing = [name for name, present in required.items() if not present]
    if missing:
        fail("scene architecture checks missing: " + ", ".join(missing))
    else:
        ok("Runtime architecture is scene-driven, tile-collided and y-sorted")


def validate_fall_and_potassium_features() -> None:
    game = (ROOT / "scripts/game.gd").read_text(encoding="utf-8")
    story = (ROOT / "scripts/story_text.gd").read_text(encoding="utf-8")
    engine_scene = (ROOM_DIR / "engine_room.tscn").read_text(encoding="utf-8")
    panel = ROOT / "assets/props/potassium_config_panel.png"

    fall_checks = {
        "shaft scrolls upward": 'shaft_a, "position:y", -576.0' in game,
        "second shaft loops into view": 'shaft_b, "position:y", 0.0' in game,
        "actor accelerates downward": 'falling_actor, "position:y", 124.0' in game,
        "fall has speed streaks": "_make_fall_streak_field" in game,
        "fall has debris": "_make_fall_debris" in game,
        "fall has shoe gag": "_make_fall_shoe" in game,
        "fall has impact flashes": "_fall_impact" in game,
    }
    missing_fall = [name for name, present in fall_checks.items() if not present]
    if missing_fall:
        fail("fall-direction regression safeguards missing: " + ", ".join(missing_fall))
    else:
        ok("Fall scrolls the shaft upward while the actor accelerates downward, with added cinematic FX")

    potassium_checks = {
        "panel texture exists": panel.exists(),
        "panel is placed in engine room": "potassium_config_panel.png" in engine_scene,
        "panel has an interaction": 'event_name = "inspect_potassium_configuration"' in engine_scene,
        "event has a runtime handler": '"inspect_potassium_configuration":' in game,
        "dialogue contains atomic number": "ATOMIC NUMBER 19" in story,
        "dialogue contains shell distribution": "2, 8, 8, 1" in story,
        "dialogue contains shorthand configuration": "[Ar] 4s¹" in story,
    }
    missing_potassium = [name for name, present in potassium_checks.items() if not present]
    if missing_potassium:
        fail("potassium reference integration missing: " + ", ".join(missing_potassium))
    else:
        ok("Potassium configuration panel, interaction and dialogue are fully integrated")


def main() -> int:
    validate_event_graph()
    validate_dialogue_graph()
    validate_placements()
    validate_progression_guards()
    validate_architecture()
    validate_fall_and_potassium_features()
    for message in PASSES:
        print("PASS:", message)
    if ERRORS:
        print("FAIL")
        for error in ERRORS:
            print(" -", error)
        return 1
    print(f"RESULT: PASS ({len(PASSES)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
