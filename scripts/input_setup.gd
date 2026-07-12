extends RefCounted


static func ensure_default_actions() -> void:
	_add_key_action("move_left", [KEY_A, KEY_LEFT], 0.35)
	_add_key_action("move_right", [KEY_D, KEY_RIGHT], 0.35)
	_add_key_action("move_up", [KEY_W, KEY_UP], 0.35)
	_add_key_action("move_down", [KEY_S, KEY_DOWN], 0.35)
	_add_key_action("interact", [KEY_E, KEY_SPACE, KEY_ENTER], 0.25)
	_add_key_action("sprint", [KEY_SHIFT], 0.25)
	_add_key_action("pause", [KEY_ESCAPE], 0.25)
	_add_key_action("debug_collision", [KEY_F3], 0.25)


static func _add_key_action(action_name: StringName, keys: Array, deadzone: float) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name, deadzone)
	if not InputMap.action_get_events(action_name).is_empty():
		return
	for keycode in keys:
		var event := InputEventKey.new()
		event.physical_keycode = int(keycode)
		InputMap.action_add_event(action_name, event)
