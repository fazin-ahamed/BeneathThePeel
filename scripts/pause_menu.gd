class_name PauseMenu
extends CanvasLayer

signal resume_requested
signal title_requested

@onready var resume_button: Button = %ResumeButton


func _ready() -> void:
	layer = 90
	process_mode = Node.PROCESS_MODE_ALWAYS
	%ResumeButton.pressed.connect(resume_requested.emit)
	%TitleButton.pressed.connect(title_requested.emit)
	resume_button.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		resume_requested.emit()
		get_viewport().set_input_as_handled()
