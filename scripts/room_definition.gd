@tool
class_name RoomDefinition
extends Node2D

@export var room_id: String = ""
@export var room_title: String = ""
@export var world_size: Vector2 = Vector2(320, 192)
@export var player_bounds: Rect2 = Rect2(8, 8, 304, 176)
@export_file("*.wav") var music_path: String = ""
@export_range(-40.0, 0.0, 0.5) var music_volume: float = -13.0
@export_file("*.wav") var ambient_path: String = ""
@export_range(-40.0, 0.0, 0.5) var ambient_volume: float = -18.0
@export_enum("none", "rain", "dust", "sewer", "sparks", "dawn", "alarm") var fx_mode: String = "none"
@export_multiline var default_objective: String = ""


func spawn_position(spawn_name: StringName = &"Default") -> Vector2:
	var path := NodePath("SpawnPoints/" + String(spawn_name))
	var marker := get_node_or_null(path) as Marker2D
	if marker != null:
		return marker.position
	var fallback := get_node_or_null("SpawnPoints/Default") as Marker2D
	return fallback.position if fallback != null else world_size * 0.5


func default_spawn_position() -> Vector2:
	return spawn_position(&"Default")


func actor_parent() -> Node2D:
	var actors := get_node_or_null("Actors") as Node2D
	return actors if actors != null else self


func collision_map() -> TileMapLayer:
	return get_node_or_null("Tilemaps/CollisionMap") as TileMapLayer


func set_collision_debug_visible(enabled: bool) -> void:
	var map := collision_map()
	if map != null:
		map.visible = enabled


func collision_debug_visible() -> bool:
	var map := collision_map()
	return map.visible if map != null else false


func to_runtime_data() -> Dictionary:
	return {
		"id": room_id,
		"title": room_title,
		"world_size": world_size,
		"bounds": player_bounds,
		"music": music_path,
		"music_volume": music_volume,
		"ambient": ambient_path,
		"ambient_volume": ambient_volume,
		"fx": fx_mode,
		"objective": default_objective,
	}
