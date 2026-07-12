@tool
class_name InteractionPoint
extends Marker2D

@export var interaction_id: String = ""
@export var event_name: String = ""
@export_multiline var prompt: String = "Interact"
@export_range(4.0, 64.0, 1.0) var radius: float = 20.0
@export var one_shot: bool = false
