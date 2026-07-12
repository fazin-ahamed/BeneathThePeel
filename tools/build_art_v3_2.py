#!/usr/bin/env python3
"""Regenerate Beneath the Peel v3.3 non-character pixel art.

The character sheets are deliberately untouched. This script upgrades the
TileMap atlas, world props, and title/menu artwork while preserving every
runtime texture size used by the Godot scenes.
"""
from __future__ import annotations

from pathlib import Path
from random import Random
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TILE = 16

INK = (12, 10, 20, 255)
INK_2 = (24, 18, 31, 255)
CREAM = (244, 229, 185, 255)
GOLD = (244, 190, 49, 255)
GOLD_HI = (255, 230, 111, 255)
AMBER = (203, 112, 39, 255)
BURGUNDY = (91, 27, 58, 255)
PURPLE = (62, 34, 69, 255)
TEAL = (35, 116, 123, 255)
TEAL_HI = (92, 190, 185, 255)
STEEL = (71, 79, 91, 255)
STEEL_HI = (132, 145, 151, 255)


def _outline_alpha(tile: Image.Image, color: tuple[int, int, int, int] = INK) -> Image.Image:
    src = tile.convert("RGBA")
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp = src.load()
    op = out.load()
    for y in range(src.height):
        for x in range(src.width):
            if sp[x, y][3] != 0:
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < src.width and 0 <= ny < src.height and sp[nx, ny][3] > 0:
                    op[x, y] = color
                    break
    out.alpha_composite(src)
    return out


def polish_environment_atlas() -> None:
    path = ROOT / "assets/tiles/btp_environment_tiles.png"
    atlas = Image.open(path).convert("RGBA")
    rng = Random(1938)
    polished = Image.new("RGBA", atlas.size, (0, 0, 0, 0))
    for ty in range(6):
        for tx in range(16):
            tile = atlas.crop((tx * TILE, ty * TILE, (tx + 1) * TILE, (ty + 1) * TILE))
            alpha_bbox = tile.getchannel("A").getbbox()
            opaque_ratio = sum(1 for a in tile.getchannel("A").getdata() if a > 0) / 256.0
            if opaque_ratio > 0.92:
                tile = ImageEnhance.Contrast(tile).enhance(1.10)
                d = ImageDraw.Draw(tile)
                # Consistent pixel-depth treatment for painted surfaces.
                if ty == 0:  # floors
                    d.line((0, 0, 15, 0), fill=(255, 255, 255, 18))
                    d.line((0, 15, 15, 15), fill=(0, 0, 0, 40))
                    for _ in range(3):
                        x, y = rng.randrange(1, 15), rng.randrange(1, 15)
                        old = tile.getpixel((x, y))
                        if old[3]:
                            d.point((x, y), fill=(max(0, old[0] - 12), max(0, old[1] - 12), max(0, old[2] - 12), old[3]))
                elif ty == 1:  # walls
                    d.line((0, 0, 15, 0), fill=(205, 176, 174, 90))
                    d.line((0, 14, 15, 14), fill=(15, 11, 24, 100))
                    d.line((0, 15, 15, 15), fill=(7, 6, 13, 150))
                elif ty in (4, 5):
                    d.line((0, 15, 15, 15), fill=(0, 0, 0, 48))
            elif alpha_bbox is not None:
                tile = _outline_alpha(tile)
                tile = ImageEnhance.Contrast(tile).enhance(1.08)
                d = ImageDraw.Draw(tile)
                # Small material glints on props and architecture.
                if ty in (2, 3, 4):
                    for x, y in ((3, 3), (11, 5)):
                        if tile.getpixel((x, y))[3] > 0:
                            d.point((x, y), fill=(255, 235, 170, 120))
            polished.alpha_composite(tile, (tx * TILE, ty * TILE))
    polished.save(path)


def draw_sacred_box() -> Image.Image:
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((1, 2, 14, 14), fill=(61, 34, 35, 255), outline=INK)
    d.rectangle((2, 3, 13, 13), fill=(117, 66, 42, 255))
    d.line((2, 5, 13, 5), fill=(173, 101, 51, 255))
    d.rectangle((1, 2, 3, 4), fill=STEEL_HI); d.rectangle((12, 2, 14, 4), fill=STEEL_HI)
    d.rectangle((1, 12, 3, 14), fill=STEEL); d.rectangle((12, 12, 14, 14), fill=STEEL)
    d.arc((5, 5, 11, 12), 245, 75, fill=GOLD, width=2)
    d.point((11, 10), fill=GOLD_HI)
    return im


def draw_security_seal() -> Image.Image:
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((1, 1, 14, 14), fill=(94, 54, 30, 255), outline=INK)
    d.ellipse((2, 2, 13, 13), fill=GOLD)
    d.ellipse((4, 4, 11, 11), fill=(116, 29, 63, 255), outline=(255, 223, 102, 255))
    d.polygon([(8, 4), (10, 7), (9, 11), (6, 11), (5, 7)], fill=(155, 45, 82, 255))
    d.point((5, 4), fill=CREAM); d.point((11, 5), fill=GOLD_HI)
    return im


def draw_golden_statue() -> Image.Image:
    im = Image.new("RGBA", (32, 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((4, 33, 27, 38), fill=(17, 11, 24, 145))
    d.rectangle((4, 31, 27, 36), fill=(71, 37, 43, 255), outline=INK)
    d.rectangle((7, 28, 24, 32), fill=(129, 67, 47, 255), outline=INK)
    # Layered curved banana body.
    d.arc((5, 3, 27, 30), 235, 70, fill=INK, width=8)
    d.arc((6, 3, 26, 29), 235, 70, fill=(196, 125, 35, 255), width=6)
    d.arc((7, 4, 25, 27), 235, 70, fill=GOLD, width=4)
    d.arc((8, 5, 24, 25), 235, 70, fill=GOLD_HI, width=1)
    d.rectangle((22, 5, 25, 8), fill=(83, 52, 32, 255))
    d.rectangle((6, 25, 9, 28), fill=(83, 52, 32, 255))
    d.point((18, 8), fill=(255, 247, 194, 255)); d.point((21, 11), fill=(255, 247, 194, 255))
    return im


def draw_manhole() -> Image.Image:
    im = Image.new("RGBA", (32, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((1, 3, 30, 15), fill=(12, 11, 18, 170))
    d.ellipse((2, 1, 29, 13), fill=(42, 47, 58, 255), outline=INK)
    d.ellipse((5, 3, 26, 11), fill=(31, 34, 43, 255), outline=STEEL_HI)
    for x in (8, 12, 16, 20, 24): d.line((x, 4, x - 2, 10), fill=(88, 97, 106, 255))
    d.arc((4, 2, 27, 12), 190, 340, fill=(153, 163, 168, 255), width=1)
    return im


def draw_engine() -> Image.Image:
    im = Image.new("RGBA", (64, 48), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((5, 40, 59, 47), fill=(10, 7, 17, 150))
    # side tanks
    for x in (3, 47):
        d.rectangle((x, 11, x + 13, 38), fill=(39, 43, 54, 255), outline=INK)
        d.rectangle((x + 2, 13, x + 11, 35), fill=(57, 63, 75, 255))
        d.line((x + 3, 14, x + 10, 14), fill=STEEL_HI)
        for y in (20, 27, 34): d.line((x + 3, y, x + 10, y), fill=(28, 31, 40, 255))
    # upper pipes
    d.line((10, 11, 10, 5, 27, 5, 27, 10), fill=INK, width=4)
    d.line((10, 10, 10, 6, 27, 6, 27, 11), fill=(83, 105, 105, 255), width=2)
    d.line((54, 11, 54, 5, 38, 5, 38, 10), fill=INK, width=4)
    d.line((54, 10, 54, 6, 38, 6, 38, 11), fill=(83, 105, 105, 255), width=2)
    # centre housing and core
    d.rectangle((17, 9, 46, 41), fill=(31, 27, 42, 255), outline=INK)
    d.rectangle((19, 11, 44, 39), fill=(61, 37, 53, 255), outline=STEEL)
    d.ellipse((22, 14, 41, 33), fill=(41, 19, 38, 255), outline=GOLD)
    d.ellipse((25, 17, 38, 30), fill=(151, 42, 71, 255), outline=GOLD_HI)
    d.ellipse((28, 20, 35, 27), fill=(255, 183, 52, 255))
    d.ellipse((30, 22, 33, 25), fill=(255, 246, 176, 255))
    # gauge and switches
    d.rectangle((20, 34, 28, 38), fill=(22, 22, 31, 255), outline=STEEL_HI)
    d.line((22, 36, 26, 36), fill=TEAL_HI)
    d.rectangle((35, 34, 42, 38), fill=(22, 22, 31, 255), outline=STEEL_HI)
    d.point((37, 36), fill=(96, 226, 154, 255)); d.point((40, 36), fill=(230, 67, 73, 255))
    # base
    d.rectangle((8, 39, 55, 44), fill=(49, 31, 39, 255), outline=INK)
    d.line((11, 40, 52, 40), fill=(126, 73, 69, 255))
    return im


def draw_potassium_panel() -> Image.Image:
    im = Image.new("RGBA", (128, 48), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((1, 3, 126, 45), fill=(21, 24, 33, 255), outline=INK, width=2)
    d.rectangle((4, 6, 123, 42), fill=(31, 38, 47, 255), outline=STEEL_HI)
    d.line((5, 7, 122, 7), fill=(78, 94, 100, 255))
    # periodic tile
    d.rectangle((8, 10, 35, 37), fill=(42, 54, 55, 255), outline=TEAL_HI)
    d.text((11, 10), "19", fill=(164, 206, 196, 255), font=ImageFont.load_default())
    d.text((16, 19), "K", fill=GOLD_HI, font=ImageFont.load_default())
    d.text((10, 30), "39.10", fill=(164, 206, 196, 255), font=ImageFont.load_default())
    # shell diagram
    cx, cy = 63, 24
    for r in (5, 10, 15): d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(62, 112, 121, 255))
    d.ellipse((cx-2, cy-2, cx+2, cy+2), fill=(179, 58, 78, 255))
    electrons = [(63,9),(63,39),(48,24),(78,24),(53,14),(73,34),(53,34),(73,14)]
    for x,y in electrons: d.rectangle((x-1,y-1,x+1,y+1), fill=GOLD)
    # configuration and cult annotation
    d.text((84, 10), "2  8  8  1", fill=CREAM, font=ImageFont.load_default())
    d.text((84, 22), "[Ar] 4s1", fill=GOLD, font=ImageFont.load_default())
    d.text((84, 33), "ONE OUTER", fill=TEAL_HI, font=ImageFont.load_default())
    d.point((122, 8), fill=(100, 255, 170, 255))
    return im


def draw_noticeboard() -> Image.Image:
    im = Image.new("RGBA", (48, 32), (0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle((1,2,46,29), fill=(77,45,35,255), outline=INK)
    d.rectangle((4,5,43,26), fill=(117,77,49,255), outline=(183,119,61,255))
    papers=[(6,7,17,16),(20,6,31,15),(33,8,41,19),(10,18,24,24),(27,17,39,25)]
    for i,b in enumerate(papers):
        d.rectangle(b, fill=(213,199,160,255), outline=(73,52,47,255))
        x1,y1,x2,y2=b
        d.line((x1+2,y1+3,x2-2,y1+3), fill=(97,78,69,255))
        if i==2: d.arc((x1+1,y1+1,x2-1,y2-1),245,75,fill=GOLD,width=1)
    for x,y in ((7,7),(22,7),(35,9),(12,19),(29,18)): d.point((x,y),fill=(191,45,51,255))
    return im


def draw_vending_machine() -> Image.Image:
    im=Image.new("RGBA",(32,48),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle((3,1,28,46), fill=(41,28,45,255), outline=INK, width=2)
    d.rectangle((6,5,25,28), fill=(19,25,34,255), outline=(111,82,104,255))
    for row in range(3):
        for col in range(3):
            x=8+col*6; y=8+row*6
            d.arc((x,y,x+5,y+5),240,70,fill=GOLD,width=2)
    d.rectangle((7,32,18,39), fill=(27,31,39,255), outline=STEEL_HI)
    d.rectangle((21,32,24,35), fill=(100,218,137,255))
    d.rectangle((8,42,24,45), fill=(17,15,24,255))
    d.line((5,3,26,3), fill=(153,72,111,255))
    return im


def draw_ritual_drum() -> Image.Image:
    im=Image.new("RGBA",(32,32),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.ellipse((4,2,27,11), fill=(143,82,58,255), outline=INK)
    d.rectangle((4,6,27,24), fill=(76,30,50,255), outline=INK)
    d.ellipse((4,19,27,28), fill=(56,24,41,255), outline=INK)
    for x in (7,13,19,25): d.line((x,8,x-1,22), fill=(211,155,66,255))
    d.arc((9,8,22,22),245,75,fill=GOLD,width=2)
    return im


def draw_sewer_sign() -> Image.Image:
    im=Image.new("RGBA",(48,24),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle((1,2,46,20), fill=(37,47,50,255), outline=INK)
    d.rectangle((3,4,44,18), fill=(68,80,75,255), outline=(126,139,126,255))
    d.text((6,7), "LOWER TEMPLE", fill=(220,191,79,255), font=ImageFont.load_default())
    d.line((4,21,4,23),fill=STEEL); d.line((43,21,43,23),fill=STEEL)
    return im


def draw_menu_selector() -> Image.Image:
    im=Image.new("RGBA",(10,10),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.arc((0,0,8,9),240,70,fill=INK,width=4)
    d.arc((1,0,8,8),240,70,fill=GOLD,width=2)
    d.point((8,2),fill=GOLD_HI)
    return im


def pixel_text(draw: ImageDraw.ImageDraw, xy: tuple[int,int], text: str, fill, size: int, anchor: str | None = None) -> None:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    font = ImageFont.truetype(font_path, size=size)
    draw.text(xy, text, fill=fill, font=font, anchor=anchor, stroke_width=max(1,size//12), stroke_fill=(8,6,14,255))


def draw_title_background() -> Image.Image:
    im = Image.new("RGBA", (320, 180), (6, 8, 18, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 319, 78), fill=(8, 12, 28, 255))
    d.rectangle((0, 78, 319, 179), fill=(10, 12, 22, 255))
    for box, color in (
        ((0, 15, 105, 42), (14, 18, 38, 255)),
        ((72, 8, 205, 38), (12, 16, 34, 255)),
        ((180, 18, 319, 48), (13, 17, 36, 255)),
    ):
        d.rectangle(box, fill=color)
    for x, height in ((4, 35), (18, 49), (34, 38), (282, 44), (300, 55), (314, 40)):
        d.polygon(((x, 115), (x + 9, 115), (x + 4, 115 - height)), fill=(5, 7, 13, 255))
    d.rectangle((54, 151, 242, 158), fill=(20, 20, 30, 255))
    d.rectangle((43, 159, 252, 166), fill=(14, 15, 23, 255))
    d.rectangle((31, 167, 264, 176), fill=(9, 11, 18, 255))
    d.rectangle((65, 72, 231, 151), fill=(24, 24, 36, 255))
    d.rectangle((72, 78, 224, 151), fill=(31, 29, 41, 255))
    d.polygon(((50, 76), (148, 30), (246, 76)), fill=(18, 19, 31, 255))
    d.polygon(((62, 72), (148, 38), (234, 72)), fill=(35, 31, 43, 255))
    d.line(((50, 76), (148, 30), (246, 76)), fill=(54, 48, 62, 255), width=2)
    for x in (78, 104, 192, 218):
        d.rectangle((x, 82, x + 9, 151), fill=(39, 36, 48, 255))
        d.rectangle((x - 2, 79, x + 11, 84), fill=(51, 46, 57, 255))
        d.rectangle((x - 2, 148, x + 11, 153), fill=(18, 19, 29, 255))
    d.rectangle((134, 87, 162, 151), fill=(12, 10, 17, 255))
    d.rectangle((137, 91, 159, 151), fill=(63, 34, 35, 255))
    d.rectangle((140, 94, 156, 151), fill=(86, 45, 39, 255))
    d.rectangle((155, 96, 158, 146), fill=(216, 126, 53, 255))
    for x in (113, 172):
        d.rectangle((x, 96, x + 6, 122), fill=(10, 12, 20, 255))
        d.rectangle((x + 2, 98, x + 4, 119), fill=(116, 83, 55, 255))
    d.rectangle((0, 151, 319, 179), fill=(17, 20, 29, 255))
    d.rectangle((0, 158, 319, 179), fill=(13, 16, 24, 255))
    d.rectangle((0, 166, 319, 179), fill=(9, 12, 19, 255))
    d.polygon(((145, 152), (155, 152), (169, 178), (132, 178)), fill=(72, 47, 35, 80))
    for x, y, width in ((12, 162, 27), (77, 173, 40), (242, 163, 51), (279, 175, 30)):
        d.line((x, y, x + width, y), fill=(42, 58, 78, 170), width=1)
    rng = Random(3319)
    for _ in range(115):
        x = rng.randrange(0, 320)
        y = rng.randrange(0, 178)
        length = rng.choice((3, 4, 5, 6))
        color = rng.choice(((75, 105, 145, 170), (103, 132, 166, 135), (53, 79, 119, 150)))
        d.line((x, y, x - 2, y + length), fill=color, width=1)
    return im


def draw_boot_splash(_bg: Image.Image) -> Image.Image:
    im = Image.new("RGBA", (320, 180), (5, 6, 14, 255))
    d = ImageDraw.Draw(im)
    for x, y in ((12, 18), (48, 8), (92, 28), (141, 12), (188, 25), (236, 10), (284, 30)):
        d.line((x, y, x - 3, y + 8), fill=(45, 62, 90, 130), width=1)
    pixel_text(d, (160, 72), "BENEATH", CREAM, 24, "mm")
    pixel_text(d, (160, 101), "THE PEEL", CREAM, 24, "mm")
    d.rectangle((105, 123, 215, 124), fill=(90, 78, 66, 170))
    d.text((160, 136), "LISTEN CAREFULLY", fill=(98, 109, 132, 255), font=ImageFont.load_default(), anchor="mm")
    return im


def draw_icon() -> Image.Image:
    im=Image.new("RGBA",(128,128),(10,8,18,255)); d=ImageDraw.Draw(im)
    d.ellipse((8,8,119,119),fill=(35,22,42,255),outline=(165,91,114,255),width=4)
    d.ellipse((16,16,111,111),outline=(244,190,49,255),width=3)
    d.arc((30,22,101,103),235,70,fill=INK,width=24)
    d.arc((34,24,98,99),235,70,fill=GOLD,width=17)
    d.arc((40,29,92,92),235,70,fill=GOLD_HI,width=4)
    d.rectangle((91,25,103,36),fill=(74,48,30,255))
    d.rectangle((28,90,39,102),fill=(74,48,30,255))
    return im


def build_all() -> None:
    polish_environment_atlas()
    props=ROOT/"assets/props"
    outputs={
        "sacred_box.png":draw_sacred_box(),
        "security_seal.png":draw_security_seal(),
        "golden_banana_statue.png":draw_golden_statue(),
        "manhole.png":draw_manhole(),
        "ripening_engine.png":draw_engine(),
        "potassium_config_panel.png":draw_potassium_panel(),
        "cult_noticeboard.png":draw_noticeboard(),
        "banana_vending_machine.png":draw_vending_machine(),
        "ritual_drum.png":draw_ritual_drum(),
        "sewer_direction_sign.png":draw_sewer_sign(),
    }
    for name,im in outputs.items(): im.save(props/name)
    ui=ROOT/"assets/ui"
    bg=draw_title_background(); bg.save(ui/"title_menu_bg.png")
    draw_boot_splash(bg).save(ui/"title.png")
    draw_icon().save(ui/"icon.png")
    draw_menu_selector().save(ui/"menu_selector.png")
    print("Generated",len(outputs)+4,"polished art assets")


if __name__ == "__main__":
    build_all()
