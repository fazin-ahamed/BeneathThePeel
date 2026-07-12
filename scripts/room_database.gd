extends RefCounted

const ROOM_SCENES: Dictionary = {
	"temple_exterior": "res://scenes/rooms/temple_exterior.tscn",
	"temple_interior": "res://scenes/rooms/temple_interior.tscn",
	"street": "res://scenes/rooms/street.tscn",
	"sewer_explore": "res://scenes/rooms/sewer_explore.tscn",
	"cult_lobby": "res://scenes/rooms/cult_lobby.tscn",
	"cult_hq": "res://scenes/rooms/cult_hq.tscn",
	"storage": "res://scenes/rooms/storage.tscn",
	"statue_room": "res://scenes/rooms/statue_room.tscn",
	"engine_room": "res://scenes/rooms/engine_room.tscn",
	"quarters": "res://scenes/rooms/quarters.tscn",
	"chase": "res://scenes/rooms/chase.tscn",
	"surface_ending": "res://scenes/rooms/surface_ending.tscn",
}


static func scene_path(room_id: String) -> String:
	return str(ROOM_SCENES.get(room_id, ""))


static func has_room(room_id: String) -> bool:
	return ROOM_SCENES.has(room_id)


static func get_room(room_id: String) -> Dictionary:
	var path := scene_path(room_id)
	return {} if path.is_empty() else {"id": room_id, "scene": path}


static func room_ids() -> Array[String]:
	var ids: Array[String] = []
	for key in ROOM_SCENES.keys():
		ids.append(str(key))
	return ids
