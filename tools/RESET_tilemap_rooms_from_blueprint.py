#!/usr/bin/env python3
"""DESTRUCTIVE RESET: rebuild every TileMap room from the Python blueprint.

Do not run this after making manual edits in Godot unless you intend to discard
those edits. The shipped .tscn rooms are the primary editable source of truth.
Playable rooms do not use full-screen background images.
"""
from __future__ import annotations

import base64
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Set, Tuple

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TILE = 16
ATLAS_COLS = 16
ATLAS_ROWS = 6

Cell = Tuple[int, int]
Atlas = Tuple[int, int]

# ---------------------------------------------------------------------------
# Pixel-art tile atlas
# ---------------------------------------------------------------------------

TILES: Dict[str, Atlas] = {
    # Ground tiles
    "temple_floor": (0, 0),
    "temple_floor_alt": (1, 0),
    "stone_floor": (2, 0),
    "stone_floor_alt": (3, 0),
    "cult_floor": (4, 0),
    "cult_floor_alt": (5, 0),
    "street_floor": (6, 0),
    "street_floor_alt": (7, 0),
    "sewer_walk": (8, 0),
    "sewer_walk_alt": (9, 0),
    "sewer_water": (10, 0),
    "sewer_water_alt": (11, 0),
    "metal_floor": (12, 0),
    "metal_floor_alt": (13, 0),
    "ritual_carpet": (14, 0),
    "ritual_carpet_border": (15, 0),
    # Walls
    "temple_wall": (0, 1),
    "temple_wall_crack": (1, 1),
    "temple_wall_top": (2, 1),
    "temple_wall_bottom": (3, 1),
    "cult_wall": (4, 1),
    "cult_wall_crack": (5, 1),
    "cult_wall_top": (6, 1),
    "cult_wall_bottom": (7, 1),
    "sewer_wall": (8, 1),
    "sewer_wall_moss": (9, 1),
    "sewer_wall_top": (10, 1),
    "sewer_wall_bottom": (11, 1),
    "metal_wall": (12, 1),
    "metal_wall_panel": (13, 1),
    "brick_wall": (14, 1),
    "brick_wall_crack": (15, 1),
    # Architecture
    "temple_door": (0, 2),
    "cult_door": (1, 2),
    "metal_door": (2, 2),
    "arch": (3, 2),
    "pillar": (4, 2),
    "pew_mid": (5, 2),
    "pew_left": (6, 2),
    "pew_right": (7, 2),
    "altar_base": (8, 2),
    "altar_top": (9, 2),
    "stairs_up": (10, 2),
    "stairs_down": (11, 2),
    "pipe_h": (12, 2),
    "pipe_v": (13, 2),
    "pipe_corner": (14, 2),
    "grate": (15, 2),
    # Props and decals
    "candle": (0, 3),
    "banana_banner": (1, 3),
    "plain_banner": (2, 3),
    "crate": (3, 3),
    "shelf": (4, 3),
    "locker": (5, 3),
    "desk": (6, 3),
    "chair": (7, 3),
    "rug_edge": (8, 3),
    "window": (9, 3),
    "lamp": (10, 3),
    "puddle": (11, 3),
    "manhole": (12, 3),
    "yellow_mark": (13, 3),
    "purple_mark": (14, 3),
    "floor_crack": (15, 3),
    # Industrial / scenery
    "roof": (0, 4),
    "skyline": (1, 4),
    "railing": (2, 4),
    "water_edge_top": (3, 4),
    "water_edge_bottom": (4, 4),
    "bridge": (5, 4),
    "fence": (6, 4),
    "vent": (7, 4),
    "engine_base": (8, 4),
    "engine_pipe": (9, 4),
    "engine_core": (10, 4),
    "box_stack": (11, 4),
    "shrine_platform": (12, 4),
    "ritual_circle": (13, 4),
    "banana_symbol": (14, 4),
    "sealed_exit": (15, 4),
    # Exterior / misc
    "grass_dark": (0, 5),
    "path": (1, 5),
    "building_face": (2, 5),
    "building_window": (3, 5),
    "city_wall": (4, 5),
    "city_window": (5, 5),
    "temple_steps": (6, 5),
    "curb": (7, 5),
    "sewer_window": (8, 5),
    "warning_stripe": (9, 5),
    "blood_mark": (10, 5),
    "banana_tile": (11, 5),
    "shadow_tile": (12, 5),
    "light_tile": (13, 5),
    "void": (14, 5),
    "highlight": (15, 5),
}


def _px(draw: ImageDraw.ImageDraw, xy, fill):
    draw.point(xy, fill=fill)


def _tile_canvas() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _pattern_floor(base, line, speck, seed: int = 0) -> Image.Image:
    im, d = _tile_canvas()
    d.rectangle((0, 0, 15, 15), fill=base)
    d.line((0, 7, 15, 7), fill=line)
    d.line((7, 0, 7, 7), fill=line)
    d.line((3, 8, 3, 15), fill=line)
    pts = [(2 + seed % 3, 3), (11, 11 + seed % 2), (14, 5)]
    for p in pts:
        _px(d, p, speck)
    return im


def _wall(base, mortar, top, crack: bool = False) -> Image.Image:
    im, d = _tile_canvas()
    d.rectangle((0, 0, 15, 15), fill=base)
    d.rectangle((0, 0, 15, 2), fill=top)
    for y in (5, 10):
        d.line((0, y, 15, y), fill=mortar)
    d.line((7, 3, 7, 5), fill=mortar)
    d.line((3, 6, 3, 10), fill=mortar)
    d.line((11, 11, 11, 15), fill=mortar)
    if crack:
        d.line((10, 4, 8, 7, 10, 9, 7, 13), fill=(20, 16, 28, 255))
    return im


def _door(base, trim, glow) -> Image.Image:
    im, d = _tile_canvas()
    d.rectangle((2, 0, 13, 15), fill=trim)
    d.rectangle((4, 2, 11, 15), fill=base)
    d.rectangle((5, 3, 10, 14), outline=(30, 18, 26, 255))
    d.rectangle((9, 8, 10, 9), fill=glow)
    return im


def _simple_prop(kind: str) -> Image.Image:
    im, d = _tile_canvas()
    transparent = (0, 0, 0, 0)
    if kind == "pillar":
        d.rectangle((5, 1, 10, 14), fill=(105, 91, 109, 255))
        d.rectangle((3, 0, 12, 2), fill=(158, 142, 157, 255))
        d.rectangle((3, 13, 12, 15), fill=(64, 52, 73, 255))
    elif kind.startswith("pew"):
        d.rectangle((0, 5, 15, 11), fill=(83, 45, 38, 255))
        d.rectangle((0, 4, 15, 6), fill=(132, 78, 47, 255))
        d.rectangle((2, 11, 4, 15), fill=(51, 31, 33, 255))
        d.rectangle((11, 11, 13, 15), fill=(51, 31, 33, 255))
        if kind == "pew_left":
            d.rectangle((0, 3, 2, 13), fill=(155, 93, 50, 255))
        if kind == "pew_right":
            d.rectangle((13, 3, 15, 13), fill=(155, 93, 50, 255))
    elif kind == "altar_base":
        d.rectangle((1, 7, 14, 14), fill=(91, 50, 62, 255))
        d.rectangle((0, 6, 15, 8), fill=(150, 87, 70, 255))
        d.rectangle((3, 9, 12, 12), fill=(62, 35, 52, 255))
    elif kind == "altar_top":
        d.rectangle((4, 6, 11, 14), fill=(70, 39, 51, 255))
        d.polygon([(8, 1), (13, 6), (8, 9), (3, 6)], fill=(241, 190, 49, 255))
        d.line((5, 6, 10, 4), fill=(255, 229, 111, 255), width=1)
    elif kind.startswith("stairs"):
        base = (61, 57, 73, 255)
        hi = (112, 106, 126, 255)
        for i in range(4):
            y = 3 + i * 3
            d.rectangle((2 + i, y, 13 - i, y + 1), fill=hi)
            d.rectangle((2 + i, y + 2, 13 - i, y + 2), fill=base)
        if kind == "stairs_down":
            im = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    elif kind == "pipe_h":
        d.rectangle((0, 5, 15, 10), fill=(61, 76, 79, 255))
        d.line((0, 5, 15, 5), fill=(126, 145, 138, 255))
        d.rectangle((3, 4, 5, 11), fill=(40, 50, 56, 255))
        d.rectangle((11, 4, 13, 11), fill=(40, 50, 56, 255))
    elif kind == "pipe_v":
        d.rectangle((5, 0, 10, 15), fill=(61, 76, 79, 255))
        d.line((5, 0, 5, 15), fill=(126, 145, 138, 255))
        d.rectangle((4, 3, 11, 5), fill=(40, 50, 56, 255))
        d.rectangle((4, 11, 11, 13), fill=(40, 50, 56, 255))
    elif kind == "pipe_corner":
        d.rectangle((5, 5, 15, 10), fill=(61, 76, 79, 255))
        d.rectangle((5, 5, 10, 15), fill=(61, 76, 79, 255))
        d.arc((4, 4, 15, 15), 180, 270, fill=(126, 145, 138, 255), width=1)
    elif kind == "grate":
        d.rectangle((2, 2, 13, 13), fill=(35, 38, 48, 255), outline=(95, 101, 111, 255))
        for x in range(4, 13, 3):
            d.line((x, 3, x, 12), fill=(114, 119, 126, 255))
    elif kind == "candle":
        d.rectangle((7, 6, 9, 14), fill=(223, 194, 132, 255))
        d.polygon([(8, 1), (11, 5), (8, 7), (5, 5)], fill=(255, 180, 44, 255))
        _px(d, (8, 3), (255, 245, 155, 255))
    elif kind in ("banana_banner", "plain_banner"):
        d.rectangle((2, 0, 13, 15), fill=(76, 24, 58, 255))
        d.rectangle((2, 0, 13, 2), fill=(143, 78, 72, 255))
        if kind == "banana_banner":
            d.arc((4, 4, 11, 12), 250, 80, fill=(255, 210, 51, 255), width=2)
    elif kind == "crate":
        d.rectangle((1, 1, 14, 14), fill=(100, 58, 39, 255), outline=(47, 30, 34, 255))
        d.line((2, 2, 13, 13), fill=(157, 93, 51, 255))
        d.line((13, 2, 2, 13), fill=(157, 93, 51, 255))
    elif kind == "shelf":
        d.rectangle((1, 0, 14, 15), fill=(54, 33, 36, 255))
        for y in (3, 8, 13):
            d.rectangle((1, y, 14, y + 1), fill=(145, 82, 48, 255))
        d.rectangle((3, 1, 5, 3), fill=(228, 169, 46, 255))
        d.rectangle((9, 5, 12, 8), fill=(86, 34, 50, 255))
    elif kind == "locker":
        d.rectangle((2, 0, 13, 15), fill=(54, 61, 72, 255), outline=(118, 125, 133, 255))
        d.line((4, 4, 11, 4), fill=(26, 29, 38, 255))
        d.rectangle((10, 8, 11, 9), fill=(200, 157, 56, 255))
    elif kind == "desk":
        d.rectangle((1, 4, 14, 11), fill=(98, 54, 42, 255))
        d.rectangle((0, 3, 15, 5), fill=(153, 88, 50, 255))
        d.rectangle((2, 11, 4, 15), fill=(50, 31, 34, 255))
        d.rectangle((11, 11, 13, 15), fill=(50, 31, 34, 255))
    elif kind == "chair":
        d.rectangle((4, 4, 11, 10), fill=(106, 60, 42, 255))
        d.rectangle((4, 1, 11, 5), fill=(147, 84, 46, 255))
        d.line((5, 10, 4, 15), fill=(50, 30, 33, 255), width=2)
        d.line((10, 10, 11, 15), fill=(50, 30, 33, 255), width=2)
    elif kind == "window":
        d.rectangle((2, 1, 13, 14), fill=(31, 27, 46, 255), outline=(97, 80, 100, 255))
        d.line((7, 2, 7, 13), fill=(153, 129, 129, 255))
        d.line((3, 7, 12, 7), fill=(153, 129, 129, 255))
        d.rectangle((4, 3, 6, 6), fill=(103, 132, 142, 255))
    elif kind == "lamp":
        d.rectangle((7, 7, 8, 15), fill=(70, 63, 72, 255))
        d.rectangle((4, 3, 11, 8), fill=(244, 196, 62, 255))
        d.rectangle((5, 4, 10, 7), fill=(255, 235, 139, 255))
    elif kind == "puddle":
        d.ellipse((1, 5, 14, 12), fill=(40, 83, 94, 200), outline=(80, 130, 139, 255))
        d.line((4, 8, 9, 7), fill=(142, 185, 184, 255))
    elif kind == "manhole":
        d.ellipse((2, 2, 13, 13), fill=(41, 44, 50, 255), outline=(111, 117, 121, 255))
        for x in range(5, 12, 3):
            d.line((x, 4, x, 11), fill=(78, 83, 89, 255))
    elif kind.endswith("_mark"):
        color = (246, 200, 44, 255) if kind == "yellow_mark" else (178, 75, 196, 255)
        d.rectangle((2, 2, 13, 13), outline=color, width=2)
        d.line((4, 8, 7, 11, 12, 4), fill=color, width=1)
    elif kind == "floor_crack":
        d.line((3, 2, 7, 6, 5, 9, 11, 14), fill=(40, 28, 39, 255), width=1)
    elif kind == "roof":
        d.polygon([(0, 13), (8, 1), (15, 13)], fill=(53, 43, 66, 255))
        d.line((0, 13, 8, 1, 15, 13), fill=(122, 102, 123, 255))
    elif kind == "skyline":
        d.rectangle((0, 10, 15, 15), fill=(18, 19, 31, 255))
        d.rectangle((2, 6, 6, 15), fill=(25, 27, 42, 255))
        d.rectangle((9, 3, 14, 15), fill=(30, 31, 47, 255))
        _px(d, (4, 8), (244, 195, 52, 255)); _px(d, (11, 6), (244, 195, 52, 255))
    elif kind == "railing":
        d.line((0, 5, 15, 5), fill=(112, 102, 91, 255), width=2)
        d.line((0, 12, 15, 12), fill=(65, 58, 59, 255), width=2)
        for x in (2, 7, 12): d.line((x, 3, x, 15), fill=(91, 82, 77, 255), width=1)
    elif kind.startswith("water_edge"):
        d.rectangle((0, 0, 15, 15), fill=(19, 68, 81, 255))
        y = 2 if kind.endswith("top") else 13
        d.line((0, y, 15, y), fill=(73, 139, 145, 255))
    elif kind == "bridge":
        d.rectangle((0, 2, 15, 13), fill=(92, 58, 43, 255))
        for y in (3, 7, 11): d.line((0, y, 15, y), fill=(151, 94, 52, 255))
    elif kind == "fence":
        for x in (2, 7, 12): d.rectangle((x, 0, x + 1, 15), fill=(92, 85, 84, 255))
        d.rectangle((0, 5, 15, 6), fill=(122, 111, 103, 255))
    elif kind == "vent":
        d.rectangle((2, 2, 13, 13), fill=(38, 43, 51, 255), outline=(101, 108, 115, 255))
        for y in range(4, 13, 3): d.line((4, y, 11, y), fill=(129, 136, 141, 255))
    elif kind.startswith("engine"):
        d.rectangle((1, 1, 14, 14), fill=(40, 44, 54, 255), outline=(110, 117, 122, 255))
        if kind == "engine_base":
            d.rectangle((3, 9, 12, 13), fill=(88, 55, 58, 255))
        elif kind == "engine_pipe":
            d.line((3, 13, 3, 3, 12, 3, 12, 13), fill=(112, 128, 126, 255), width=2)
        else:
            d.ellipse((4, 4, 11, 11), fill=(123, 33, 59, 255), outline=(245, 187, 45, 255))
            d.ellipse((6, 6, 9, 9), fill=(255, 232, 127, 255))
    elif kind == "box_stack":
        for ox, oy in ((1, 7), (7, 7), (4, 1)):
            d.rectangle((ox, oy, ox + 7, oy + 7), fill=(103, 58, 39, 255), outline=(46, 29, 33, 255))
            d.line((ox + 1, oy + 1, ox + 6, oy + 6), fill=(158, 92, 50, 255))
    elif kind == "shrine_platform":
        d.ellipse((0, 7, 15, 15), fill=(89, 40, 66, 255), outline=(175, 76, 139, 255))
        d.rectangle((3, 10, 12, 15), fill=(68, 34, 55, 255))
    elif kind == "ritual_circle":
        d.ellipse((1, 1, 14, 14), outline=(155, 63, 143, 255), width=2)
        d.line((8, 2, 12, 12, 3, 6, 13, 6, 4, 12, 8, 2), fill=(111, 42, 94, 255))
    elif kind == "banana_symbol":
        d.arc((3, 2, 12, 13), 245, 75, fill=(255, 211, 49, 255), width=3)
        d.point((10, 2), fill=(93, 64, 29, 255))
    elif kind == "sealed_exit":
        d.rectangle((2, 0, 13, 15), fill=(48, 30, 42, 255), outline=(160, 78, 117, 255))
        d.ellipse((5, 5, 10, 10), fill=(245, 194, 41, 255))
        d.line((7, 6, 8, 9), fill=(99, 46, 41, 255))
    elif kind == "grass_dark":
        d.rectangle((0, 0, 15, 15), fill=(25, 43, 40, 255))
        for x, y in ((2, 4), (8, 12), (13, 5)):
            d.line((x, y, x + 1, y - 2), fill=(48, 72, 55, 255))
    elif kind == "path":
        d.rectangle((0, 0, 15, 15), fill=(78, 70, 79, 255))
        d.line((0, 5, 15, 5), fill=(55, 50, 62, 255))
        d.line((5, 0, 5, 5), fill=(55, 50, 62, 255))
        d.line((10, 6, 10, 15), fill=(55, 50, 62, 255))
    elif kind == "building_face":
        d.rectangle((0, 0, 15, 15), fill=(54, 48, 64, 255))
        d.rectangle((0, 0, 15, 2), fill=(91, 80, 96, 255))
        d.line((0, 8, 15, 8), fill=(38, 34, 48, 255))
    elif kind == "building_window":
        d.rectangle((0, 0, 15, 15), fill=(54, 48, 64, 255))
        d.rectangle((4, 3, 11, 12), fill=(31, 35, 49, 255), outline=(124, 105, 113, 255))
        d.rectangle((5, 4, 10, 11), fill=(102, 117, 124, 255))
        d.line((7, 4, 7, 11), fill=(219, 173, 61, 255))
    elif kind == "city_wall":
        d.rectangle((0, 0, 15, 15), fill=(34, 37, 51, 255))
        d.line((0, 7, 15, 7), fill=(21, 23, 35, 255))
        d.line((5, 0, 5, 7), fill=(21, 23, 35, 255))
    elif kind == "city_window":
        d.rectangle((0, 0, 15, 15), fill=(26, 29, 44, 255))
        d.rectangle((5, 4, 10, 10), fill=(242, 197, 53, 255))
        d.rectangle((6, 5, 9, 9), fill=(255, 232, 138, 255))
    elif kind == "temple_steps":
        for i in range(4):
            d.rectangle((i, 3 + i * 3, 15 - i, 5 + i * 3), fill=(92 + i * 8, 84 + i * 8, 97 + i * 8, 255))
    elif kind == "curb":
        d.rectangle((0, 0, 15, 5), fill=(104, 102, 108, 255))
        d.rectangle((0, 6, 15, 15), fill=(55, 57, 67, 255))
    elif kind == "sewer_window":
        d.rectangle((1, 1, 14, 14), fill=(18, 28, 35, 255), outline=(83, 104, 107, 255))
        for x in (4, 8, 12): d.line((x, 2, x, 13), fill=(60, 78, 83, 255))
    elif kind == "warning_stripe":
        d.rectangle((0, 0, 15, 15), fill=(34, 37, 45, 255))
        for x in range(-8, 20, 8): d.line((x, 15, x + 8, 7), fill=(221, 163, 39, 255), width=3)
    elif kind == "blood_mark":
        d.rectangle((0, 0, 15, 15), fill=(62, 47, 57, 255))
        d.ellipse((5, 5, 10, 11), fill=(113, 31, 51, 255))
        d.line((7, 10, 6, 15), fill=(113, 31, 51, 255))
    elif kind == "banana_tile":
        d.rectangle((0, 0, 15, 15), fill=(67, 39, 55, 255))
        d.arc((3, 2, 12, 13), 245, 75, fill=(255, 211, 49, 255), width=3)
    elif kind == "shadow_tile":
        d.rectangle((0, 0, 15, 15), fill=(15, 12, 24, 255))
    elif kind == "light_tile":
        d.rectangle((0, 0, 15, 15), fill=(92, 70, 48, 255))
        d.ellipse((3, 3, 12, 12), fill=(255, 224, 122, 255))
    elif kind == "void":
        d.rectangle((0, 0, 15, 15), fill=(12, 10, 20, 255))
    elif kind == "highlight":
        d.rectangle((0, 0, 15, 15), fill=(139, 66, 113, 255))
        d.rectangle((2, 2, 13, 13), outline=(245, 194, 58, 255))
    return im


def build_atlas() -> None:
    atlas = Image.new("RGBA", (ATLAS_COLS * TILE, ATLAS_ROWS * TILE), (0, 0, 0, 0))
    palettes = {
        "temple_floor": ((76, 65, 78, 255), (54, 46, 61, 255), (125, 106, 111, 255)),
        "temple_floor_alt": ((82, 70, 84, 255), (58, 50, 65, 255), (147, 119, 112, 255)),
        "stone_floor": ((53, 54, 67, 255), (36, 37, 49, 255), (93, 96, 108, 255)),
        "stone_floor_alt": ((59, 60, 72, 255), (39, 40, 52, 255), (107, 109, 119, 255)),
        "cult_floor": ((58, 39, 56, 255), (39, 27, 43, 255), (116, 67, 91, 255)),
        "cult_floor_alt": ((64, 43, 61, 255), (43, 29, 47, 255), (132, 75, 98, 255)),
        "street_floor": ((48, 53, 65, 255), (31, 35, 47, 255), (93, 100, 110, 255)),
        "street_floor_alt": ((54, 59, 70, 255), (35, 39, 51, 255), (104, 111, 120, 255)),
        "sewer_walk": ((43, 57, 62, 255), (29, 41, 46, 255), (74, 95, 96, 255)),
        "sewer_walk_alt": ((47, 62, 67, 255), (31, 44, 49, 255), (82, 105, 104, 255)),
        "metal_floor": ((49, 53, 62, 255), (29, 32, 40, 255), (96, 103, 110, 255)),
        "metal_floor_alt": ((55, 59, 68, 255), (34, 37, 46, 255), (112, 118, 124, 255)),
    }
    for name, coord in TILES.items():
        if name in palettes:
            base, line, speck = palettes[name]
            tile = _pattern_floor(base, line, speck, coord[0] + coord[1])
        elif name == "sewer_water" or name == "sewer_water_alt":
            tile, d = _tile_canvas()
            base = (16, 69, 82, 255) if name == "sewer_water" else (18, 76, 88, 255)
            d.rectangle((0, 0, 15, 15), fill=base)
            for y in (3, 9):
                d.line((0, y, 5, y, 8, y - 1, 15, y - 1), fill=(49, 122, 132, 255))
            _px(d, (11, 13), (95, 157, 158, 255))
        elif name == "ritual_carpet":
            tile, d = _tile_canvas(); d.rectangle((0, 0, 15, 15), fill=(77, 20, 57, 255)); d.rectangle((2, 2, 13, 13), outline=(172, 71, 113, 255)); d.point((8, 8), fill=(245, 196, 45, 255))
        elif name == "ritual_carpet_border":
            tile, d = _tile_canvas(); d.rectangle((0, 0, 15, 15), fill=(49, 26, 45, 255)); d.line((0, 2, 15, 2), fill=(194, 90, 116, 255)); d.line((0, 13, 15, 13), fill=(194, 90, 116, 255))
        elif name.endswith("wall") or name.endswith("wall_crack"):
            if name.startswith("temple"):
                tile = _wall((67, 51, 67, 255), (39, 30, 45, 255), (125, 96, 100, 255), name.endswith("crack"))
            elif name.startswith("cult"):
                tile = _wall((61, 39, 55, 255), (35, 24, 40, 255), (112, 61, 85, 255), name.endswith("crack"))
            elif name.startswith("sewer"):
                tile = _wall((39, 52, 56, 255), (24, 35, 39, 255), (73, 92, 91, 255), name.endswith("moss"))
                if name.endswith("moss"):
                    _, d = tile, ImageDraw.Draw(tile); d.line((2, 2, 4, 5, 4, 9), fill=(45, 89, 66, 255))
            elif name.startswith("metal"):
                tile = _wall((47, 50, 59, 255), (29, 31, 39, 255), (99, 104, 109, 255), name.endswith("panel"))
            else:
                tile = _wall((57, 38, 51, 255), (34, 25, 39, 255), (99, 64, 77, 255), name.endswith("crack"))
        elif name.endswith("wall_top"):
            base = (72, 57, 73, 255) if name.startswith("temple") else (61, 40, 57, 255) if name.startswith("cult") else (41, 55, 59, 255)
            tile, d = _tile_canvas(); d.rectangle((0, 0, 15, 15), fill=base); d.rectangle((0, 0, 15, 4), fill=(128, 103, 111, 255)); d.line((0, 5, 15, 5), fill=(33, 27, 39, 255))
        elif name.endswith("wall_bottom"):
            base = (72, 57, 73, 255) if name.startswith("temple") else (61, 40, 57, 255) if name.startswith("cult") else (41, 55, 59, 255)
            tile, d = _tile_canvas(); d.rectangle((0, 0, 15, 15), fill=base); d.rectangle((0, 12, 15, 15), fill=(31, 26, 39, 255)); d.line((0, 11, 15, 11), fill=(117, 89, 98, 255))
        elif name == "temple_door": tile = _door((75, 36, 37, 255), (121, 80, 64, 255), (238, 190, 56, 255))
        elif name == "cult_door": tile = _door((55, 26, 45, 255), (124, 60, 91, 255), (246, 194, 45, 255))
        elif name == "metal_door": tile = _door((39, 44, 53, 255), (99, 109, 113, 255), (92, 217, 186, 255))
        elif name == "arch":
            tile, d = _tile_canvas(); d.arc((0, 0, 15, 18), 180, 360, fill=(118, 96, 104, 255), width=3); d.rectangle((0, 8, 2, 15), fill=(76, 59, 72, 255)); d.rectangle((13, 8, 15, 15), fill=(76, 59, 72, 255))
        else:
            tile = _simple_prop(name)
        atlas.alpha_composite(tile, (coord[0] * TILE, coord[1] * TILE))

    out = ROOT / "assets" / "tiles" / "btp_environment_tiles.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(out)

    collision = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(collision)
    d.rectangle((0, 0, 15, 15), fill=(255, 0, 180, 72), outline=(255, 80, 220, 220))
    d.line((1, 1, 14, 14), fill=(255, 255, 255, 160))
    d.line((14, 1, 1, 14), fill=(255, 255, 255, 160))
    collision.save(ROOT / "assets" / "tiles" / "collision_tile.png")


def build_tilesets() -> None:
    lines = [
        "[gd_resource type=\"TileSet\" load_steps=3 format=3]",
        "",
        '[ext_resource type="Texture2D" path="res://assets/tiles/btp_environment_tiles.png" id="1_tex"]',
        "",
        '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_btp"]',
        'texture = ExtResource("1_tex")',
        "texture_region_size = Vector2i(16, 16)",
    ]
    for y in range(ATLAS_ROWS):
        for x in range(ATLAS_COLS):
            lines.append(f"{x}:{y}/0 = 0")
    lines += [
        "",
        "[resource]",
        'resource_name = "BTP Environment TileSet"',
        "tile_size = Vector2i(16, 16)",
        'sources/0 = SubResource("TileSetAtlasSource_btp")',
        "",
    ]
    (ROOT / "assets" / "tiles" / "world_tileset.tres").write_text("\n".join(lines), encoding="utf-8")

    collision = """[gd_resource type="TileSet" load_steps=3 format=3]

[ext_resource type="Texture2D" path="res://assets/tiles/collision_tile.png" id="1_tex"]

[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_collision"]
texture = ExtResource("1_tex")
texture_region_size = Vector2i(16, 16)
0:0/0 = 0
0:0/0/physics_layer_0/polygon_0/points = PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)

[resource]
resource_name = "BTP Invisible Collision TileSet"
tile_size = Vector2i(16, 16)
physics_layer_0/collision_layer = 1
physics_layer_0/collision_mask = 1
sources/0 = SubResource("TileSetAtlasSource_collision")
"""
    (ROOT / "assets" / "tiles" / "collision_tileset.tres").write_text(collision, encoding="utf-8")


# ---------------------------------------------------------------------------
# Room data and TileMap serialization
# ---------------------------------------------------------------------------


def encode_cells(cells: Mapping[Cell, Atlas], source_id: int = 0) -> str:
    payload = bytearray(b"\x00\x00")
    for (x, y), (ax, ay) in sorted(cells.items(), key=lambda item: (item[0][1], item[0][0])):
        payload.extend(struct.pack("<hhhhhh", x, y, source_id, ax, ay, 0))
    return base64.b64encode(bytes(payload)).decode("ascii")


def fill_rect(layer: MutableMapping[Cell, Atlas], x0: int, y0: int, x1: int, y1: int, tile: str, alt: str | None = None) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            use = alt if alt is not None and (x + y) % 5 == 0 else tile
            layer[(x, y)] = TILES[use]


def line_h(layer: MutableMapping[Cell, Atlas], y: int, x0: int, x1: int, tile: str) -> None:
    for x in range(x0, x1 + 1):
        layer[(x, y)] = TILES[tile]


def line_v(layer: MutableMapping[Cell, Atlas], x: int, y0: int, y1: int, tile: str) -> None:
    for y in range(y0, y1 + 1):
        layer[(x, y)] = TILES[tile]


def rect_cells(x0: int, y0: int, x1: int, y1: int) -> Set[Cell]:
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def border_cells(w: int, h: int, openings: Iterable[Cell] = ()) -> Set[Cell]:
    out = {(x, 0) for x in range(w)} | {(x, h - 1) for x in range(w)}
    out |= {(0, y) for y in range(h)} | {(w - 1, y) for y in range(h)}
    out -= set(openings)
    return out


def put(layer: MutableMapping[Cell, Atlas], cells: Iterable[Cell], tile: str) -> None:
    for cell in cells:
        layer[cell] = TILES[tile]


def c(x: float, y: float) -> Tuple[float, float]:
    return ((x + 0.5) * TILE, (y + 0.5) * TILE)


@dataclass
class Interaction:
    name: str
    event: str
    prompt: str
    pos: Tuple[float, float]
    radius: float = 18.0
    one_shot: bool = False


@dataclass
class NPC:
    name: str
    kind: str
    pos: Tuple[float, float]
    facing: int = 0
    animated: bool = True


@dataclass
class Trigger:
    name: str
    event: str
    pos: Tuple[float, float]
    size: Tuple[float, float]
    one_shot: bool = True


@dataclass
class GuardSpawn:
    name: str
    pos: Tuple[float, float]
    speed: float = 44.0


@dataclass
class Prop:
    name: str
    texture: str
    pos: Tuple[float, float]
    scale: Tuple[float, float] = (1.0, 1.0)
    z_index: int = 0


@dataclass
class RoomSpec:
    room_id: str
    title: str
    w: int
    h: int
    floor: str
    floor_alt: str
    wall: str
    wall_top: str
    wall_bottom: str
    music: str
    music_volume: float
    ambient: str = ""
    ambient_volume: float = -18.0
    fx: str = "none"
    objective: str = ""
    ground: Dict[Cell, Atlas] = field(default_factory=dict)
    details_below: Dict[Cell, Atlas] = field(default_factory=dict)
    walls: Dict[Cell, Atlas] = field(default_factory=dict)
    details_above: Dict[Cell, Atlas] = field(default_factory=dict)
    collision: Set[Cell] = field(default_factory=set)
    spawns: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    interactions: List[Interaction] = field(default_factory=list)
    npcs: List[NPC] = field(default_factory=list)
    triggers: List[Trigger] = field(default_factory=list)
    guards: List[GuardSpawn] = field(default_factory=list)
    peels: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    progress: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    props: List[Prop] = field(default_factory=list)

    @property
    def world_size(self) -> Tuple[int, int]:
        return self.w * TILE, self.h * TILE

    @property
    def player_bounds(self) -> Tuple[int, int, int, int]:
        return 8, 8, self.w * TILE - 16, self.h * TILE - 16


def init_room(spec: RoomSpec, openings: Iterable[Cell] = ()) -> None:
    # Floor and subtle variation.
    fill_rect(spec.ground, 0, 0, spec.w - 1, spec.h - 1, spec.floor, spec.floor_alt)
    # Architectural border.
    line_h(spec.walls, 0, 0, spec.w - 1, spec.wall_top)
    line_h(spec.walls, spec.h - 1, 0, spec.w - 1, spec.wall_bottom)
    line_v(spec.walls, 0, 1, spec.h - 2, spec.wall)
    line_v(spec.walls, spec.w - 1, 1, spec.h - 2, spec.wall)
    for cell in openings:
        spec.walls.pop(cell, None)
    spec.collision |= border_cells(spec.w, spec.h, openings)


def temple_exterior() -> RoomSpec:
    r = RoomSpec("temple_exterior", "THE TEMPLE", 20, 12, "grass_dark", "grass_dark", "temple_wall", "temple_wall_top", "temple_wall_bottom", "res://assets/audio/temple_drone.wav", -17.0, "res://assets/audio/rain_loop.wav", -20.0, "rain", "Enter the temple")
    # Courtyard/path and temple facade.
    fill_rect(r.ground, 0, 0, 19, 11, "grass_dark")
    fill_rect(r.ground, 7, 6, 12, 11, "path", "street_floor_alt")
    fill_rect(r.walls, 4, 1, 15, 6, "building_face")
    line_h(r.details_above, 1, 3, 16, "roof")
    for x in (5, 7, 12, 14):
        r.details_above[(x, 3)] = TILES["building_window"]
    for x in (4, 15):
        line_v(r.details_above, x, 2, 6, "pillar")
    for x in range(7, 13):
        r.details_below[(x, 7)] = TILES["temple_steps"]
    r.details_above[(9, 5)] = TILES["temple_door"]
    r.details_above[(10, 5)] = TILES["temple_door"]
    r.details_above[(2, 8)] = TILES["lamp"]
    r.details_above[(17, 8)] = TILES["lamp"]
    r.collision |= rect_cells(4, 1, 15, 5)
    r.collision -= {(9, 5), (10, 5)}
    r.collision |= border_cells(20, 12, {(9, 11), (10, 11)})
    r.spawns = {"Default": c(9.5, 10.2)}
    r.interactions = [Interaction("temple_front_door", "enter_temple", "Enter the temple", c(9.5, 6.4), 24.0, True)]
    return r


def temple_interior() -> RoomSpec:
    r = RoomSpec("temple_interior", "INSIDE THE TEMPLE", 20, 12, "temple_floor", "temple_floor_alt", "temple_wall", "temple_wall_top", "temple_wall_bottom", "res://assets/audio/temple_drone.wav", -15.0, fx="dust", objective="Approach the altar")
    init_room(r, {(9, 11), (10, 11)})
    # Central aisle carpet.
    fill_rect(r.details_below, 8, 2, 11, 10, "ritual_carpet", "ritual_carpet_border")
    # Altar and rear arch.
    for x in range(7, 13): r.details_above[(x, 1)] = TILES["arch"]
    put(r.details_above, {(8, 2), (9, 2), (10, 2), (11, 2)}, "altar_base")
    r.details_above[(9, 1)] = TILES["altar_top"]
    r.details_above[(10, 1)] = TILES["banana_symbol"]
    r.collision |= rect_cells(8, 1, 11, 2)
    # Pews with clear central aisle.
    for y in (5, 7, 9):
        for x in range(2, 7): r.details_above[(x, y)] = TILES["pew_mid"]
        r.details_above[(1, y)] = TILES["pew_left"]
        r.details_above[(7, y)] = TILES["pew_right"]
        for x in range(13, 18): r.details_above[(x, y)] = TILES["pew_mid"]
        r.details_above[(12, y)] = TILES["pew_left"]
        r.details_above[(18, y)] = TILES["pew_right"]
        r.collision |= rect_cells(1, y, 7, y)
        r.collision |= rect_cells(12, y, 18, y)
    for x in (2, 17):
        r.details_above[(x, 3)] = TILES["candle"]
    r.details_above[(9, 11)] = TILES["temple_door"]
    r.details_above[(10, 11)] = TILES["temple_door"]
    r.spawns = {"Default": c(9.5, 9.7), "Entrance": c(9.5, 9.7)}
    r.interactions = [
        Interaction("prayer_altar", "pray_at_altar", "Pray", c(9.5, 3.2), 24.0, True),
        Interaction("temple_exit", "leave_temple", "Leave the temple", c(9.5, 10.2), 20.0, False),
    ]
    return r


def street() -> RoomSpec:
    r = RoomSpec("street", "THE STREET", 20, 12, "street_floor", "street_floor_alt", "brick_wall", "brick_wall", "brick_wall", "res://assets/audio/temple_drone.wav", -20.0, "res://assets/audio/rain_loop.wav", -18.0, "rain", "Head home")
    fill_rect(r.ground, 0, 0, 19, 11, "street_floor", "street_floor_alt")
    # Building strip at top.
    fill_rect(r.walls, 0, 0, 19, 3, "city_wall")
    for x in (1, 4, 7, 12, 15, 18): r.details_above[(x, 1)] = TILES["city_window"]
    r.details_above[(9, 2)] = TILES["temple_door"]; r.details_above[(10, 2)] = TILES["temple_door"]
    r.collision |= rect_cells(0, 0, 19, 3)
    r.collision |= border_cells(20, 12)
    for x, y in ((4, 7), (14, 8), (7, 10)):
        r.details_below[(x, y)] = TILES["puddle"]
    r.details_below[(9, 7)] = TILES["manhole"]; r.details_below[(10, 7)] = TILES["manhole"]
    r.details_above[(2, 5)] = TILES["lamp"]; r.details_above[(17, 5)] = TILES["lamp"]
    r.spawns = {"Default": c(9.5, 4.2), "TempleDoor": c(9.5, 4.2)}
    r.interactions = [Interaction("open_manhole", "fall_into_manhole", "Inspect the suspicious puddle", c(9.5, 7.3), 24.0, True)]
    return r


def sewer_explore() -> RoomSpec:
    r = RoomSpec("sewer_explore", "BENEATH THE TEMPLE", 40, 12, "sewer_walk", "sewer_walk_alt", "sewer_wall", "sewer_wall_top", "sewer_wall_bottom", "res://assets/audio/heartbeat_loop.wav", -17.0, "res://assets/audio/sewer_flow_loop.wav", -17.0, "sewer", "Follow the thumping")
    fill_rect(r.ground, 0, 0, 39, 11, "sewer_water", "sewer_water_alt")
    # Upper tunnel wall and long walkable ledge.
    fill_rect(r.walls, 0, 0, 39, 4, "sewer_wall", "sewer_wall_moss")
    fill_rect(r.ground, 0, 5, 39, 8, "sewer_walk", "sewer_walk_alt")
    line_h(r.details_below, 9, 0, 39, "water_edge_top")
    r.collision |= rect_cells(0, 0, 39, 4)
    r.collision |= border_cells(40, 12)
    # Pipes along upper wall.
    for x in range(1, 39):
        if x % 7 != 0: r.details_above[(x, 3)] = TILES["pipe_h"]
    for x in (4, 12, 24, 34):
        r.details_above[(x, 2)] = TILES["pipe_v"]
        r.details_above[(x, 3)] = TILES["pipe_corner"]
    # Obstacles with walkable gaps.
    for x, y in ((6, 7), (7, 7), (18, 6), (29, 6), (30, 6), (31, 6)):
        r.details_above[(x, y)] = TILES["crate"]
        r.collision.add((x, y))
    # Cult window and stairs.
    for x in (30, 31, 32): r.details_above[(x, 5)] = TILES["sewer_window"]
    r.details_above[(37, 5)] = TILES["stairs_down"]
    r.details_above[(38, 5)] = TILES["stairs_down"]
    r.spawns = {"Default": c(2, 7), "WashedUp": c(2, 7)}
    r.interactions = [
        Interaction("cult_observation_window", "inspect_cult_window", "Look through the window", c(31, 6.3), 24.0, True),
        Interaction("sewer_stairs", "descend_to_lobby", "Descend the stairs", c(37.5, 6.2), 22.0, False),
        Interaction("inspect_sewer_sign", "inspect_sewer_sign", "Read the corroded sign", (272.0, 102.0), 21.0, True),
    ]
    r.props = [Prop("LowerTempleSign", "res://assets/props/sewer_direction_sign.png", (272.0, 78.0), (1.0, 1.0), 1)]
    return r


def cult_lobby() -> RoomSpec:
    r = RoomSpec("cult_lobby", "THE UNDERGROUND LOBBY", 20, 12, "cult_floor", "cult_floor_alt", "cult_wall", "cult_wall_top", "cult_wall_bottom", "res://assets/audio/cult_music_loop.wav", -14.0, fx="dust", objective="Find a way through the double doors")
    init_room(r, {(3, 11), (4, 11), (9, 0), (10, 0)})
    # Double door and ceremonial aisle.
    r.details_above[(9, 0)] = TILES["cult_door"]; r.details_above[(10, 0)] = TILES["cult_door"]
    fill_rect(r.details_below, 8, 1, 11, 10, "ritual_carpet", "ritual_carpet_border")
    # Reception desk left, vending shrine right, chairs.
    for x in range(2, 7): r.details_above[(x, 6)] = TILES["desk"]
    r.collision |= rect_cells(2, 6, 6, 6)
    for y in range(4, 8):
        r.details_above[(17, y)] = TILES["box_stack"]
        r.collision.add((17, y))
    for x, y in ((12, 7), (14, 7), (12, 9), (14, 9)):
        r.details_above[(x, y)] = TILES["chair"]
        r.collision.add((x, y))
    r.details_above[(4, 3)] = TILES["banana_banner"]; r.details_above[(15, 3)] = TILES["banana_banner"]
    r.spawns = {"Default": c(3.5, 9.5), "SewerStairs": c(3.5, 9.5)}
    r.interactions = [
        Interaction("cult_double_doors", "cult_induction", "Approach the guarded doors", c(9.5, 2.8), 26.0, True),
        Interaction("inspect_vending_machine", "inspect_vending_machine", "Inspect the banana vending machine", (278.0, 150.0), 21.0, True),
        Interaction("inspect_cult_noticeboard", "inspect_cult_noticeboard", "Read the cult noticeboard", (48.0, 101.0), 20.0, True),
    ]
    r.npcs = [NPC("guard_01", "guard", c(8, 3.8), 0), NPC("guard_02", "guard", c(11, 3.8), 0), NPC("cultist_03", "cultist", c(5, 4.3), 2)]
    r.props = [
        Prop("BananaVendingMachine", "res://assets/props/banana_vending_machine.png", (278.0, 122.0), (1.0, 1.0), 3),
        Prop("CultNoticeboard", "res://assets/props/cult_noticeboard.png", (48.0, 80.0), (1.0, 1.0), 1),
    ]
    return r


def cult_hq() -> RoomSpec:
    r = RoomSpec("cult_hq", "CULT HEADQUARTERS", 40, 23, "cult_floor", "cult_floor_alt", "cult_wall", "cult_wall_top", "cult_wall_bottom", "res://assets/audio/cult_music_loop.wav", -12.0, fx="dust", objective="Report to the Logistics Elder")
    init_room(r, {(19, 0), (20, 0), (0, 11), (39, 11), (5, 22), (6, 22), (19, 22), (20, 22)})
    # Cross-shaped ritual carpets.
    fill_rect(r.details_below, 18, 1, 21, 21, "ritual_carpet", "ritual_carpet_border")
    fill_rect(r.details_below, 1, 10, 38, 13, "ritual_carpet", "ritual_carpet_border")
    # Four work islands with circulation around them.
    islands = [(5, 4, 10, 7), (29, 4, 34, 7), (5, 15, 10, 18), (29, 15, 34, 18)]
    for x0, y0, x1, y1 in islands:
        fill_rect(r.details_above, x0, y0, x1, y1, "desk", "chair")
        r.collision |= rect_cells(x0, y0, x1, y1)
    # Doors and thematic markings.
    for pos in ((19, 0), (20, 0)): r.details_above[pos] = TILES["cult_door"]
    r.details_above[(0, 11)] = TILES["cult_door"]; r.details_above[(39, 11)] = TILES["metal_door"]
    r.details_above[(5, 22)] = TILES["cult_door"]; r.details_above[(6, 22)] = TILES["cult_door"]
    r.details_above[(19, 22)] = TILES["sealed_exit"]; r.details_above[(20, 22)] = TILES["sealed_exit"]
    for x, y, tile in ((6, 13, "purple_mark"), (33, 13, "yellow_mark"), (19, 8, "yellow_mark")):
        r.details_below[(x, y)] = TILES[tile]
    for x, y in ((2, 3), (37, 3), (2, 18), (37, 18)):
        r.details_above[(x, y)] = TILES["banana_banner"]
    # Named approach points keep transitions editable.
    r.spawns = {
        "Default": c(19.5, 20.0),
        "Lobby": c(19.5, 20.0),
        "FromStorage": c(19.5, 2.2),
        "FromStatue": c(2.2, 11.5),
        "FromEngine": c(36.8, 11.5),
        "FromQuarters": c(5.5, 19.5),
    }
    r.interactions = [
        Interaction("hq_foreman", "talk_foreman", "Speak to the Logistics Elder", c(19.5, 6.0), 22.0),
        Interaction("door_storage", "go_storage", "Enter Sacred Storage", c(19.5, 1.5), 20.0),
        Interaction("door_statue", "go_statue", "Enter the Shrine", c(1.5, 11.5), 20.0),
        Interaction("door_engine", "go_engine", "Enter the Engine Room", c(37.5, 11.5), 20.0),
        Interaction("door_quarters", "go_quarters", "Enter the Initiate Quarters", c(5.5, 20.5), 20.0),
        Interaction("hq_exit", "attempt_escape", "Use the sealed exit", c(19.5, 20.5), 22.0),
        Interaction("delivery_statue", "deliver_box_statue", "Place the box at the purple mark", c(6, 13), 20.0),
        Interaction("delivery_engine", "deliver_box_engine", "Place the box beside the machinery", c(33, 13), 20.0),
        Interaction("delivery_archive", "deliver_box_archive", "Place the box at the central desk", c(19, 8), 20.0),
        Interaction("inspect_ritual_drum", "inspect_ritual_drum", "Inspect the source of the thumping", (320.0, 123.0), 22.0, True),
    ]
    r.props = [Prop("RitualDrum", "res://assets/props/ritual_drum.png", (320.0, 99.0), (1.0, 1.0), 2)]
    r.npcs = [
        NPC("leader_01", "leader", c(19.5, 4.0), 0),
        NPC("cultist_02", "cultist", c(19.5, 6.0), 0),
        NPC("cultist_03", "cultist", c(4.0, 9.0), 2),
        NPC("cultist_04", "cultist", c(35.0, 9.0), 1),
        NPC("cultist_05", "cultist", c(14.0, 15.0), 0),
        NPC("cultist_06", "cultist", c(25.0, 15.0), 0),
    ]
    r.progress = {"DeliveryStatue": c(6, 13), "DeliveryEngine": c(33, 13), "DeliveryArchive": c(19, 8)}
    return r


def storage() -> RoomSpec:
    r = RoomSpec("storage", "SACRED STORAGE", 20, 12, "cult_floor", "cult_floor_alt", "cult_wall", "cult_wall_top", "cult_wall_bottom", "res://assets/audio/cult_music_loop.wav", -13.0, fx="dust", objective="Take a Sacred Box")
    init_room(r, {(9, 11), (10, 11)})
    # Shelves and crates around perimeter, clear center lane.
    for x in (2, 4, 15, 17):
        for y in range(2, 9):
            r.details_above[(x, y)] = TILES["shelf"]
            r.collision.add((x, y))
    for x, y in ((6, 3), (13, 3), (6, 8), (13, 8)):
        r.details_above[(x, y)] = TILES["crate"]
        r.collision.add((x, y))
    r.details_above[(9, 4)] = TILES["box_stack"]; r.details_above[(10, 4)] = TILES["box_stack"]
    r.details_above[(9, 5)] = TILES["box_stack"]; r.details_above[(10, 5)] = TILES["box_stack"]
    r.collision |= rect_cells(9, 4, 10, 5)
    r.details_above[(9, 11)] = TILES["cult_door"]; r.details_above[(10, 11)] = TILES["cult_door"]
    r.spawns = {"Default": c(9.5, 9.5), "FromHQ": c(9.5, 9.5)}
    r.interactions = [
        Interaction("sacred_box_stack", "pick_up_box", "Take a Sacred Box", c(9.5, 6.5), 22.0),
        Interaction("storage_exit", "return_from_storage", "Return to headquarters", c(9.5, 10.3), 20.0),
    ]
    r.npcs = [NPC("cultist_01", "cultist", c(7.5, 3.5), 0)]
    return r


def statue_room() -> RoomSpec:
    r = RoomSpec("statue_room", "SHRINE OF THE CURVED ONE", 20, 12, "cult_floor", "cult_floor_alt", "cult_wall", "cult_wall_top", "cult_wall_bottom", "res://assets/audio/cult_music_loop.wav", -12.0, fx="dust", objective="Polish The Curved One")
    init_room(r, {(9, 11), (10, 11)})
    # Carpet and circular shrine.
    fill_rect(r.details_below, 5, 2, 14, 8, "ritual_carpet", "ritual_carpet_border")
    for x, y in ((6, 3), (13, 3), (5, 6), (14, 6), (7, 8), (12, 8)):
        r.details_below[(x, y)] = TILES["ritual_circle"]
    put(r.details_above, rect_cells(7, 2, 12, 4), "shrine_platform")
    r.collision |= rect_cells(7, 2, 12, 4)
    for x, y in ((4, 4), (15, 4), (4, 8), (15, 8)):
        r.details_above[(x, y)] = TILES["candle"]
    r.details_above[(9, 11)] = TILES["cult_door"]; r.details_above[(10, 11)] = TILES["cult_door"]
    r.props = [Prop("GoldenBanana", "res://assets/props/golden_banana_statue.png", c(9.5, 3.0), (1.0, 1.0), 2)]
    r.spawns = {"Default": c(9.5, 9.5), "FromHQ": c(9.5, 9.5)}
    r.interactions = [
        Interaction("golden_statue", "polish_statue", "Polish The Curved One", c(9.5, 6.1), 24.0),
        Interaction("statue_exit", "return_from_statue", "Return to headquarters", c(9.5, 10.3), 20.0),
    ]
    r.npcs = [NPC("cultist_01", "cultist", c(4.5, 6.0), 2), NPC("cultist_02", "cultist", c(15.5, 6.0), 1)]
    r.progress = {"SealBurst": c(9.5, 5.5)}
    return r


def engine_room() -> RoomSpec:
    r = RoomSpec("engine_room", "THE RIPENING ENGINE", 20, 12, "metal_floor", "metal_floor_alt", "metal_wall", "metal_wall", "metal_wall", "res://assets/audio/cult_music_loop.wav", -12.0, fx="dust", objective="Load three fuel units")
    init_room(r, {(9, 11), (10, 11)})
    # Industrial wall pipes and center machinery.
    for x in range(1, 19):
        if x not in range(1, 7):
            r.details_above[(x, 2)] = TILES["pipe_h"]
    for x in (7, 16):
        r.details_above[(x, 1)] = TILES["pipe_v"]; r.details_above[(x, 2)] = TILES["pipe_corner"]
    put(r.details_above, rect_cells(7, 3, 12, 6), "engine_base")
    for x in (8, 11): r.details_above[(x, 4)] = TILES["engine_pipe"]
    r.details_above[(9, 4)] = TILES["engine_core"]; r.details_above[(10, 4)] = TILES["engine_core"]
    r.collision |= rect_cells(7, 3, 12, 6)
    # Fuel stations, separated from engine approach.
    put(r.details_above, rect_cells(2, 6, 4, 8), "crate")
    put(r.details_above, rect_cells(15, 6, 17, 8), "crate")
    r.collision |= rect_cells(2, 6, 4, 8) | rect_cells(15, 6, 17, 8)
    r.details_above[(9, 11)] = TILES["metal_door"]; r.details_above[(10, 11)] = TILES["metal_door"]
    r.props = [
        Prop("RipeningEngine", "res://assets/props/ripening_engine.png", c(9.5, 4.7), (1.0, 1.0), 2),
        Prop(
            "PotassiumConfigPanel",
            "res://assets/props/potassium_config_panel.png",
            c(3.5, 1.45),
            (0.65, 0.65),
            1,
        ),
    ]
    r.spawns = {"Default": c(9.5, 9.6), "FromHQ": c(9.5, 9.6)}
    r.interactions = [
        Interaction("fuel_left", "load_banana_fuel_left", "Collect yellow fuel", c(5.0, 7.0), 20.0),
        Interaction("fuel_right", "load_banana_fuel_right", "Collect suspicious fruit", c(14.0, 7.0), 20.0),
        Interaction("fuel_apple", "load_apple", "Insert the forbidden apple", c(6.0, 3.0), 20.0),
        Interaction(
            "potassium_configuration",
            "inspect_potassium_configuration",
            "Read the potassium configuration panel",
            c(4.6, 4.15),
            28.0,
        ),
        Interaction("engine_core", "activate_engine", "Activate the Ripening Engine", c(9.5, 7.0), 22.0),
        Interaction("engine_exit", "return_from_engine", "Return to headquarters", c(9.5, 10.3), 20.0),
    ]
    r.npcs = [NPC("cultist_01", "cultist", c(14.0, 4.5), 1)]
    r.progress = {"FuelLeft": c(8.5, 6.5), "FuelRight": c(9.5, 6.5), "FuelApple": c(10.5, 6.5), "SealBurst": c(9.5, 5.5), "AppleLaunchStart": c(5.5, 4.5), "AppleLaunchTarget": c(17.0, 2.5)}
    return r


def quarters() -> RoomSpec:
    r = RoomSpec("quarters", "INITIATE QUARTERS", 20, 12, "cult_floor", "cult_floor_alt", "cult_wall", "cult_wall_top", "cult_wall_bottom", "res://assets/audio/cult_music_loop.wav", -14.0, fx="dust", objective="Find Brother Cavendish")
    init_room(r, {(9, 11), (10, 11)})
    # Five lockers across the upper half with approach lane below.
    locker_x = [2, 5, 8, 11, 14]
    for x in locker_x:
        for y in (2, 3, 4):
            r.details_above[(x, y)] = TILES["locker"]
            r.collision.add((x, y))
    for x in (3, 16):
        r.details_above[(x, 8)] = TILES["desk"]
        r.collision.add((x, 8))
    r.details_above[(9, 11)] = TILES["cult_door"]; r.details_above[(10, 11)] = TILES["cult_door"]
    r.spawns = {"Default": c(9.5, 9.5), "FromHQ": c(9.5, 9.5)}
    r.interactions = []
    for idx, x in enumerate(locker_x, start=1):
        r.interactions.append(Interaction(f"locker_{idx}", f"search_locker_{idx}", f"Search locker {idx}", c(x, 5.6), 18.0))
    r.interactions.append(Interaction("quarters_exit", "return_from_quarters", "Return to headquarters", c(9.5, 10.3), 20.0))
    r.progress = {"Cavendish": c(11, 5.5), "SealBurst": c(11, 5.0)}
    return r


def chase() -> RoomSpec:
    r = RoomSpec("chase", "THE ESCAPE", 80, 12, "cult_floor", "cult_floor_alt", "brick_wall", "brick_wall", "brick_wall", "res://assets/audio/chase_music.wav", -8.0, fx="dust", objective="RUN")
    init_room(r, {(0, 5), (0, 6), (79, 5), (79, 6)})
    # Long corridor with repeated arches, banners and staggered obstacles.
    for x in range(4, 78, 8):
        r.details_above[(x, 1)] = TILES["arch"]
        r.details_above[(x, 2)] = TILES["banana_banner"]
    obstacles = [(17, 5, 18, 7), (31, 3, 32, 5), (45, 6, 46, 8), (59, 4, 60, 6), (70, 6, 71, 8)]
    for x0, y0, x1, y1 in obstacles:
        put(r.details_above, rect_cells(x0, y0, x1, y1), "crate")
        r.collision |= rect_cells(x0, y0, x1, y1)
    # Keep alternating upper/lower escape lanes.
    for x in range(1, 79):
        if x % 9 == 0: r.details_below[(x, 9)] = TILES["floor_crack"]
    r.spawns = {"Default": c(2, 6), "Start": c(2, 6)}
    r.triggers = [Trigger("chase_finish", "finish_chase", c(78, 6), (32.0, 96.0), True)]
    r.guards = [GuardSpawn("Guard_01", c(0, 5.2), 42.0), GuardSpawn("Guard_02", (-32.0, c(0, 7)[1]), 45.0), GuardSpawn("Guard_03", (-72.0, c(0, 6)[1]), 48.0)]
    r.peels = {"Peel_01": c(21, 4), "Peel_02": c(37, 7), "Peel_03": c(52, 4), "Peel_04": c(66, 7)}
    return r


def surface_ending() -> RoomSpec:
    r = RoomSpec("surface_ending", "THE GREAT RIPENING", 20, 12, "street_floor", "street_floor_alt", "city_wall", "city_wall", "city_wall", "res://assets/audio/temple_drone.wav", -20.0, "res://assets/audio/rain_loop.wav", -22.0, "rain", "")
    fill_rect(r.ground, 0, 0, 19, 11, "street_floor", "street_floor_alt")
    fill_rect(r.walls, 0, 0, 19, 4, "city_wall")
    for x in (2, 5, 8, 12, 15, 18): r.details_above[(x, 2)] = TILES["city_window"]
    r.collision |= rect_cells(0, 0, 19, 4) | border_cells(20, 12)
    r.details_below[(9, 7)] = TILES["manhole"]; r.details_below[(10, 7)] = TILES["manhole"]
    r.details_above[(2, 6)] = TILES["lamp"]; r.details_above[(17, 6)] = TILES["lamp"]
    r.spawns = {"Default": c(9.5, 9.3)}
    return r


ROOM_BUILDERS = [
    temple_exterior,
    temple_interior,
    street,
    sewer_explore,
    cult_lobby,
    cult_hq,
    storage,
    statue_room,
    engine_room,
    quarters,
    chase,
    surface_ending,
]


def fmt_vec(v: Tuple[float, float]) -> str:
    return f"Vector2({v[0]:g}, {v[1]:g})"


def fmt_rect(v: Tuple[int, int, int, int]) -> str:
    return f"Rect2({v[0]}, {v[1]}, {v[2]}, {v[3]})"


def q(text: str) -> str:
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def render_room_scene(spec: RoomSpec) -> str:
    prop_textures: List[str] = []
    for prop in spec.props:
        if prop.texture not in prop_textures:
            prop_textures.append(prop.texture)
    prop_ids = {path: f"{8 + i}_prop" for i, path in enumerate(prop_textures)}
    ext_count = 7 + len(prop_textures)
    lines = [f"[gd_scene load_steps={ext_count + 1} format=3]", ""]
    lines += [
        '[ext_resource type="Script" path="res://scripts/room_definition.gd" id="1_room"]',
        '[ext_resource type="TileSet" path="res://assets/tiles/world_tileset.tres" id="2_tiles"]',
        '[ext_resource type="TileSet" path="res://assets/tiles/collision_tileset.tres" id="3_collision"]',
        '[ext_resource type="Script" path="res://scripts/interaction_point.gd" id="4_interaction"]',
        '[ext_resource type="Script" path="res://scripts/npc_spawn.gd" id="5_npc"]',
        '[ext_resource type="Script" path="res://scripts/trigger_marker.gd" id="6_trigger"]',
        '[ext_resource type="Script" path="res://scripts/guard_spawn.gd" id="7_guard"]',
    ]
    for path, res_id in prop_ids.items():
        lines.append(f'[ext_resource type="Texture2D" path={q(path)} id="{res_id}"]')
    lines += [
        "",
        f'[node name="{spec.room_id.title().replace("_", "")}" type="Node2D"]',
        'script = ExtResource("1_room")',
        f"room_id = {q(spec.room_id)}",
        f"room_title = {q(spec.title)}",
        f"world_size = Vector2({spec.world_size[0]}, {spec.world_size[1]})",
        f"player_bounds = {fmt_rect(spec.player_bounds)}",
        f"music_path = {q(spec.music)}",
        f"music_volume = {spec.music_volume:g}",
        f"ambient_path = {q(spec.ambient)}",
        f"ambient_volume = {spec.ambient_volume:g}",
        f"fx_mode = {q(spec.fx)}",
        f"default_objective = {q(spec.objective)}",
        "",
        '[node name="Tilemaps" type="Node2D" parent="."]',
        "",
    ]
    for name, layer, z in (
        ("Ground", spec.ground, -50),
        ("DetailsBelow", spec.details_below, -40),
        ("Walls", spec.walls, -20),
        ("DetailsAbove", spec.details_above, 20),
    ):
        lines += [f'[node name="{name}" type="TileMapLayer" parent="Tilemaps"]', f"z_index = {z}", 'tile_set = ExtResource("2_tiles")']
        if layer:
            lines.append(f'tile_map_data = PackedByteArray("{encode_cells(layer)}")')
        lines += ["texture_filter = 1", ""]
    collision_cells = {cell: (0, 0) for cell in spec.collision}
    lines += [
        '[node name="CollisionMap" type="TileMapLayer" parent="Tilemaps"]',
        "visible = false",
        "z_index = 90",
        'tile_set = ExtResource("3_collision")',
        f'tile_map_data = PackedByteArray("{encode_cells(collision_cells)}")',
        "collision_enabled = true",
        "navigation_enabled = false",
        "texture_filter = 1",
        "",
        '[node name="Actors" type="Node2D" parent="."]',
        "y_sort_enabled = true",
        "",
    ]
    for prop in spec.props:
        lines += [
            f'[node name={q(prop.name)} type="Sprite2D" parent="Actors"]',
            f"position = {fmt_vec(prop.pos)}",
            f'texture = ExtResource("{prop_ids[prop.texture]}")',
            f"scale = {fmt_vec(prop.scale)}",
            f"z_index = {prop.z_index}",
            "texture_filter = 1",
            "",
        ]
    lines += ['[node name="SpawnPoints" type="Node2D" parent="."]', ""]
    for name, pos in spec.spawns.items():
        lines += [f'[node name={q(name)} type="Marker2D" parent="SpawnPoints"]', f"position = {fmt_vec(pos)}", ""]
    lines += ['[node name="Interactions" type="Node2D" parent="."]', ""]
    for item in spec.interactions:
        lines += [
            f'[node name={q(item.name)} type="Marker2D" parent="Interactions"]',
            f"position = {fmt_vec(item.pos)}",
            'script = ExtResource("4_interaction")',
            f"interaction_id = {q(item.name)}",
            f"event_name = {q(item.event)}",
            f"prompt = {q(item.prompt)}",
            f"radius = {item.radius:g}",
            f"one_shot = {'true' if item.one_shot else 'false'}",
            "",
        ]
    lines += ['[node name="NPCSpawns" type="Node2D" parent="."]', ""]
    for item in spec.npcs:
        lines += [
            f'[node name={q(item.name)} type="Marker2D" parent="NPCSpawns"]',
            f"position = {fmt_vec(item.pos)}",
            'script = ExtResource("5_npc")',
            f"kind = {q(item.kind)}",
            f"facing = {item.facing}",
            f"animated = {'true' if item.animated else 'false'}",
            "",
        ]
    lines += ['[node name="Triggers" type="Node2D" parent="."]', ""]
    for item in spec.triggers:
        lines += [
            f'[node name={q(item.name)} type="Marker2D" parent="Triggers"]',
            f"position = {fmt_vec(item.pos)}",
            'script = ExtResource("6_trigger")',
            f"trigger_id = {q(item.name)}",
            f"event_name = {q(item.event)}",
            f"size = {fmt_vec(item.size)}",
            f"one_shot = {'true' if item.one_shot else 'false'}",
            "",
        ]
    lines += ['[node name="GuardSpawns" type="Node2D" parent="."]', ""]
    for item in spec.guards:
        lines += [
            f'[node name={q(item.name)} type="Marker2D" parent="GuardSpawns"]',
            f"position = {fmt_vec(item.pos)}",
            'script = ExtResource("7_guard")',
            f"speed = {item.speed:g}",
            "",
        ]
    lines += ['[node name="PeelSpawns" type="Node2D" parent="."]', ""]
    for name, pos in spec.peels.items():
        lines += [f'[node name={q(name)} type="Marker2D" parent="PeelSpawns"]', f"position = {fmt_vec(pos)}", ""]
    lines += ['[node name="ProgressMarkers" type="Node2D" parent="."]', ""]
    for name, pos in spec.progress.items():
        lines += [f'[node name={q(name)} type="Marker2D" parent="ProgressMarkers"]', f"position = {fmt_vec(pos)}", ""]
    return "\n".join(lines).rstrip() + "\n"


def build_rooms() -> Dict[str, RoomSpec]:
    rooms: Dict[str, RoomSpec] = {}
    out_dir = ROOT / "scenes" / "rooms"
    out_dir.mkdir(parents=True, exist_ok=True)
    for builder in ROOM_BUILDERS:
        spec = builder()
        rooms[spec.room_id] = spec
        (out_dir / f"{spec.room_id}.tscn").write_text(render_room_scene(spec), encoding="utf-8")
    return rooms


# ---------------------------------------------------------------------------
# Tile-built cinematic scenes
# ---------------------------------------------------------------------------


def render_cutscene_scene(name: str, w: int, h: int, layers: Mapping[str, Mapping[Cell, Atlas]]) -> str:
    lines = [
        "[gd_scene load_steps=2 format=3]",
        "",
        '[ext_resource type="TileSet" path="res://assets/tiles/world_tileset.tres" id="1_tiles"]',
        "",
        f'[node name={q(name)} type="Node2D"]',
        "",
    ]
    for layer_name, cells in layers.items():
        lines += [
            f'[node name={q(layer_name)} type="TileMapLayer" parent="."]',
            'tile_set = ExtResource("1_tiles")',
            f'tile_map_data = PackedByteArray("{encode_cells(cells)}")',
            "texture_filter = 1",
            "",
        ]
    return "\n".join(lines)


def build_cutscenes() -> None:
    out = ROOT / "scenes" / "cutscenes"
    out.mkdir(parents=True, exist_ok=True)
    # Tall fall shaft, 20x36.
    ground: Dict[Cell, Atlas] = {}
    walls: Dict[Cell, Atlas] = {}
    details: Dict[Cell, Atlas] = {}
    fill_rect(ground, 0, 0, 19, 35, "void")
    for y in range(36):
        for x in (0, 1, 18, 19): walls[(x, y)] = TILES["sewer_wall"]
        if y % 5 == 0:
            for x in range(2, 18): details[(x, y)] = TILES["pipe_h"]
        if y % 9 == 3:
            details[(4, y)] = TILES["pipe_v"]; details[(15, y)] = TILES["pipe_v"]
        if y % 7 == 2:
            details[(2, y)] = TILES["warning_stripe"]
            details[(17, y)] = TILES["warning_stripe"]
        if y % 11 == 6:
            details[(6, y)] = TILES["grate"]
            details[(13, y)] = TILES["vent"]
        if y % 13 == 8:
            details[(9, y)] = TILES["lamp"]
            details[(10, y)] = TILES["lamp"]
    (out / "fall_shaft.tscn").write_text(render_cutscene_scene("FallShaft", 20, 36, {"Ground": ground, "Walls": walls, "Details": details}), encoding="utf-8")

    # Horizontal sewer ride, 40x12.
    ground = {}; walls = {}; details = {}
    fill_rect(ground, 0, 0, 39, 11, "sewer_water", "sewer_water_alt")
    fill_rect(walls, 0, 0, 39, 4, "sewer_wall", "sewer_wall_moss")
    line_h(details, 5, 0, 39, "water_edge_top")
    for x in range(40):
        if x % 3 != 0: details[(x, 3)] = TILES["pipe_h"]
        if x % 11 == 0: details[(x, 2)] = TILES["pipe_v"]
    (out / "sewer_ride.tscn").write_text(render_cutscene_scene("SewerRide", 40, 12, {"Ground": ground, "Walls": walls, "Details": details}), encoding="utf-8")

    # Ritual window cinematic.
    ground = {}; walls = {}; details = {}
    fill_rect(ground, 0, 0, 19, 11, "cult_floor", "cult_floor_alt")
    put(walls, border_cells(20, 12), "cult_wall")
    fill_rect(details, 6, 2, 13, 9, "ritual_carpet", "ritual_carpet_border")
    for x, y in ((4, 3), (15, 3), (4, 8), (15, 8)): details[(x, y)] = TILES["candle"]
    details[(9, 5)] = TILES["banana_symbol"]; details[(10, 5)] = TILES["banana_symbol"]
    for x, y in ((6, 3), (8, 2), (11, 2), (13, 3), (5, 6), (14, 6), (7, 9), (12, 9)):
        details[(x, y)] = TILES["banana_banner"]
    (out / "cult_window.tscn").write_text(render_cutscene_scene("CultWindow", 20, 12, {"Ground": ground, "Walls": walls, "Details": details}), encoding="utf-8")


def main() -> None:
    build_atlas()
    # Reapply the v3.2 art pass after rebuilding the base atlas. This preserves
    # the polished environment, props and menu artwork when rooms are reset.
    from build_art_v3_2 import build_all
    build_all()
    build_tilesets()
    rooms = build_rooms()
    build_cutscenes()
    print(f"Generated {len(rooms)} tile-mapped rooms and 3 tile-mapped cutscenes.")


if __name__ == "__main__":
    main()
