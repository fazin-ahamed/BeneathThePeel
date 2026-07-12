#!/usr/bin/env python3
"""Helpers for validating Godot 4 TileMapLayer scene files.

This intentionally parses only the compact text features used by this project;
it is independent of the room generator so packaged scenes are checked as-built.
"""
from __future__ import annotations

import base64
import math
import re
import struct
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

TILE_SIZE = 16
NODE_RE = re.compile(
    r'^\[node name="([^"]+)" type="([^"]+)"(?: parent="([^"]*)")?[^\]]*\]\s*$',
    re.MULTILINE,
)
VECTOR_RE = re.compile(r"Vector2\(([-+\d.eE]+),\s*([-+\d.eE]+)\)")
RECT_RE = re.compile(
    r"Rect2\(([-+\d.eE]+),\s*([-+\d.eE]+),\s*([-+\d.eE]+),\s*([-+\d.eE]+)\)"
)


@dataclass
class NodeBlock:
    name: str
    node_type: str
    parent: str
    properties: dict[str, str] = field(default_factory=dict)

    @property
    def full_path(self) -> str:
        return self.name if not self.parent or self.parent == "." else f"{self.parent}/{self.name}"

    def vector(self, key: str, default: tuple[float, float] | None = None):
        value = self.properties.get(key)
        if value is None:
            return default
        match = VECTOR_RE.fullmatch(value)
        return (float(match.group(1)), float(match.group(2))) if match else default

    def number(self, key: str, default: float = 0.0) -> float:
        value = self.properties.get(key)
        return float(value) if value is not None else default

    def boolean(self, key: str, default: bool = False) -> bool:
        value = self.properties.get(key)
        if value is None:
            return default
        return value.strip().lower() == "true"

    def string(self, key: str, default: str = "") -> str:
        value = self.properties.get(key)
        if value is None:
            return default
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            return value[1:-1].replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        return value


@dataclass
class ParsedScene:
    path: Path
    text: str
    root_properties: dict[str, str]
    nodes: list[NodeBlock]

    def node(self, full_path: str) -> NodeBlock | None:
        for item in self.nodes:
            if item.full_path == full_path:
                return item
        return None

    def children_of(self, parent: str) -> list[NodeBlock]:
        return [item for item in self.nodes if item.parent == parent]


def parse_scene(path: Path) -> ParsedScene:
    text = path.read_text(encoding="utf-8")
    matches = list(NODE_RE.finditer(text))
    if not matches:
        raise ValueError(f"{path}: no [node] blocks")
    nodes: list[NodeBlock] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end]
        props: dict[str, str] = {}
        for raw in body.splitlines():
            line = raw.strip()
            if not line or line.startswith("[") or " = " not in line:
                continue
            key, value = line.split(" = ", 1)
            props[key.strip()] = value.strip()
        nodes.append(NodeBlock(match.group(1), match.group(2), match.group(3) or "", props))
    root = nodes[0]
    return ParsedScene(path, text, root.properties, nodes)


def decode_tile_data(value: str) -> dict[tuple[int, int], tuple[int, int, int, int]]:
    match = re.fullmatch(r'PackedByteArray\("([A-Za-z0-9+/=]*)"\)', value.strip())
    if not match:
        raise ValueError("invalid PackedByteArray syntax")
    raw = base64.b64decode(match.group(1), validate=True)
    if len(raw) < 2 or raw[:2] != b"\x00\x00":
        raise ValueError("unexpected TileMap data header")
    payload = raw[2:]
    if len(payload) % 12:
        raise ValueError(f"tile payload is {len(payload)} bytes, not divisible by 12")
    cells: dict[tuple[int, int], tuple[int, int, int, int]] = {}
    for offset in range(0, len(payload), 12):
        x, y, source, atlas_x, atlas_y, alternative = struct.unpack_from("<hhhhhh", payload, offset)
        key = (x, y)
        if key in cells:
            raise ValueError(f"duplicate tile cell {key}")
        cells[key] = (source, atlas_x, atlas_y, alternative)
    return cells


def tile_cells(node: NodeBlock | None) -> dict[tuple[int, int], tuple[int, int, int, int]]:
    if node is None:
        return {}
    value = node.properties.get("tile_map_data")
    return decode_tile_data(value) if value else {}


def root_vector(scene: ParsedScene, key: str, default: tuple[float, float]) -> tuple[float, float]:
    value = scene.root_properties.get(key)
    if value is None:
        return default
    match = VECTOR_RE.fullmatch(value)
    if not match:
        raise ValueError(f"{scene.path.name}: malformed {key}")
    return float(match.group(1)), float(match.group(2))


def root_rect(scene: ParsedScene, key: str, default: tuple[float, float, float, float]):
    value = scene.root_properties.get(key)
    if value is None:
        return default
    match = RECT_RE.fullmatch(value)
    if not match:
        raise ValueError(f"{scene.path.name}: malformed {key}")
    return tuple(float(match.group(i)) for i in range(1, 5))


def footprint_blocked(
    point: tuple[float, float],
    collision_cells: set[tuple[int, int]],
    bounds: tuple[float, float, float, float],
    half: tuple[float, float] = (5.0, 6.0),
) -> bool:
    x, y = point
    bx, by, bw, bh = bounds
    hx, hy = half
    if x < bx + hx or x > bx + bw - hx or y < by + hy or y > by + bh - hy:
        return True
    min_cx = math.floor((x - hx) / TILE_SIZE)
    max_cx = math.floor((x + hx - 1e-6) / TILE_SIZE)
    min_cy = math.floor((y - hy) / TILE_SIZE)
    max_cy = math.floor((y + hy - 1e-6) / TILE_SIZE)
    for cy in range(min_cy, max_cy + 1):
        for cx in range(min_cx, max_cx + 1):
            if (cx, cy) in collision_cells:
                return True
    return False


def reachable_points(
    start: tuple[float, float],
    collision_cells: set[tuple[int, int]],
    bounds: tuple[float, float, float, float],
    step: int = 4,
) -> set[tuple[int, int]]:
    sx = int(round(start[0] / step) * step)
    sy = int(round(start[1] / step) * step)
    first = (sx, sy)
    if footprint_blocked(first, collision_cells, bounds):
        return set()
    queue = deque([first])
    visited = {first}
    while queue:
        x, y = queue.popleft()
        for candidate in ((x + step, y), (x - step, y), (x, y + step), (x, y - step)):
            if candidate in visited or footprint_blocked(candidate, collision_cells, bounds):
                continue
            visited.add(candidate)
            queue.append(candidate)
    return visited


def nearest_distance(points: Iterable[tuple[int, int]], target: tuple[float, float]) -> float:
    tx, ty = target
    return min((math.hypot(x - tx, y - ty) for x, y in points), default=math.inf)


def rect_has_reachable_point(
    points: Iterable[tuple[int, int]], center: tuple[float, float], size: tuple[float, float]
) -> bool:
    cx, cy = center
    sx, sy = size
    left, top, right, bottom = cx - sx * 0.5, cy - sy * 0.5, cx + sx * 0.5, cy + sy * 0.5
    return any(left <= x <= right and top <= y <= bottom for x, y in points)
