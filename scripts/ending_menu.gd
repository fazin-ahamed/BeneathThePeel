class_name EndingMenu
extends CanvasLayer

signal replay_requested
signal title_requested

@onready var replay_button: Button = %ReplayButton


func _ready() -> void:
	layer = 70
	process_mode = Node.PROCESS_MODE_ALWAYS
	%ReplayButton.pressed.connect(replay_requested.emit)
	%TitleButton.pressed.connect(title_requested.emit)
	replay_button.grab_focus()
