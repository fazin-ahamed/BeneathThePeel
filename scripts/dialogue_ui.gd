extends CanvasLayer

signal finished(choice: Variant)

const PORTRAITS: Dictionary = {
	"player": {"path": "res://assets/characters/player_sheet.png", "size": 16.0, "scale": 2.6},
	"player_robed":
	{"path": "res://assets/characters/player_robed_sheet.png", "size": 16.0, "scale": 2.6},
	"cultist": {"path": "res://assets/characters/cultist_sheet.png", "size": 16.0, "scale": 2.6},
	"guard": {"path": "res://assets/characters/guard_sheet.png", "size": 16.0, "scale": 2.6},
	"leader": {"path": "res://assets/characters/cult_leader_sheet.png", "size": 16.0, "scale": 2.6},
	"cavendish":
	{"path": "res://assets/characters/cavendish_sheet.png", "size": 16.0, "scale": 2.6},
	"banana": {"path": "res://assets/characters/banana_sheet.png", "size": 16.0, "scale": 2.6},
	"narrator":
	{"path": "res://assets/characters/narrator_detective.png", "size": 32.0, "scale": 1.45}
}

var panel: ColorRect
var speaker_label: Label
var body_label: Label
var choices_label: Label
var continue_label: Label
var portrait: Sprite2D

var lines: Array = []
var line_index: int = 0
var choices: Array = []
var choice_index: int = 0
var last_choice: Variant = null
var is_open: bool = false
var input_armed: bool = false
var characters_shown: float = 0.0
var type_speed: float = 46.0
var tick_accumulator: int = 0


func _ready() -> void:
	layer = 40
	_build_ui()
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS


func _make_label(font_size: int) -> Label:
	var label := Label.new()
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color(0.96, 0.92, 0.82))
	label.add_theme_color_override("font_outline_color", Color(0.03, 0.02, 0.05))
	label.add_theme_constant_override("outline_size", 2)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


func _build_ui() -> void:
	panel = ColorRect.new()
	panel.position = Vector2(7, 96)
	panel.size = Vector2(306, 77)
	panel.color = Color(0.035, 0.022, 0.055, 0.98)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(panel)

	var top_line := ColorRect.new()
	top_line.position = Vector2.ZERO
	top_line.size = Vector2(306, 2)
	top_line.color = Color(0.73, 0.37, 0.35)
	top_line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(top_line)

	speaker_label = _make_label(9)
	speaker_label.position = Vector2(48, 5)
	speaker_label.size = Vector2(248, 14)
	speaker_label.add_theme_color_override("font_color", Color(1.0, 0.78, 0.24))
	panel.add_child(speaker_label)

	body_label = _make_label(9)
	body_label.position = Vector2(48, 19)
	body_label.size = Vector2(249, 42)
	body_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	panel.add_child(body_label)

	choices_label = _make_label(8)
	choices_label.position = Vector2(48, 43)
	choices_label.size = Vector2(245, 31)
	choices_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	choices_label.visible = false
	panel.add_child(choices_label)

	continue_label = _make_label(8)
	continue_label.text = "[E]"
	continue_label.position = Vector2(287, 61)
	continue_label.size = Vector2(12, 12)
	continue_label.visible = false
	panel.add_child(continue_label)

	portrait = Sprite2D.new()
	portrait.position = Vector2(30, 136)
	portrait.scale = Vector2(2.6, 2.6)
	portrait.region_enabled = true
	portrait.region_rect = Rect2(0, 0, 16, 16)
	portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(portrait)


func play(new_lines: Array) -> Variant:
	if new_lines.is_empty():
		return null
	while is_open:
		await finished
	lines = new_lines.duplicate(true)
	line_index = 0
	last_choice = null
	is_open = true
	input_armed = false
	visible = true
	_show_current_line()
	var result: Variant = await finished
	return result


func _process(delta: float) -> void:
	if not is_open:
		return

	if not input_armed:
		if not Input.is_action_pressed("interact") and not Input.is_action_pressed("ui_accept"):
			input_armed = true

	if body_label.visible_characters < body_label.text.length():
		if input_armed and _advance_pressed():
			body_label.visible_characters = body_label.text.length()
			characters_shown = float(body_label.text.length())
			input_armed = false
			_refresh_choices()
			return
		characters_shown += type_speed * delta
		var new_count := mini(int(characters_shown), body_label.text.length())
		if new_count > body_label.visible_characters:
			tick_accumulator += new_count - body_label.visible_characters
			body_label.visible_characters = new_count
			if tick_accumulator >= 3:
				tick_accumulator = 0
				AudioManager.play_sfx(
					"res://assets/audio/dialogue_tick.wav", -18.0, randf_range(0.94, 1.06)
				)
		if body_label.visible_characters >= body_label.text.length():
			_refresh_choices()
		return

	if not input_armed:
		return

	if not choices.is_empty():
		if Input.is_action_just_pressed("move_up"):
			choice_index = wrapi(choice_index - 1, 0, choices.size())
			_refresh_choices()
		elif Input.is_action_just_pressed("move_down"):
			choice_index = wrapi(choice_index + 1, 0, choices.size())
			_refresh_choices()

	if _advance_pressed():
		input_armed = false
		if not choices.is_empty():
			var selected: Dictionary = choices[choice_index]
			last_choice = selected.get("value", choice_index)
		_advance()


func _advance_pressed() -> bool:
	return Input.is_action_just_pressed("interact") or Input.is_action_just_pressed("ui_accept")


func _show_current_line() -> void:
	var line: Dictionary = lines[line_index]
	speaker_label.text = str(line.get("speaker", ""))
	body_label.text = str(line.get("text", ""))
	body_label.visible_characters = 0
	characters_shown = 0.0
	tick_accumulator = 0
	choices = line.get("choices", [])
	choice_index = 0
	choices_label.visible = false
	continue_label.visible = false
	body_label.size.y = 23.0 if not choices.is_empty() else 42.0
	_set_portrait(str(line.get("portrait", "")))
	input_armed = false


func _set_portrait(kind: String) -> void:
	if kind.is_empty() or not PORTRAITS.has(kind):
		portrait.visible = false
		body_label.position.x = 12
		body_label.size.x = 285
		speaker_label.position.x = 12
		choices_label.position.x = 12
		choices_label.size.x = 281
		return
	portrait.visible = true
	var portrait_info: Dictionary = PORTRAITS[kind]
	portrait.texture = load(str(portrait_info.get("path", "")))
	var region_size: float = float(portrait_info.get("size", 16.0))
	var portrait_scale: float = float(portrait_info.get("scale", 2.6))
	portrait.region_rect = Rect2(0.0, 0.0, region_size, region_size)
	portrait.scale = Vector2.ONE * portrait_scale
	body_label.position.x = 48
	body_label.size.x = 249
	speaker_label.position.x = 48
	choices_label.position.x = 48
	choices_label.size.x = 245


func _refresh_choices() -> void:
	if choices.is_empty():
		choices_label.visible = false
		continue_label.visible = true
		return
	var text := ""
	for index in range(choices.size()):
		var item: Dictionary = choices[index]
		text += ("> " if index == choice_index else "  ") + str(item.get("text", "...")
)
		if index < choices.size() - 1:
			text += "\n"
	choices_label.text = text
	choices_label.visible = true
	continue_label.visible = false


func _advance() -> void:
	line_index += 1
	if line_index >= lines.size():
		_close()
		return
	_show_current_line()


func _close() -> void:
	is_open = false
	visible = false
	input_armed = false
	choices.clear()
	finished.emit(last_choice)
