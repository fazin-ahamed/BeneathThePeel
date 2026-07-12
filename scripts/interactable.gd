extends Node2D

signal activated(event_name: String, source: Node)

var interaction_id: String = ""
var event_name: String = ""
var prompt: String = "Interact"
var radius: float = 20.0
var one_shot: bool = false
var disabled: bool = false


func configure(data: Dictionary) -> void:
	interaction_id = str(data.get("id", ""))
	event_name = str(data.get("event", ""))
	prompt = str(data.get("prompt", "Interact"))
	radius = float(data.get("radius", 20.0))
	one_shot = bool(data.get("one_shot", false))
	position = data.get("pos", Vector2.ZERO)


func is_available() -> bool:
	if disabled:
		return false
	if one_shot and GameState.is_claimed(interaction_id):
		return false
	return true


func try_activate() -> bool:
	if not is_available():
		return false
	if one_shot:
		disabled = true
	activated.emit(event_name, self)
	return true


func disable() -> void:
	disabled = true


func enable() -> void:
	disabled = false


func set_prompt(value: String) -> void:
	prompt = value
