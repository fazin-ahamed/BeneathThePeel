extends CharacterBody2D

signal caught_player
signal slipped

var target: CharacterBody2D
var move_speed: float = 44.0
var active: bool = true
var slip_time: float = 0.0
var facing_row: int = 2
var animation_frame: int = 0
var animation_time: float = 0.0
var capture_emitted: bool = false

var sprite: Sprite2D
var shadow: Sprite2D
var capture_area: Area2D


func _ready() -> void:
	z_index = 4
	shadow = Sprite2D.new()
	shadow.texture = load("res://assets/props/shadow.png")
	shadow.position = Vector2(0, 7)
	shadow.z_index = -1
	shadow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(shadow)

	sprite = Sprite2D.new()
	sprite.texture = load("res://assets/characters/guard_sheet.png")
	sprite.region_enabled = true
	sprite.region_rect = Rect2(0, facing_row * 16, 16, 16)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(sprite)

	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(8, 8)
	collision.shape = shape
	collision.position = Vector2(0, 4)
	add_child(collision)

	capture_area = Area2D.new()
	capture_area.name = "CaptureArea"
	capture_area.position = Vector2(0, 4)
	capture_area.collision_layer = 0
	capture_area.collision_mask = 1
	capture_area.monitoring = true
	capture_area.monitorable = false
	var capture_shape := CollisionShape2D.new()
	var capture_circle := CircleShape2D.new()
	capture_circle.radius = 10.5
	capture_shape.shape = capture_circle
	capture_area.add_child(capture_shape)
	add_child(capture_area)
	capture_area.body_entered.connect(_on_capture_body_entered)


func _physics_process(delta: float) -> void:
	if slip_time > 0.0:
		slip_time -= delta
		velocity = velocity.move_toward(Vector2.ZERO, 180.0 * delta)
		move_and_slide()
		if slip_time <= 0.0 and is_instance_valid(sprite):
			sprite.rotation = 0.0
		return

	if not active or capture_emitted or not is_instance_valid(target):
		velocity = Vector2.ZERO
		return

	var direction: Vector2 = target.global_position - global_position
	if direction.length_squared() <= 144.0:
		_capture_target()
		return
	direction = direction.normalized()
	velocity = direction * move_speed
	move_and_slide()
	_update_facing(direction)
	animation_time += delta
	if animation_time >= 0.1:
		animation_time = 0.0
		animation_frame = (animation_frame + 1) % 4
	_update_region()


func _on_capture_body_entered(body: Node2D) -> void:
	if body == target:
		_capture_target()


func _capture_target() -> void:
	if capture_emitted or not active or slip_time > 0.0:
		return
	capture_emitted = true
	active = false
	velocity = Vector2.ZERO
	caught_player.emit()


func make_slip() -> void:
	if slip_time > 0.0 or capture_emitted:
		return
	slip_time = 1.25
	velocity *= 1.5
	if is_instance_valid(sprite):
		sprite.rotation = PI * 0.5
	slipped.emit()


func _update_facing(direction: Vector2) -> void:
	if absf(direction.x) > absf(direction.y):
		facing_row = 2 if direction.x > 0.0 else 1
	else:
		facing_row = 0 if direction.y > 0.0 else 3


func _update_region() -> void:
	if is_instance_valid(sprite):
		sprite.region_rect = Rect2(animation_frame * 16, facing_row * 16, 16, 16)
