extends Node

signal state_changed

const DEFAULT_COUNTERS: Dictionary = {"boxes_delivered": 0, "fuel_loaded": 0, "seals": 0}

var flags: Dictionary = {}
var counters: Dictionary = DEFAULT_COUNTERS.duplicate(true)
var checkpoint_room: String = "temple_exterior"
var checkpoint_position: Array = [160.0, 154.0]


func _ready() -> void:
	reset_game()


func reset_game() -> void:
	flags = {}
	counters = DEFAULT_COUNTERS.duplicate(true)
	checkpoint_room = "temple_exterior"
	checkpoint_position = [160.0, 154.0]
	_commit_state()


func get_flag(key: String, default_value: Variant = false) -> Variant:
	return flags.get(key, default_value)


func set_flag(key: String, value: Variant = true, persist: bool = true) -> void:
	flags[key] = value
	if persist:
		_commit_state()
	else:
		state_changed.emit()


func is_claimed(interaction_id: String) -> bool:
	return bool(flags.get("once:" + interaction_id, false))


func claim_once(interaction_id: String, persist: bool = true) -> bool:
	var key: String = "once:" + interaction_id
	if bool(flags.get(key, false)):
		return false
	flags[key] = true
	if persist:
		_commit_state()
	else:
		state_changed.emit()
	return true


func get_counter(key: String, default_value: int = 0) -> int:
	return int(counters.get(key, default_value))


func set_counter(key: String, value: int, persist: bool = true) -> void:
	counters[key] = value
	if persist:
		_commit_state()
	else:
		state_changed.emit()


func increment_counter(key: String, amount: int = 1, persist: bool = true) -> int:
	var value: int = get_counter(key) + amount
	counters[key] = value
	if persist:
		_commit_state()
	else:
		state_changed.emit()
	return value


func begin_box_delivery(target_index: int) -> bool:
	if bool(flags.get("carrying_box", false)) or get_counter("boxes_delivered") >= 3:
		return false
	flags["carrying_box"] = true
	flags["box_target"] = target_index
	_commit_state()
	return true


func complete_box_delivery(target_index: int) -> int:
	if not bool(flags.get("carrying_box", false)):
		return -1
	if int(flags.get("box_target", -1)) != target_index:
		return -1
	flags["carrying_box"] = false
	flags["box_target"] = -1
	counters["boxes_delivered"] = mini(get_counter("boxes_delivered") + 1, 3)
	_commit_state()
	return get_counter("boxes_delivered")


func complete_fuel_source(source_id: String) -> int:
	var key: String = "once:" + source_id
	if bool(flags.get(key, false)):
		return -1
	flags[key] = true
	counters["fuel_loaded"] = mini(get_counter("fuel_loaded") + 1, 3)
	_commit_state()
	return get_counter("fuel_loaded")


func complete_seal_task(task_id: String, seal_source: String) -> bool:
	var once_key: String = "once:" + task_id
	var seal_key: String = "seal:" + seal_source
	if bool(flags.get(once_key, false)) or bool(flags.get(seal_key, false)):
		return false
	flags[once_key] = true
	flags[seal_key] = true
	counters["seals"] = mini(get_counter("seals") + 1, 3)
	_commit_state()
	return true


func add_seal(source: String) -> bool:
	var seal_key: String = "seal:" + source
	if bool(flags.get(seal_key, false)):
		return false
	flags[seal_key] = true
	counters["seals"] = mini(get_counter("seals") + 1, 3)
	_commit_state()
	return true


func set_checkpoint(room_id: String, world_position: Vector2) -> void:
	# Checkpoints are session-only and support retries without creating save files.
	checkpoint_room = room_id
	checkpoint_position = [world_position.x, world_position.y]
	state_changed.emit()


func get_checkpoint_position() -> Vector2:
	if checkpoint_position.size() >= 2:
		return Vector2(float(checkpoint_position[0]), float(checkpoint_position[1]))
	return Vector2(160.0, 154.0)


func _commit_state() -> void:
	state_changed.emit()
