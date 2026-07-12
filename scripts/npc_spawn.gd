@tool
class_name NPCSpawnPoint
extends Marker2D

@export_enum("cultist", "guard", "cavendish", "leader") var kind: String = "cultist"
@export_range(0, 3, 1) var facing: int = 0
@export var animated: bool = true
