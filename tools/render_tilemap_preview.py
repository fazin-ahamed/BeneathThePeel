#!/usr/bin/env python3
"""Render contact sheets from the actual serialized Godot TileMap scenes."""
from __future__ import annotations

import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from scene_validation import parse_scene, root_vector, tile_cells

ROOT = Path(__file__).resolve().parents[1]
ATLAS = Image.open(ROOT / "assets/tiles/btp_environment_tiles.png").convert("RGBA")
TILE = 16
ORDER = [
    "temple_exterior", "temple_interior", "street", "sewer_explore",
    "cult_lobby", "cult_hq", "storage", "statue_room", "engine_room",
    "quarters", "chase", "surface_ending",
]
DISPLAY = {
    "temple_exterior": "TEMPLE APPROACH", "temple_interior": "TEMPLE INTERIOR",
    "street": "RAINY STREET", "sewer_explore": "SEWER EXPLORATION",
    "cult_lobby": "CULT LOBBY", "cult_hq": "CULT HEADQUARTERS",
    "storage": "SACRED STORAGE", "statue_room": "CURVED ONE SHRINE",
    "engine_room": "RIPENING ENGINE", "quarters": "INITIATE QUARTERS",
    "chase": "ESCAPE CORRIDOR", "surface_ending": "SURFACE ENDING",
}
SHEET_BY_KIND = {
    "cultist": "cultist_sheet.png", "guard": "guard_sheet.png",
    "cavendish": "cavendish_sheet.png", "leader": "cult_leader_sheet.png",
}


def ext_resources(text: str) -> dict[str, Path]:
    out = {}
    for resource_type, path, resource_id in re.findall(
        r'\[ext_resource type="([^"]+)" path="([^"]+)" id="([^"]+)"\]', text
    ):
        if resource_type == "Texture2D" and path.startswith("res://"):
            out[resource_id] = ROOT / path.removeprefix("res://")
    return out


def render_room(room_id: str) -> Image.Image:
    scene = parse_scene(ROOT / "scenes/rooms" / f"{room_id}.tscn")
    world = root_vector(scene, "world_size", (320.0, 180.0))
    image = Image.new("RGBA", (int(world[0]), int(world[1])), (7, 6, 14, 255))
    for layer_name in ("Ground", "DetailsBelow", "Walls", "DetailsAbove"):
        for (x, y), (_, ax, ay, _) in tile_cells(scene.node(f"Tilemaps/{layer_name}")).items():
            tile = ATLAS.crop((ax * TILE, ay * TILE, (ax + 1) * TILE, (ay + 1) * TILE))
            image.alpha_composite(tile, (x * TILE, y * TILE))

    resources = ext_resources(scene.text)
    for node in scene.children_of("Actors"):
        texture_value = node.properties.get("texture", "")
        match = re.fullmatch(r'ExtResource\("([^"]+)"\)', texture_value)
        pos = node.vector("position")
        if not match or not pos or match.group(1) not in resources:
            continue
        sprite = Image.open(resources[match.group(1)]).convert("RGBA")
        scale = node.vector("scale", (1.0, 1.0))
        if scale != (1.0, 1.0):
            sprite = sprite.resize((max(1, round(sprite.width * scale[0])), max(1, round(sprite.height * scale[1]))), Image.Resampling.NEAREST)
        image.alpha_composite(sprite, (round(pos[0] - sprite.width / 2), round(pos[1] - sprite.height / 2)))

    # Editor-authored NPC placements, rendered using their unchanged first frames.
    for node in scene.children_of("NPCSpawns"):
        pos = node.vector("position")
        kind = node.string("kind", "cultist")
        sheet_name = SHEET_BY_KIND.get(kind)
        if not pos or not sheet_name:
            continue
        sheet = Image.open(ROOT / "assets/characters" / sheet_name).convert("RGBA")
        frame = sheet.crop((0, 0, 16, 16))
        image.alpha_composite(frame, (round(pos[0] - 8), round(pos[1] - 8)))

    default = scene.node("SpawnPoints/Default")
    if default and default.vector("position"):
        pos = default.vector("position")
        player = Image.open(ROOT / "assets/characters/player_sheet.png").convert("RGBA").crop((0, 0, 16, 16))
        image.alpha_composite(player, (round(pos[0] - 8), round(pos[1] - 8)))
    return image.convert("RGB")


def make_contact_sheet() -> None:
    canvas = Image.new("RGB", (1280, 900), (9, 8, 18))
    draw = ImageDraw.Draw(canvas)
    draw.text((40, 24), "BENEATH THE PEEL", fill=(246, 222, 173), font=ImageFont.load_default())
    draw.text((40, 42), "GODOT TILEMAP STORY EDITION — 12 INDEPENDENT ROOMS", fill=(183, 141, 60), font=ImageFont.load_default())
    card_w, card_h = 292, 246
    start_x, start_y = 40, 70
    for index, room_id in enumerate(ORDER):
        col, row = index % 4, index // 4
        x, y = start_x + col * 308, start_y + row * 270
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=8, fill=(20, 17, 31), outline=(73, 59, 84), width=2)
        room = render_room(room_id)
        max_w, max_h = 272, 205
        scale = min(max_w / room.width, max_h / room.height)
        resized = room.resize((max(1, int(room.width * scale)), max(1, int(room.height * scale))), Image.Resampling.NEAREST)
        px = x + (card_w - resized.width) // 2
        py = y + 25 + (max_h - resized.height) // 2
        canvas.paste(resized, (px, py))
        draw.text((x + 10, y + 8), DISPLAY[room_id], fill=(245, 205, 78), font=ImageFont.load_default())
        draw.text((x + 10, y + card_h - 14), f"{room.width}×{room.height}px • 16×16 tiles", fill=(135, 129, 147), font=ImageFont.load_default())
    out = ROOT / "docs/TILEMAP_ROOM_OVERVIEW.png"
    canvas.save(out)
    canvas.save(ROOT / "PREVIEW_TILEMAP_EDITION.png")
    print(out)


if __name__ == "__main__":
    make_contact_sheet()
