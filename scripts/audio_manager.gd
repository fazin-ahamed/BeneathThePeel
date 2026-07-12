extends Node

var _music_players: Array[AudioStreamPlayer] = []
var _active_music: int = 0
var _music_path: String = ""
var _ambient_player: AudioStreamPlayer
var _ambient_path: String = ""


func _ready() -> void:
	for index in range(2):
		var player := AudioStreamPlayer.new()
		player.name = "Music" + str(index)
		player.volume_db = -60.0
		add_child(player)
		player.finished.connect(_on_music_finished.bind(index))
		_music_players.append(player)
	_ambient_player = AudioStreamPlayer.new()
	_ambient_player.name = "Ambient"
	_ambient_player.volume_db = -18.0
	add_child(_ambient_player)
	_ambient_player.finished.connect(_on_ambient_finished)


func play_music(path: String, volume_db: float = -13.0, fade_seconds: float = 0.65) -> void:
	if path.is_empty():
		stop_music(fade_seconds)
		return
	if _music_path == path and _music_players[_active_music].playing:
		return
	var stream := load(path)
	if stream == null:
		push_warning("Missing music stream: " + path)
		return
	var old_index := _active_music
	var next_index := 1 - old_index
	var old_player := _music_players[old_index]
	var next_player := _music_players[next_index]
	next_player.stop()
	next_player.stream = stream
	next_player.volume_db = -60.0
	next_player.play()
	_music_path = path
	_active_music = next_index
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(next_player, "volume_db", volume_db, max(0.05, fade_seconds))
	if old_player.playing:
		tween.tween_property(old_player, "volume_db", -60.0, max(0.05, fade_seconds))
	tween.set_parallel(false)
	tween.tween_callback(
		func() -> void:
			if old_index != _active_music:
				old_player.stop()
	)


func stop_music(fade_seconds: float = 0.4) -> void:
	_music_path = ""
	for player in _music_players:
		if player.playing:
			var tween := create_tween()
			tween.tween_property(player, "volume_db", -60.0, max(0.05, fade_seconds))
			tween.tween_callback(player.stop)


func play_ambient(path: String, volume_db: float = -18.0) -> void:
	if path.is_empty():
		stop_ambient()
		return
	if _ambient_path == path and _ambient_player.playing:
		_ambient_player.volume_db = volume_db
		return
	var stream := load(path)
	if stream == null:
		push_warning("Missing ambient stream: " + path)
		return
	_ambient_path = path
	_ambient_player.stop()
	_ambient_player.stream = stream
	_ambient_player.volume_db = volume_db
	_ambient_player.play()


func stop_ambient() -> void:
	_ambient_path = ""
	if is_instance_valid(_ambient_player):
		_ambient_player.stop()


func play_sfx(path: String, volume_db: float = -5.0, pitch_scale: float = 1.0) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	add_child(player)
	player.stream = load(path)
	player.volume_db = volume_db
	player.pitch_scale = pitch_scale
	player.finished.connect(player.queue_free)
	if player.stream != null:
		player.play()
	else:
		push_warning("Missing sound stream: " + path)
		player.queue_free()
	return player


func set_music_volume(volume_db: float) -> void:
	if _music_players.size() > _active_music:
		_music_players[_active_music].volume_db = volume_db


func _on_music_finished(index: int) -> void:
	if index == _active_music and not _music_path.is_empty():
		_music_players[index].play()


func _on_ambient_finished() -> void:
	if not _ambient_path.is_empty():
		_ambient_player.play()
