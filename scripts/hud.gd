extends CanvasLayer

const QuestIndicatorScene = preload("res://scenes/ui/quest_indicator.tscn")

var objective_bg: ColorRect
var objective_label: Label
var prompt_bg: ColorRect
var prompt_label: Label
var seal_bg: ColorRect
var seal_label: Label
var seal_icons: Array[TextureRect] = []
var notification_bg: ColorRect
var notification_label: Label
var room_label: Label
var quest_indicator: QuestIndicator


func _ready() -> void:
	layer = 20
	_build_objective()
	_build_prompt()
	_build_seals()
	_build_notification()
	_build_room_label()
	_build_quest_indicator()
	set_prompt("")
	set_objective("")
	update_seals(0)


func _make_label(font_size: int = 8) -> Label:
	var label := Label.new()
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color(0.95, 0.91, 0.78))
	label.add_theme_color_override("font_outline_color", Color(0.04, 0.03, 0.07))
	label.add_theme_constant_override("outline_size", 2)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


func _build_objective() -> void:
	objective_bg = ColorRect.new()
	objective_bg.position = Vector2(5, 5)
	objective_bg.size = Vector2(216, 25)
	objective_bg.color = Color(0.035, 0.025, 0.06, 0.86)
	objective_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(objective_bg)
	objective_label = _make_label(8)
	objective_label.position = Vector2(7, 4)
	objective_label.size = Vector2(204, 19)
	objective_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	objective_bg.add_child(objective_label)


func _build_prompt() -> void:
	prompt_bg = ColorRect.new()
	prompt_bg.position = Vector2(68, 156)
	prompt_bg.size = Vector2(184, 19)
	prompt_bg.color = Color(0.04, 0.025, 0.065, 0.92)
	prompt_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(prompt_bg)
	prompt_label = _make_label(8)
	prompt_label.position = Vector2(3, 2)
	prompt_label.size = Vector2(178, 15)
	prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt_bg.add_child(prompt_label)


func _build_seals() -> void:
	seal_bg = ColorRect.new()
	seal_bg.position = Vector2(230, 5)
	seal_bg.size = Vector2(85, 25)
	seal_bg.color = Color(0.035, 0.025, 0.06, 0.86)
	seal_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(seal_bg)

	seal_label = _make_label(7)
	seal_label.position = Vector2(5, 5)
	seal_label.size = Vector2(30, 15)
	seal_label.text = "SEALS"
	seal_bg.add_child(seal_label)

	for index in range(3):
		var icon := TextureRect.new()
		icon.texture = load("res://assets/props/security_seal.png")
		icon.position = Vector2(36 + index * 15, 6)
		icon.size = Vector2(12, 12)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		seal_bg.add_child(icon)
		seal_icons.append(icon)


func _build_notification() -> void:
	notification_bg = ColorRect.new()
	notification_bg.position = Vector2(48, 44)
	notification_bg.size = Vector2(224, 27)
	notification_bg.color = Color(0.12, 0.05, 0.10, 0.94)
	notification_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	notification_bg.visible = false
	add_child(notification_bg)
	notification_label = _make_label(9)
	notification_label.position = Vector2(4, 5)
	notification_label.size = Vector2(216, 18)
	notification_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	notification_bg.add_child(notification_label)


func _build_room_label() -> void:
	room_label = _make_label(8)
	room_label.position = Vector2(8, 34)
	room_label.size = Vector2(304, 14)
	room_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	room_label.modulate.a = 0.0
	add_child(room_label)


func _build_quest_indicator() -> void:
	quest_indicator = QuestIndicatorScene.instantiate() as QuestIndicator
	add_child(quest_indicator)


func set_objective(text: String) -> void:
	objective_label.text = "OBJECTIVE  " + text
	objective_bg.visible = not text.is_empty()


func set_prompt(text: String) -> void:
	prompt_label.text = "[E]  " + text
	prompt_bg.visible = not text.is_empty()


func set_quest_target(world_position: Vector2, player_node: Node2D, label: String = "") -> void:
	if is_instance_valid(quest_indicator):
		quest_indicator.set_target(world_position, player_node, label)


func clear_quest_target() -> void:
	if is_instance_valid(quest_indicator):
		quest_indicator.clear_target()


func update_seals(count: int) -> void:
	for index in range(seal_icons.size()):
		var earned: bool = index < count
		seal_icons[index].modulate = (
			Color(1.0, 0.92, 0.55, 1.0) if earned else Color(0.28, 0.30, 0.36, 0.42)
		)
	seal_bg.visible = count > 0 or bool(GameState.get_flag("robed", false))


func show_notification(text: String, duration: float = 1.8) -> void:
	notification_label.text = text
	notification_bg.visible = true
	notification_bg.modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(notification_bg, "modulate:a", 1.0, 0.12)
	tween.tween_interval(duration)
	tween.tween_property(notification_bg, "modulate:a", 0.0, 0.3)
	tween.tween_callback(func() -> void: notification_bg.visible = false)


func show_room_title(text: String) -> void:
	room_label.text = text
	room_label.modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(room_label, "modulate:a", 1.0, 0.25)
	tween.tween_interval(1.4)
	tween.tween_property(room_label, "modulate:a", 0.0, 0.55)
