class_name QuestIndicator
extends Control

var target_world_position: Vector2 = Vector2.ZERO
var target_player: Node2D = null
var target_label: String = ""
var has_target: bool = false
var pulse_time: float = 0.0

const GOLD := Color(1.0, 0.78, 0.22, 1.0)
const GOLD_SOFT := Color(1.0, 0.78, 0.22, 0.22)
const EDGE_MARGIN := Vector2(15.0, 18.0)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false


func set_target(world_position: Vector2, player_node: Node2D, label: String = "") -> void:
	target_world_position = world_position
	target_player = player_node
	target_label = label
	has_target = true
	visible = true
	queue_redraw()


func clear_target() -> void:
	has_target = false
	target_player = null
	target_label = ""
	visible = false
	queue_redraw()


func _process(delta: float) -> void:
	if not has_target or not is_instance_valid(target_player):
		visible = false
		return
	visible = true
	pulse_time += delta
	queue_redraw()


func _draw() -> void:
	if not has_target or not is_instance_valid(target_player):
		return
	var viewport_size: Vector2 = get_viewport_rect().size
	var canvas_transform: Transform2D = get_viewport().get_canvas_transform()
	var target_screen: Vector2 = canvas_transform * target_world_position
	var safe_rect := Rect2(
		Vector2(EDGE_MARGIN.x, 35.0),
		Vector2(viewport_size.x - EDGE_MARGIN.x * 2.0, viewport_size.y - 55.0)
	)
	var pulse: float = (sin(pulse_time * 5.5) + 1.0) * 0.5
	if safe_rect.has_point(target_screen):
		_draw_world_marker(target_screen, pulse)
	else:
		_draw_edge_arrow(target_screen, viewport_size, safe_rect, pulse)


func _draw_world_marker(screen_position: Vector2, pulse: float) -> void:
	var bob: float = sin(pulse_time * 5.5) * 2.0
	var point := screen_position + Vector2(0.0, -15.0 + bob)
	draw_circle(point, 7.0 + pulse * 2.0, GOLD_SOFT, false, 1.0)
	var diamond := PackedVector2Array(
		[
			point + Vector2(0.0, -5.0),
			point + Vector2(5.0, 0.0),
			point + Vector2(0.0, 5.0),
			point + Vector2(-5.0, 0.0),
		]
	)
	draw_colored_polygon(diamond, GOLD)
	draw_line(point + Vector2(0.0, 6.0), screen_position + Vector2(0.0, -7.0), GOLD, 1.0)


func _draw_edge_arrow(target_screen: Vector2, viewport_size: Vector2, safe_rect: Rect2, pulse: float) -> void:
	var center := viewport_size * 0.5
	var direction := (target_screen - center).normalized()
	if direction.length_squared() < 0.01:
		direction = Vector2.UP
	var point := Vector2(
		clampf(target_screen.x, safe_rect.position.x, safe_rect.end.x),
		clampf(target_screen.y, safe_rect.position.y, safe_rect.end.y)
	)
	var angle := direction.angle()
	var size: float = 6.0 + pulse
	var forward := Vector2.RIGHT.rotated(angle)
	var side := Vector2.DOWN.rotated(angle)
	var arrow := PackedVector2Array(
		[
			point + forward * size,
			point - forward * size * 0.65 + side * size * 0.65,
			point - forward * size * 0.65 - side * size * 0.65,
		]
	)
	draw_circle(point, 9.0 + pulse * 2.0, GOLD_SOFT, false, 1.0)
	draw_colored_polygon(arrow, GOLD)
