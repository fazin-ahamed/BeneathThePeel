extends Control

var drops: Array[Dictionary] = []
var rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	rng.seed = 19019
	for index in range(72):
		drops.append(_new_drop(float(index) / 72.0))
	queue_redraw()


func _new_drop(normalized_y: float = 0.0) -> Dictionary:
	return {
		"position": Vector2(rng.randf_range(0.0, 320.0), normalized_y * 180.0),
		"speed": rng.randf_range(48.0, 96.0),
		"length": rng.randf_range(3.0, 7.0),
		"alpha": rng.randf_range(0.16, 0.42),
	}


func _process(delta: float) -> void:
	for drop in drops:
		var position_value: Vector2 = drop.get("position", Vector2.ZERO)
		position_value += Vector2(-18.0, float(drop.get("speed", 64.0))) * delta
		if position_value.y > size.y + 8.0:
			position_value.y = -8.0
			position_value.x = rng.randf_range(0.0, maxf(1.0, size.x))
		if position_value.x < -8.0:
			position_value.x = size.x + 8.0
		drop["position"] = position_value
	queue_redraw()


func _draw() -> void:
	for drop in drops:
		var position_value: Vector2 = drop.get("position", Vector2.ZERO)
		var length_value: float = float(drop.get("length", 4.0))
		var alpha_value: float = float(drop.get("alpha", 0.25))
		draw_line(
			position_value,
			position_value + Vector2(-2.0, length_value),
			Color(0.45, 0.62, 0.84, alpha_value),
			1.0
		)
