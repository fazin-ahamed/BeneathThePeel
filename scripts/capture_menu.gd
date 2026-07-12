class_name CaptureMenu
extends CanvasLayer

signal retry_requested
signal title_requested

@onready var panel: PanelContainer = %Panel
@onready var retry_button: Button = %RetryButton
@onready var title_button: Button = %TitleButton


func _ready() -> void:
	layer = 75
	process_mode = Node.PROCESS_MODE_ALWAYS
	retry_button.pressed.connect(retry_requested.emit)
	title_button.pressed.connect(title_requested.emit)
	retry_button.grab_focus()
	panel.modulate.a = 0.0
	panel.scale = Vector2(0.96, 0.96)
	panel.pivot_offset = panel.size * 0.5
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(panel, "modulate:a", 1.0, 0.18)
	tween.tween_property(panel, "scale", Vector2.ONE, 0.18)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		title_requested.emit()
		get_viewport().set_input_as_handled()
