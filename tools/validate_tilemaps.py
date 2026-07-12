#!/usr/bin/env python3
"""Validate the image-free, editor-painted TileMap room architecture."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from scene_validation import (
    parse_scene,
    reachable_points,
    root_rect,
    root_vector,
    tile_cells,
    footprint_blocked,
    nearest_distance,
    rect_has_reachable_point,
)

ROOT = Path(__file__).resolve().parents[1]
ROOM_DIR = ROOT / "scenes" / "rooms"
CUTSCENE_DIR = ROOT / "scenes" / "cutscenes"
EXPECTED_ROOMS = {
    "temple_exterior", "temple_interior", "street", "sewer_explore",
    "cult_lobby", "cult_hq", "storage", "statue_room", "engine_room",
    "quarters", "chase", "surface_ending",
}
EXPECTED_CUTSCENES = {"fall_shaft", "sewer_ride", "cult_window"}
REQUIRED_LAYERS = ("Ground", "DetailsBelow", "Walls", "DetailsAbove", "CollisionMap")
ERRORS: list[str] = []
PASSES: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def ok(message: str) -> None:
    PASSES.append(message)


def validate_tilesets() -> None:
    world = (ROOT / "assets/tiles/world_tileset.tres").read_text(encoding="utf-8")
    collision = (ROOT / "assets/tiles/collision_tileset.tres").read_text(encoding="utf-8")
    if not world.startswith('[gd_resource type="TileSet"'):
        fail("world_tileset.tres is an untyped GDResource instead of an explicit TileSet")
    if not collision.startswith('[gd_resource type="TileSet"'):
        fail("collision_tileset.tres is an untyped GDResource instead of an explicit TileSet")
    if 'resource_name = "BTP Environment TileSet"' not in world:
        fail("world TileSet has no stable editor-facing resource name")
    if 'resource_name = "BTP Invisible Collision TileSet"' not in collision:
        fail("collision TileSet has no stable editor-facing resource name")
    if 'texture_region_size = Vector2i(16, 16)' not in world or 'tile_size = Vector2i(16, 16)' not in world:
        fail("world_tileset.tres is not configured as a 16x16 atlas")
    if 'physics_layer_0/polygon_0/points' not in collision:
        fail("collision_tileset.tres has no physics polygon")
    if 'physics_layer_0/collision_layer = 1' not in collision:
        fail("collision tiles do not collide on physics layer 1")
    if not ERRORS:
        ok("World and invisible collision resources are explicit, named 16x16 TileSets")


def validate_rooms() -> None:
    paths = sorted(ROOM_DIR.glob("*.tscn"))
    actual = {path.stem for path in paths}
    if actual != EXPECTED_ROOMS:
        fail(f"room scene set mismatch: expected {sorted(EXPECTED_ROOMS)}, got {sorted(actual)}")
        return

    total_tiles = 0
    total_targets = 0
    for path in paths:
        scene = parse_scene(path)
        if "assets/backgrounds/" in scene.text or '[node name="Background"' in scene.text:
            fail(f"{path.name}: playable room still uses a full-room background image")
        if 'script = ExtResource("1_room")' not in scene.text:
            fail(f"{path.name}: root does not use RoomDefinition")

        for layer_name in REQUIRED_LAYERS:
            node = scene.node(f"Tilemaps/{layer_name}")
            if node is None or node.node_type != "TileMapLayer":
                fail(f"{path.name}: missing Tilemaps/{layer_name} TileMapLayer")
                continue
            try:
                cells = tile_cells(node)
                total_tiles += len(cells)
            except Exception as exc:  # noqa: BLE001
                fail(f"{path.name}/{layer_name}: invalid serialized tile data ({exc})")

        collision_node = scene.node("Tilemaps/CollisionMap")
        if collision_node is None:
            continue
        if collision_node.boolean("visible", True):
            fail(f"{path.name}: CollisionMap must be hidden by default")
        if not collision_node.boolean("collision_enabled", False):
            fail(f"{path.name}: CollisionMap physics must remain enabled while hidden")
        collision = set(tile_cells(collision_node))
        if not collision:
            fail(f"{path.name}: CollisionMap has no cells")
            continue

        bounds = root_rect(scene, "player_bounds", (8.0, 8.0, 304.0, 164.0))
        world_size = root_vector(scene, "world_size", (320.0, 180.0))
        if bounds[0] < 0 or bounds[1] < 0 or bounds[0] + bounds[2] > world_size[0] or bounds[1] + bounds[3] > world_size[1]:
            fail(f"{path.name}: player_bounds extends outside world_size")

        spawns = scene.children_of("SpawnPoints")
        default = next((node for node in spawns if node.name == "Default"), None)
        if default is None:
            fail(f"{path.name}: missing SpawnPoints/Default")
            continue
        default_pos = default.vector("position")
        if default_pos is None or footprint_blocked(default_pos, collision, bounds):
            fail(f"{path.name}: default player spawn overlaps collision")
            continue
        visited = reachable_points(default_pos, collision, bounds)
        if not visited:
            fail(f"{path.name}: default spawn has no walkable region")
            continue

        for spawn in spawns:
            pos = spawn.vector("position")
            if pos is None:
                fail(f"{path.name}/{spawn.name}: missing position")
            elif footprint_blocked(pos, collision, bounds):
                fail(f"{path.name}/{spawn.name}: spawn overlaps collision")
            elif nearest_distance(visited, pos) > 5.7:
                fail(f"{path.name}/{spawn.name}: named spawn is disconnected from Default")

        for interaction in scene.children_of("Interactions"):
            pos = interaction.vector("position")
            radius = interaction.number("radius", 18.0)
            if pos is None:
                fail(f"{path.name}/{interaction.name}: interaction has no position")
                continue
            distance = nearest_distance(visited, pos)
            total_targets += 1
            if distance > radius:
                fail(f"{path.name}/{interaction.name}: not approachable (nearest {distance:.1f}px, radius {radius:.1f}px)")

        for trigger in scene.children_of("Triggers"):
            pos = trigger.vector("position")
            size = trigger.vector("size", (16.0, 16.0))
            total_targets += 1
            if pos is None or not rect_has_reachable_point(visited, pos, size):
                fail(f"{path.name}/{trigger.name}: trigger does not intersect reachable floor")

    if not ERRORS:
        ok(f"All {len(paths)} rooms are image-free TileMap scenes ({total_tiles} painted cells)")
        ok(f"All spawns and {total_targets} story targets are collision-reachable")


def validate_cutscenes() -> None:
    paths = sorted(CUTSCENE_DIR.glob("*.tscn"))
    actual = {path.stem for path in paths}
    missing = EXPECTED_CUTSCENES - actual
    if missing:
        fail("missing tile-built cutscenes: " + ", ".join(sorted(missing)))
        return
    for name in EXPECTED_CUTSCENES:
        scene = parse_scene(CUTSCENE_DIR / f"{name}.tscn")
        if "assets/backgrounds/" in scene.text or "Sprite2D" in scene.text:
            fail(f"{name}.tscn: cinematic still relies on a full-scene image")
        layers = [node for node in scene.nodes if node.node_type == "TileMapLayer"]
        if not layers:
            fail(f"{name}.tscn: no TileMapLayer")
        for layer in layers:
            try:
                tile_cells(layer)
            except Exception as exc:  # noqa: BLE001
                fail(f"{name}.tscn/{layer.name}: invalid tile data ({exc})")
    if not any(error.startswith(tuple(EXPECTED_CUTSCENES)) for error in ERRORS):
        ok("Fall, sewer-current and ritual-window cinematics are tile-built scenes")


def validate_runtime_references() -> None:
    game = (ROOT / "scripts/game.gd").read_text(encoding="utf-8")
    db = (ROOT / "scripts/room_database.gd").read_text(encoding="utf-8")
    room_paths = dict(re.findall(r'"([a-z_]+)":\s*"res://scenes/rooms/([a-z_]+)\.tscn"', db))
    if set(room_paths) != EXPECTED_ROOMS or any(key != value for key, value in room_paths.items()):
        fail("RoomDB is not a clean room-id to independent scene registry")

    for room_id, spawn_name in re.findall(r'_change_room\("([a-z_]+)",\s*&"([A-Za-z0-9_]+)"', game):
        scene_path = ROOM_DIR / f"{room_id}.tscn"
        if not scene_path.exists():
            fail(f"runtime transition targets missing room {room_id}")
            continue
        scene = parse_scene(scene_path)
        if scene.node(f"SpawnPoints/{spawn_name}") is None:
            fail(f"runtime transition {room_id}/{spawn_name} targets a missing spawn marker")

    old_images = ("fall_shaft.png", "sewer_ride.png", "cult_window_cutscene.png")
    for name in old_images:
        if name in game:
            fail(f"game.gd still loads old cinematic image {name}")
    if "CollisionShape2D" in db or "Rect2(" in db or '"background"' in db:
        fail("RoomDB still contains layout or collision data instead of only scene paths")
    if "debug_collision" not in game or "set_collision_debug_visible" not in game:
        fail("hidden collision layer has no opt-in debug toggle")
    if not ERRORS:
        ok("Runtime loads independent room scenes and resolves named spawn markers")
        ok("Collision stays hidden by default and is only exposed through the debug toggle")


def main() -> int:
    validate_tilesets()
    validate_rooms()
    validate_cutscenes()
    validate_runtime_references()
    for item in PASSES:
        print("PASS:", item)
    if ERRORS:
        print("FAIL")
        for item in ERRORS:
            print(" -", item)
        return 1
    print(f"RESULT: PASS ({len(PASSES)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
