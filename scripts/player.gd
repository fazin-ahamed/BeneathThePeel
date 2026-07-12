extends CharacterBody2D

signal footstep

const FRAME_SIZE := Vector2(16, 16)
const SHEETS := {
	"normal": "res://assets/characters/player_sheet.png",
	"robed": "res://assets/characters/player_robed_sheet.png",
	"banana": "res://assets/characters/banana_sheet.png"
}

var input_enabled: bool = true
var base_speed: float = 52.0
var sprint_multiplier: float = 1.35
var world_bounds: Rect2 = Rect2(8, 8, 304, 164)
var costume: String = "normal"
var carrying: bool = false
var facing_row: int = 0
var animation_frame: int = 0
var animation_time: float = 0.0
var forced_velocity: Vector2 = Vector2.ZERO
var use_forced_velocity: bool = false

var sprite: Sprite2D
var shadow: Sprite2D
var carry_sprite: Sprite2D
var camera: Camera2D


func _ready() -> void:
	z_as_relative = false
	z_index = 100

	_build_visuals()
	_build_collision()
	_build_camera()
	set_costume(costume)
	set_carrying(carrying)


func _build_visuals() -> void:
	shadow = Sprite2D.new()
	shadow.name = "Shadow"
	shadow.texture = load("res://assets/props/shadow.png")
	shadow.position = Vector2(0, 7)
	shadow.z_index = -1
	shadow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(shadow)

	sprite = Sprite2D.new()
	sprite.name = "Sprite"
	sprite.region_enabled = true
	sprite.region_rect = Rect2(Vector2.ZERO, FRAME_SIZE)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)

	carry_sprite = Sprite2D.new()
	carry_sprite.name = "CarriedBox"
	carry_sprite.texture = load("res://assets/props/sacred_box.png")
	carry_sprite.position = Vector2(0, -13)
	carry_sprite.z_index = 1
	carry_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(carry_sprite)


func _build_collision() -> void:
	var collision := CollisionShape2D.new()
	collision.name = "Collision"
	var shape := RectangleShape2D.new()
	shape.size = Vector2(8, 8)
	collision.shape = shape
	collision.position = Vector2(0, 4)
	add_child(collision)


func _build_camera() -> void:
	camera = Camera2D.new()
	camera.name = "Camera"
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 7.0
	camera.limit_smoothed = true
	camera.enabled = true
	add_child(camera)
	update_camera_limits(Vector2(320, 180))


func update_camera_limits(world_size: Vector2) -> void:
	if not is_instance_valid(camera):
		return
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = int(world_size.x)
	camera.limit_bottom = int(world_size.y)


func set_costume(value: String) -> void:
	costume = value if SHEETS.has(value) else "normal"
	if is_instance_valid(sprite):
		sprite.texture = load(SHEETS[costume])
		_update_sprite_region()


func set_carrying(value: bool) -> void:
	carrying = value
	if is_instance_valid(carry_sprite):
		carry_sprite.visible = carrying


func set_world_bounds(value: Rect2) -> void:
	world_bounds = value


func set_facing(row: int) -> void:
	facing_row = clampi(row, 0, 3)
	animation_frame = 0
	_update_sprite_region()


func set_pose(row: int, frame: int = 0, angle: float = 0.0) -> void:
	facing_row = clampi(row, 0, 3)
	animation_frame = clampi(frame, 0, 3)
	sprite.rotation = angle
	_update_sprite_region()


func clear_pose_rotation() -> void:
	if is_instance_valid(sprite):
		sprite.rotation = 0.0


func _physics_process(delta: float) -> void:
	var movement := Vector2.ZERO
	if use_forced_velocity:
		movement = forced_velocity
	elif input_enabled:
		movement = Input.get_vector("move_left", "move_right", "move_up", "move_down")
		if movement.length_squared() > 1.0:
			movement = movement.normalized()

	var speed := base_speed
	if input_enabled and Input.is_action_pressed("sprint"):
		speed *= sprint_multiplier
	velocity = movement * speed
	move_and_slide()

	var half := Vector2(5, 6)
	position.x = clampf(position.x, world_bounds.position.x + half.x, world_bounds.end.x - half.x)
	position.y = clampf(position.y, world_bounds.position.y + half.y, world_bounds.end.y - half.y)

	if movement.length_squared() > 0.01:
		_update_facing_from_vector(movement)
		animation_time += delta
		if animation_time >= 0.12:
			animation_time = 0.0
			animation_frame = (animation_frame + 1) % 4
			if animation_frame == 1 or animation_frame == 3:
				footstep.emit()
	else:
		animation_frame = 0
		animation_time = 0.0
	_update_sprite_region()


func _update_facing_from_vector(direction: Vector2) -> void:
	if absf(direction.x) > absf(direction.y):
		facing_row = 2 if direction.x > 0.0 else 1
	else:
		facing_row = 0 if direction.y > 0.0 else 3


func _update_sprite_region() -> void:
	if not is_instance_valid(sprite):
		return
	sprite.region_rect = Rect2(Vector2(animation_frame * 16, facing_row * 16), FRAME_SIZE)
