extends Node2D

const SHEETS := {
	"cultist": "res://assets/characters/cultist_sheet.png",
	"guard": "res://assets/characters/guard_sheet.png",
	"cavendish": "res://assets/characters/cavendish_sheet.png",
	"leader": "res://assets/characters/cult_leader_sheet.png"
}

var kind: String = "cultist"
var facing_row: int = 0
var animated: bool = true
var animation_time: float = 0.0
var animation_frame: int = 0
var sprite: Sprite2D
var shadow: Sprite2D


func _ready() -> void:
	z_index = 4
	shadow = Sprite2D.new()
	shadow.texture = load("res://assets/props/shadow.png")
	shadow.position = Vector2(0, 7)
	shadow.z_index = -1
	shadow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(shadow)

	sprite = Sprite2D.new()
	sprite.region_enabled = true
	sprite.region_rect = Rect2(0, facing_row * 16, 16, 16)
	sprite.texture = load(SHEETS.get(kind, SHEETS["cultist"]))
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)


func configure(data: Dictionary) -> void:
	kind = str(data.get("kind", "cultist"))
	facing_row = int(data.get("facing", 0))
	animated = bool(data.get("animated", true))


func set_facing(row: int) -> void:
	facing_row = clampi(row, 0, 3)
	_update_region()


func _process(delta: float) -> void:
	if not animated or not is_instance_valid(sprite):
		return
	animation_time += delta
	if animation_time >= 0.55:
		animation_time = 0.0
		animation_frame = 0 if animation_frame == 1 else 1
		_update_region()


func _update_region() -> void:
	if is_instance_valid(sprite):
		sprite.region_rect = Rect2(animation_frame * 16, facing_row * 16, 16, 16)
