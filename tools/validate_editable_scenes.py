#!/usr/bin/env python3
"""Focused check that rooms are visually editable without collision clutter."""
from __future__ import annotations

import sys
from pathlib import Path

from scene_validation import parse_scene, tile_cells

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []
rooms = sorted((ROOT / "scenes/rooms").glob("*.tscn"))
for path in rooms:
    scene = parse_scene(path)
    if "assets/backgrounds/" in scene.text:
        errors.append(f"{path.name}: still uses a room image")
    for layer in ("Ground", "DetailsBelow", "Walls", "DetailsAbove"):
        node = scene.node(f"Tilemaps/{layer}")
        if node is None or node.node_type != "TileMapLayer":
            errors.append(f"{path.name}: missing editable {layer} TileMapLayer")
    collision = scene.node("Tilemaps/CollisionMap")
    if collision is None:
        errors.append(f"{path.name}: missing hidden CollisionMap")
    else:
        if collision.boolean("visible", True):
            errors.append(f"{path.name}: collision is visible in the editor by default")
        if not collision.boolean("collision_enabled", False):
            errors.append(f"{path.name}: hidden collision physics disabled")
        if not tile_cells(collision):
            errors.append(f"{path.name}: empty collision map")
    if scene.node("Actors") is None:
        errors.append(f"{path.name}: missing y-sorted Actors root")
    if scene.node("SpawnPoints/Default") is None:
        errors.append(f"{path.name}: missing default spawn marker")

if errors:
    print("FAIL")
    print("\n".join(errors))
    sys.exit(1)
print(f"PASS: {len(rooms)} independent tile-painted rooms; collision hidden and physics-enabled")
