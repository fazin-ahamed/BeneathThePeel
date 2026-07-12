extends Node2D

const RoomDB = preload("res://scripts/room_database.gd")
const InputSetup = preload("res://scripts/input_setup.gd")
const InteractionRules = preload("res://scripts/interaction_rules.gd")
const RoomLighting = preload("res://scripts/room_lighting.gd")
const Story = preload("res://scripts/story_text.gd")
const PlayerActor = preload("res://scripts/player.gd")
const Actor = preload("res://scripts/actor.gd")
const Interactable = preload("res://scripts/interactable.gd")
const Guard = preload("res://scripts/guard.gd")
const FXLayer = preload("res://scripts/fx_layer.gd")
const HUD = preload("res://scripts/hud.gd")
const DialogueUI = preload("res://scripts/dialogue_ui.gd")
const TitleUI = preload("res://scenes/ui/title_menu.tscn")
const PauseUI = preload("res://scenes/ui/pause_menu.tscn")
const EndingUI = preload("res://scenes/ui/ending_menu.tscn")
const CaptureUI = preload("res://scenes/ui/capture_menu.tscn")

var background: Sprite2D
var world_root: Node2D
var fx_root
var lighting_root
var player
var hud
var dialogue
var title_screen
var fade_layer: CanvasLayer
var fade_rect: ColorRect
var pause_layer: CanvasLayer
var capture_screen: CaptureMenu

var current_room: String = ""
var room_data: Dictionary = {}
var interactables: Array = []
var triggers: Array = []
var guards: Array = []
var peel_nodes: Array = []

var busy: bool = true
var ending_active: bool = false
var interaction_cooldown: float = 0.0
var nearest_interactable = null
var shake_time: float = 0.0
var shake_strength: float = 0.0
var paused_by_menu: bool = false
var story_starting: bool = false
var capture_active: bool = false


func _ready() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
	InputSetup.ensure_default_actions()
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build_root_nodes()
	_show_title()


func _build_root_nodes() -> void:
	background = Sprite2D.new()
	background.name = "Background"
	background.centered = false
	background.z_index = -100
	background.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(background)

	hud = HUD.new()
	add_child(hud)

	dialogue = DialogueUI.new()
	add_child(dialogue)

	fade_layer = CanvasLayer.new()
	fade_layer.layer = 80
	add_child(fade_layer)
	fade_rect = ColorRect.new()
	fade_rect.position = Vector2.ZERO
	fade_rect.size = Vector2(320, 180)
	fade_rect.color = Color.BLACK
	fade_rect.modulate.a = 0.0
	fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade_layer.add_child(fade_rect)


func _show_title() -> void:
	story_starting = false
	capture_active = false
	if is_instance_valid(capture_screen):
		capture_screen.queue_free()
	capture_screen = null
	busy = true
	ending_active = false
	_clear_world()
	hud.visible = false
	AudioManager.stop_music(0.2)
	AudioManager.stop_ambient()
	if is_instance_valid(title_screen):
		title_screen.queue_free()
	title_screen = TitleUI.instantiate()
	add_child(title_screen)
	title_screen.start_new.connect(_on_new_game)
	title_screen.quit_requested.connect(_on_quit_requested)


func _on_quit_requested() -> void:
	get_tree().quit()


func _on_new_game() -> void:
	if story_starting:
		return
	story_starting = true
	if is_instance_valid(title_screen):
		title_screen.queue_free()
		title_screen = null
	GameState.reset_game()
	GameState.set_flag("started", true)
	hud.visible = true
	busy = true
	await _change_room("temple_exterior", null, true)
	if is_instance_valid(player):
		player.input_enabled = false
	await dialogue.play(Story.dialogue("intro"))
	GameState.set_flag("intro_played", true)
	hud.set_objective("Enter the temple")
	if is_instance_valid(player):
		player.input_enabled = true
	await _release_interaction_key()
	busy = false
	story_starting = false
	_refresh_objective()


func _process(delta: float) -> void:
	if interaction_cooldown > 0.0:
		interaction_cooldown = maxf(0.0, interaction_cooldown - delta)
	_update_camera_shake(delta)

	if OS.is_debug_build() and Input.is_action_just_pressed("debug_collision"):
		var room := world_root as RoomDefinition
		if room != null:
			room.set_collision_debug_visible(not room.collision_debug_visible())

	if (
		Input.is_action_just_pressed("pause")
		and not is_instance_valid(title_screen)
		and not capture_active
	):
		_toggle_pause()

	if paused_by_menu or capture_active:
		return

	if current_room == "chase" and is_instance_valid(player):
		_process_chase()

	if busy or ending_active or dialogue.is_open or not is_instance_valid(player):
		if is_instance_valid(hud):
			hud.set_prompt("")
		return

	_check_triggers()
	if busy:
		return

	_update_nearest_interaction()
	if interaction_cooldown <= 0.0 and is_instance_valid(nearest_interactable):
		if Input.is_action_just_pressed("interact"):
			interaction_cooldown = 0.22
			nearest_interactable.try_activate()


func _update_nearest_interaction() -> void:
	nearest_interactable = null
	var nearest_distance := INF
	for node in interactables:
		if not is_instance_valid(node):
			continue
		if not node.is_available():
			continue
		if not InteractionRules.is_available(node.event_name):
			continue
		var distance: float = float(player.position.distance_to(node.position))
		if distance <= node.radius and distance < nearest_distance:
			nearest_distance = distance
			nearest_interactable = node
	if is_instance_valid(nearest_interactable):
		hud.set_prompt(
			InteractionRules.dynamic_prompt(
				nearest_interactable.event_name, nearest_interactable.prompt
			)
		)
	else:
		hud.set_prompt("")


func _check_triggers() -> void:
	for trigger in triggers:
		if bool(trigger.get("disabled", false)):
			continue
		var trigger_id := str(trigger.get("id", ""))
		if bool(trigger.get("one_shot", false)) and GameState.is_claimed(trigger_id):
			continue
		var rect: Rect2 = trigger.get("rect", Rect2())
		if not rect.has_point(player.position):
			continue
		trigger["disabled"] = true
		_start_event(str(trigger.get("event", "")), null, trigger_id)
		return


func _start_event(event_name: String, source, completion_id: String = "") -> void:
	if busy:
		return
	_run_event(event_name, source, completion_id)


func _on_interactable_activated(event_name: String, source) -> void:
	_start_event(event_name, source)


func _run_event(event_name: String, source, completion_id: String = "") -> void:
	busy = true
	var one_shot_id := completion_id
	if is_instance_valid(source) and bool(source.one_shot):
		one_shot_id = str(source.interaction_id)
	var event_handled := true
	hud.set_prompt("")
	if is_instance_valid(player):
		player.input_enabled = false

	match event_name:
		"enter_temple":
			await _event_enter_temple()
		"pray_at_altar":
			await _event_pray()
		"leave_temple":
			await _event_leave_temple()
		"fall_into_manhole":
			await _event_manhole()
		"inspect_cult_window":
			await _event_cult_window()
		"descend_to_lobby":
			await _event_descend_lobby()
		"cult_induction":
			await _event_induction()
		"talk_foreman":
			await _event_foreman()
		"go_storage":
			await _change_room("storage", &"FromHQ", true)
		"return_from_storage":
			await _change_room("cult_hq", &"FromStorage", true)
		"go_statue":
			await _change_room("statue_room", &"FromHQ", true)
		"return_from_statue":
			await _change_room("cult_hq", &"FromStatue", true)
		"go_engine":
			await _change_room("engine_room", &"FromHQ", true)
		"return_from_engine":
			await _change_room("cult_hq", &"FromEngine", true)
		"go_quarters":
			await _change_room("quarters", &"FromHQ", true)
		"return_from_quarters":
			await _change_room("cult_hq", &"FromQuarters", true)
		"pick_up_box":
			await _event_pick_box()
		"deliver_box_statue":
			await _event_deliver_box(0)
		"deliver_box_engine":
			await _event_deliver_box(1)
		"deliver_box_archive":
			await _event_deliver_box(2)
		"polish_statue":
			await _event_statue(source)
		"load_banana_fuel_left":
			await _event_load_fuel("fuel_left", "fuel_left", source, false)
		"load_banana_fuel_right":
			await _event_load_fuel("fuel_right", "fuel_right", source, false)
		"load_apple":
			await _event_load_fuel("fuel_apple", "fuel_apple", source, true)
		"inspect_potassium_configuration":
			await dialogue.play(Story.dialogue("potassium_configuration"))
		"inspect_vending_machine":
			await dialogue.play(Story.dialogue("vending_machine"))
		"inspect_cult_noticeboard":
			await dialogue.play(Story.dialogue("cult_noticeboard"))
		"inspect_ritual_drum":
			await dialogue.play(Story.dialogue("ritual_drum"))
		"inspect_sewer_sign":
			await dialogue.play(Story.dialogue("sewer_sign"))
		"activate_engine":
			await _event_engine_core()
		"search_locker_1":
			await _event_locker(1, source)
		"search_locker_2":
			await _event_locker(2, source)
		"search_locker_3":
			await _event_locker(3, source)
		"search_locker_4":
			await _event_locker(4, source)
		"search_locker_5":
			await _event_locker(5, source)
		"attempt_escape":
			await _event_attempt_escape()
		"finish_chase":
			await _event_finish_chase()
		_:
			event_handled = false
			push_warning("Unhandled story event: " + event_name)

	if event_handled and not one_shot_id.is_empty():
		GameState.claim_once(one_shot_id)
	elif not event_handled and is_instance_valid(source) and bool(source.one_shot):
		source.enable()

	if is_instance_valid(player) and not ending_active:
		player.input_enabled = true
	await _release_interaction_key()
	interaction_cooldown = 0.18
	if not ending_active:
		busy = false
	_refresh_objective()


func _event_enter_temple() -> void:
	await _change_room("temple_interior", &"Entrance", true)
	player.input_enabled = false
	await dialogue.play(Story.dialogue("enter_temple"))
	GameState.set_flag("entered_temple", true)
	hud.set_objective("Approach the altar")


func _event_pray() -> void:
	var lines := Story.dialogue("prayer")
	await dialogue.play([lines[0]])
	AudioManager.play_sfx("res://assets/audio/thump.wav", -4.0)
	_start_shake(3.0, 0.45)
	await get_tree().create_timer(0.3).timeout
	var rest: Array = []
	for index in range(1, lines.size()):
		rest.append(lines[index])
	await dialogue.play(rest)
	GameState.set_flag("prayed", true)
	hud.show_notification("Something answered from beneath the floor.")
	hud.set_objective("Leave the temple")


func _event_leave_temple() -> void:
	if not bool(GameState.get_flag("prayed", false)):
		await dialogue.play(Story.dialogue("leave_before_prayer"))
		return
	await _change_room("street", &"TempleDoor", true)
	hud.show_room_title("THE STREET")
	hud.set_objective("Head home")


func _event_manhole() -> void:
	await dialogue.play(Story.dialogue("manhole"))
	await _play_fall_and_sewer_cutscene()


func _play_fall_and_sewer_cutscene() -> void:
	if is_instance_valid(player):
		player.input_enabled = false
	await _fade_to(1.0, 0.18)
	_clear_world()
	AudioManager.stop_music(0.2)
	AudioManager.play_ambient("res://assets/audio/fall_wind.wav", -7.0)

	var layer: CanvasLayer = CanvasLayer.new()
	layer.layer = 24
	add_child(layer)
	var stage: Node2D = Node2D.new()
	stage.name = "FallingStage"
	layer.add_child(stage)

	var shaft_scene: PackedScene = load("res://scenes/cutscenes/fall_shaft.tscn") as PackedScene
	var shaft_a: Node2D = shaft_scene.instantiate() as Node2D
	var shaft_b: Node2D = shaft_scene.instantiate() as Node2D
	shaft_a.position = Vector2.ZERO
	shaft_b.position = Vector2(0.0, 576.0)
	stage.add_child(shaft_a)
	stage.add_child(shaft_b)

	var streak_field: Node2D = _make_fall_streak_field(stage)
	var debris: Array[Polygon2D] = _make_fall_debris(stage)
	var falling_actor: Sprite2D = _make_cutscene_actor(
		"res://assets/characters/player_sheet.png", Vector2(160.0, 42.0)
	)
	falling_actor.rotation = 0.32
	falling_actor.z_index = 30
	stage.add_child(falling_actor)
	var loose_shoe: Polygon2D = _make_fall_shoe(stage, falling_actor.position + Vector2(10.0, 9.0))
	loose_shoe.visible = false

	var impact_flash: ColorRect = ColorRect.new()
	impact_flash.position = Vector2.ZERO
	impact_flash.size = Vector2(320.0, 180.0)
	impact_flash.color = Color(0.82, 0.91, 1.0, 1.0)
	impact_flash.modulate.a = 0.0
	impact_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(impact_flash)
	await _fade_to(0.0, 0.22)

	# The shaft moves UP while the actor accelerates DOWN. This is the visual
	# relationship that makes the fall read correctly instead of looking like ascent.
	var shaft_tween: Tween = stage.create_tween()
	shaft_tween.set_parallel(true)
	(
		shaft_tween
		. tween_property(shaft_a, "position:y", -576.0, 3.45)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)
	(
		shaft_tween
		. tween_property(shaft_b, "position:y", 0.0, 3.45)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)
	(
		shaft_tween
		. tween_property(streak_field, "position:y", -420.0, 3.45)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)

	var actor_drop: Tween = stage.create_tween()
	actor_drop.set_parallel(true)
	(
		actor_drop
		. tween_property(falling_actor, "position:y", 124.0, 3.45)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)
	(
		actor_drop
		. tween_property(falling_actor, "scale", Vector2(2.35, 2.35), 3.45)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)

	var spin_tween: Tween = stage.create_tween()
	spin_tween.set_loops(7)
	spin_tween.tween_property(falling_actor, "rotation", -0.55, 0.24)
	spin_tween.tween_property(falling_actor, "rotation", 0.55, 0.24)

	for index in range(debris.size()):
		var piece: Polygon2D = debris[index]
		var debris_tween: Tween = stage.create_tween()
		debris_tween.set_parallel(true)
		(
			debris_tween
			. tween_property(
				piece,
				"position:y",
				piece.position.y - 300.0 - float(index % 4) * 30.0,
				2.7 + float(index % 3) * 0.25
			)
			. set_trans(Tween.TRANS_QUAD)
			. set_ease(Tween.EASE_IN)
		)
		debris_tween.tween_property(piece, "rotation", piece.rotation + TAU * 2.0, 2.7)

	var hit_intervals: Array[float] = [0.62, 0.76, 0.82]
	for index in range(hit_intervals.size()):
		await get_tree().create_timer(hit_intervals[index]).timeout
		AudioManager.play_sfx("res://assets/audio/thump.wav", -5.5, 0.9 + float(index) * 0.07)
		if index == 0:
			loose_shoe.visible = true
			loose_shoe.position = falling_actor.position + Vector2(10.0, 9.0)
			var shoe_tween: Tween = stage.create_tween()
			shoe_tween.set_parallel(true)
			(
				shoe_tween
				. tween_property(loose_shoe, "position", Vector2(205.0, -28.0), 2.5)
				. set_trans(Tween.TRANS_QUAD)
				. set_ease(Tween.EASE_OUT)
			)
			shoe_tween.tween_property(loose_shoe, "rotation", TAU * 4.0, 2.5)
		_fall_impact(stage, impact_flash, -1.0 if index % 2 == 0 else 1.0, 3.0 + float(index))
	await shaft_tween.finished

	impact_flash.color = Color(0.25, 0.68, 0.86, 1.0)
	impact_flash.modulate.a = 0.72
	AudioManager.play_sfx("res://assets/audio/splash.wav", -1.0)
	var splash_flash: Tween = layer.create_tween()
	splash_flash.tween_property(impact_flash, "modulate:a", 0.0, 0.2)
	await get_tree().create_timer(0.12).timeout
	await _fade_to(1.0, 0.2)
	layer.queue_free()

	AudioManager.play_ambient("res://assets/audio/sewer_flow_loop.wav", -13.0)
	var ride_layer: CanvasLayer = CanvasLayer.new()
	ride_layer.layer = 24
	add_child(ride_layer)
	var tunnel_scene: PackedScene = load("res://scenes/cutscenes/sewer_ride.tscn") as PackedScene
	var tunnel: Node2D = tunnel_scene.instantiate() as Node2D
	tunnel.position = Vector2.ZERO
	ride_layer.add_child(tunnel)
	var floating_actor: Sprite2D = _make_cutscene_actor(
		"res://assets/characters/player_sheet.png", Vector2(118.0, 132.0)
	)
	floating_actor.rotation = PI * 0.5
	ride_layer.add_child(floating_actor)
	await _fade_to(0.0, 0.25)
	var ride_tween: Tween = ride_layer.create_tween()
	ride_tween.set_parallel(true)
	ride_tween.tween_property(tunnel, "position:x", -320.0, 5.2)
	ride_tween.tween_property(floating_actor, "position:x", 206.0, 5.2)
	ride_tween.tween_property(floating_actor, "position:y", 126.0, 2.6)
	ride_tween.set_parallel(false)
	await ride_tween.finished
	await _fade_to(1.0, 0.24)
	ride_layer.queue_free()

	await _change_room("sewer_explore", &"WashedUp", false)
	await _fade_to(0.0, 0.28)
	player.input_enabled = false
	await dialogue.play(Story.dialogue("wakeup"))
	GameState.set_flag("washed_up", true)
	GameState.set_checkpoint("sewer_explore", player.position)
	hud.show_room_title("BENEATH THE TEMPLE")
	hud.set_objective("Follow the thumping")


func _event_cult_window() -> void:
	await _fade_to(1.0, 0.18)
	var layer := CanvasLayer.new()
	layer.layer = 24
	add_child(layer)
	var ritual_scene := load("res://scenes/cutscenes/cult_window.tscn") as PackedScene
	var ritual_map := ritual_scene.instantiate() as Node2D
	ritual_map.position = Vector2.ZERO
	layer.add_child(ritual_map)
	AudioManager.play_music("res://assets/audio/cult_music_loop.wav", -16.0, 0.5)
	await _fade_to(0.0, 0.24)
	AudioManager.play_sfx("res://assets/audio/thump.wav", -7.0, 0.8)
	await dialogue.play(Story.dialogue("cult_window"))
	await _fade_to(1.0, 0.2)
	layer.queue_free()
	AudioManager.play_music("res://assets/audio/heartbeat_loop.wav", -17.0, 0.4)
	await _fade_to(0.0, 0.2)
	GameState.set_flag("window_seen", true)
	hud.set_objective("Descend the hidden stairs")


func _event_descend_lobby() -> void:
	if not bool(GameState.get_flag("window_seen", false)):
		await dialogue.play(Story.dialogue("stairs_before_window"))
		return
	await _change_room("cult_lobby", &"SewerStairs", true)
	hud.show_room_title("THE UNDERGROUND LOBBY")


func _event_induction() -> void:
	var choice: Variant = await dialogue.play(Story.dialogue("induction"))
	if choice == "plumber":
		await dialogue.play(
			[
				{
					"speaker": "Guard",
					"text": "Excellent. The eastern pipe has been bleeding since Tuesday.",
					"portrait": "guard"
				}
			]
		)
	elif choice == "hole":
		await dialogue.play(
			[
				{
					"speaker": "Guard",
					"text": "The traditional entrance. Very devout.",
					"portrait": "guard"
				}
			]
		)
	else:
		await dialogue.play(
			[{"speaker": "Guard", "text": "Flattery is the first sacrament.", "portrait": "guard"}]
		)
	GameState.set_flag("robed", true)
	GameState.set_flag("inducted", true)
	await _change_room("cult_hq", &"Lobby", true)
	player.set_costume("robed")
	player.input_enabled = false
	await dialogue.play(Story.dialogue("hq_intro"))
	GameState.set_flag("hq_intro_done", true)
	GameState.set_flag("task_phase", "boxes")
	GameState.set_checkpoint("cult_hq", player.position)
	hud.show_room_title("CULT HEADQUARTERS")
	hud.set_objective("Report to the Logistics Elder")


func _event_foreman() -> void:
	var boxes := GameState.get_counter("boxes_delivered")
	var seals := GameState.get_counter("seals")
	if boxes < 3:
		if not bool(GameState.get_flag("foreman_briefed", false)):
			GameState.set_flag("foreman_briefed", true)
			await dialogue.play(Story.dialogue("foreman_start"))
		else:
			await dialogue.play(Story.dialogue("foreman_boxes_progress"))
		hud.set_objective("Deliver three Sacred Boxes (" + str(boxes) + "/3)")
	elif seals < 3:
		if str(GameState.get_flag("task_phase", "")) != "duties":
			GameState.set_flag("task_phase", "duties")
			await dialogue.play(Story.dialogue("foreman_after_boxes"))
		else:
			await dialogue.play(
				[
					{
						"speaker": "Logistics Elder",
						"text":
						"Earn the remaining seals. Preferably without awakening anything taxable.",
						"portrait": "cultist"
					}
				]
			)
		hud.set_objective("Earn three security seals (" + str(seals) + "/3)")
	else:
		await dialogue.play(Story.dialogue("foreman_done"))
		hud.set_objective("Use the sealed exit")


func _event_pick_box() -> void:
	if bool(GameState.get_flag("carrying_box", false)):
		await dialogue.play(Story.dialogue("already_carrying"))
		return
	var delivered := GameState.get_counter("boxes_delivered")
	if delivered >= 3:
		await dialogue.play(
			[
				{
					"speaker": "You",
					"text": "The remaining boxes are someone else's problem.",
					"portrait": "player_robed"
				}
			]
		)
		return
	if not GameState.begin_box_delivery(delivered):
		return
	if is_instance_valid(player):
		player.set_carrying(true)
	AudioManager.play_sfx("res://assets/audio/pickup.wav", -3.0)
	await dialogue.play(Story.dialogue("box_pickup"))
	hud.show_notification("Sacred Box acquired.")
	_refresh_objective()


func _event_deliver_box(target_index: int) -> void:
	if not bool(GameState.get_flag("carrying_box", false)):
		return
	var expected := int(GameState.get_flag("box_target", -1))
	if expected != target_index:
		await dialogue.play(Story.dialogue("wrong_delivery"))
		return
	var delivered := GameState.complete_box_delivery(target_index)
	if delivered < 0:
		return
	if is_instance_valid(player):
		player.set_carrying(false)
	AudioManager.play_sfx("res://assets/audio/pickup.wav", -1.0, 1.15)
	hud.show_notification("Sacred Box delivered: " + str(delivered) + "/3")
	if delivered >= 3:
		GameState.set_flag("task_phase", "duties")
		await dialogue.play(Story.dialogue("boxes_complete"))
		hud.set_objective("Earn three security seals")
	else:
		hud.set_objective("Return to storage for box " + str(delivered + 1))


func _event_statue(source) -> void:
	if GameState.get_counter("boxes_delivered") < 3:
		await dialogue.play(Story.dialogue("duties_locked"))
		return
	if GameState.is_claimed("statue_polished"):
		await dialogue.play(Story.dialogue("statue_done"))
		return
	await dialogue.play(Story.dialogue("statue"))
	if not GameState.complete_seal_task("statue_polished", "statue"):
		return
	if is_instance_valid(source):
		source.disable()
	AudioManager.play_sfx("res://assets/audio/pickup.wav", -1.0, 1.3)
	_spawn_visual_burst(
		"res://assets/props/security_seal.png",
		_room_marker("ProgressMarkers/SealBurst", Vector2(160, 102)),
		12
	)
	hud.update_seals(GameState.get_counter("seals"))
	hud.show_notification("SECURITY SEAL ACQUIRED")
	_refresh_objective()


func _event_load_fuel(flag_id: String, dialogue_key: String, source, is_apple: bool) -> void:
	if GameState.get_counter("boxes_delivered") < 3:
		await dialogue.play(Story.dialogue("duties_locked"))
		return
	if GameState.is_claimed(flag_id):
		return
	await dialogue.play(Story.dialogue(dialogue_key))
	if is_apple:
		await _launch_apple()
	else:
		AudioManager.play_sfx("res://assets/audio/pickup.wav", -3.0, 0.92)
	var fuel := GameState.complete_fuel_source(flag_id)
	if fuel < 0:
		return
	if is_instance_valid(source):
		source.disable()
	hud.show_notification("Engine fuel loaded: " + str(fuel) + "/3")
	_refresh_objective()


func _launch_apple() -> void:
	var apple := Sprite2D.new()
	apple.texture = load("res://assets/props/apple.png")
	apple.position = _room_marker("ProgressMarkers/AppleLaunchStart", Vector2(85, 80))
	apple.z_index = 20
	apple.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_actor_root().add_child(apple)
	AudioManager.play_sfx("res://assets/audio/thump.wav", -5.0, 1.3)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(
		apple, "position", _room_marker("ProgressMarkers/AppleLaunchTarget", Vector2(294, 46)), 0.55
	)
	tween.tween_property(apple, "rotation", TAU * 5.0, 0.55)
	tween.set_parallel(false)
	await tween.finished
	_start_shake(3.0, 0.25)
	apple.queue_free()


func _event_engine_core() -> void:
	if GameState.get_counter("boxes_delivered") < 3:
		await dialogue.play(Story.dialogue("duties_locked"))
		return
	if GameState.get_counter("fuel_loaded") < 3:
		await dialogue.play(Story.dialogue("engine_not_ready"))
		return
	if GameState.is_claimed("engine_complete"):
		await dialogue.play(Story.dialogue("engine_done"))
		return
	AudioManager.play_sfx("res://assets/audio/alarm.wav", -5.0)
	AudioManager.play_sfx("res://assets/audio/thump.wav", -2.0, 0.72)
	_start_shake(5.0, 0.9)
	await get_tree().create_timer(0.4).timeout
	await dialogue.play(Story.dialogue("engine_complete"))
	if GameState.complete_seal_task("engine_complete", "engine"):
		hud.update_seals(GameState.get_counter("seals"))
		hud.show_notification("SECURITY SEAL ACQUIRED")
	_spawn_visual_burst("res://assets/props/security_seal.png", Vector2(160, 90), 14)


func _event_locker(number: int, source) -> void:
	if GameState.get_counter("boxes_delivered") < 3:
		await dialogue.play(Story.dialogue("duties_locked"))
		return
	var locker_id := "locker_" + str(number)
	if GameState.is_claimed(locker_id):
		await dialogue.play(Story.dialogue("locker_empty"))
		return
	if number == 4:
		var cav_data := {
			"kind": "cavendish",
			"pos": _room_marker("ProgressMarkers/Cavendish", Vector2(200, 122)),
			"facing": 0
		}
		_spawn_actor(cav_data)
		await dialogue.play(Story.dialogue("cavendish"))
		if GameState.complete_seal_task(locker_id, "cavendish"):
			hud.update_seals(GameState.get_counter("seals"))
			hud.show_notification("SECURITY SEAL ACQUIRED")
			_spawn_visual_burst(
				"res://assets/props/security_seal.png",
				_room_marker("ProgressMarkers/SealBurst", Vector2(200, 112)),
				12
			)
	else:
		await dialogue.play(Story.dialogue(locker_id))
		GameState.claim_once(locker_id)
	if is_instance_valid(source):
		source.disable()
	_refresh_objective()


func _event_attempt_escape() -> void:
	if GameState.get_counter("seals") < 3:
		await dialogue.play(Story.dialogue("exit_locked"))
		return
	if GameState.is_claimed("escape_sequence"):
		return
	AudioManager.play_sfx("res://assets/audio/alarm.wav", -1.0)
	_start_shake(4.0, 0.6)
	await dialogue.play(Story.dialogue("escape"))
	await _change_room("chase", &"Start", true)
	GameState.set_checkpoint("chase", player.position)
	GameState.claim_once("escape_sequence")
	player.base_speed = 68.0
	player.sprint_multiplier = 1.28
	player.input_enabled = true
	hud.show_room_title("ESCAPE")
	hud.set_objective("RUN. The cult has declared you a smoothie.")


func _process_chase() -> void:
	for guard_node in guards:
		if not is_instance_valid(guard_node):
			continue
		for peel in peel_nodes:
			if not is_instance_valid(peel):
				continue
			if bool(peel.get_meta("used", false)):
				continue
			if guard_node.position.distance_to(peel.position) < 11.0:
				peel.set_meta("used", true)
				peel.modulate.a = 0.25
				guard_node.make_slip()
				AudioManager.play_sfx("res://assets/audio/slip.wav", -2.0, randf_range(0.9, 1.1))
				break


func _on_guard_caught() -> void:
	if busy or ending_active or capture_active:
		return
	_show_capture_menu()


func _show_capture_menu() -> void:
	capture_active = true
	busy = true
	hud.clear_quest_target()
	hud.set_prompt("")
	if is_instance_valid(player):
		player.input_enabled = false
		player.velocity = Vector2.ZERO
	for guard_node in guards:
		if not is_instance_valid(guard_node):
			continue
		guard_node.active = false
		guard_node.velocity = Vector2.ZERO
	AudioManager.stop_music(0.18)
	AudioManager.play_sfx("res://assets/audio/alarm.wav", -5.0, 0.72)
	_start_shake(3.0, 0.25)
	if is_instance_valid(capture_screen):
		capture_screen.queue_free()
	capture_screen = CaptureUI.instantiate() as CaptureMenu
	add_child(capture_screen)
	capture_screen.retry_requested.connect(_on_capture_retry)
	capture_screen.title_requested.connect(_on_capture_title)


func _on_capture_retry() -> void:
	if not capture_active:
		return
	if is_instance_valid(capture_screen):
		capture_screen.queue_free()
	capture_screen = null
	capture_active = false
	_restart_chase()


func _on_capture_title() -> void:
	if is_instance_valid(capture_screen):
		capture_screen.queue_free()
	capture_screen = null
	capture_active = false
	_show_title()


func _restart_chase() -> void:
	busy = true
	if is_instance_valid(player):
		player.input_enabled = false
	await _change_room("chase", &"Start", true)
	player.base_speed = 68.0
	player.sprint_multiplier = 1.28
	player.input_enabled = true
	await _release_interaction_key()
	busy = false
	_refresh_objective()


func _event_finish_chase() -> void:
	ending_active = true
	if is_instance_valid(player):
		player.input_enabled = false
	await _change_room("surface_ending", &"Default", true)
	player.input_enabled = false
	await dialogue.play(Story.dialogue("ending_surface"))
	await _spawn_falling_boxes()
	AudioManager.play_sfx("res://assets/audio/banana_apocalypse.wav", -1.0)
	_start_shake(6.0, 1.2)
	await _spawn_banana_apocalypse()
	var leader_data := {"kind": "leader", "pos": Vector2(160, 143), "facing": 0}
	_spawn_actor(leader_data)
	await dialogue.play(Story.dialogue("ending_apocalypse"))
	await _fade_to(1.0, 0.5)
	_clear_world()
	background.visible = true
	background.texture = load("res://assets/backgrounds/banana_earth.png")
	background.position = Vector2.ZERO
	AudioManager.play_music("res://assets/audio/cult_music_loop.wav", -9.0, 0.8)
	await _fade_to(0.0, 0.6)
	await dialogue.play(Story.dialogue("ending_final"))
	GameState.set_flag("ending_seen", true)
	await _show_ending_menu()


func _spawn_falling_boxes() -> void:
	var tweens: Array = []
	for index in range(8):
		var sprite := Sprite2D.new()
		sprite.texture = load("res://assets/props/sacred_box.png")
		sprite.position = Vector2(20 + index * 39, -18 - (index % 3) * 12)
		sprite.z_index = 30
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		world_root.add_child(sprite)
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(sprite, "position:y", 118.0 + (index % 2) * 18.0, 0.65 + index * 0.06)
		tween.tween_property(sprite, "rotation", (index - 4) * 0.6, 0.65 + index * 0.06)
		tween.set_parallel(false)
		tweens.append(tween)
	await get_tree().create_timer(1.25).timeout


func _spawn_banana_apocalypse() -> void:
	for index in range(60):
		var sprite := Sprite2D.new()
		sprite.texture = load(
			(
				"res://assets/props/banana_peel.png"
				if index % 2 == 0
				else "res://assets/props/banana_fuel.png"
			)
		)
		sprite.position = Vector2(randf_range(0.0, 320.0), randf_range(-80.0, -4.0))
		sprite.scale = Vector2.ONE * randf_range(0.55, 1.2)
		sprite.rotation = randf_range(-PI, PI)
		sprite.z_index = 45
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		world_root.add_child(sprite)
		var target := Vector2(
			sprite.position.x + randf_range(-24.0, 24.0), randf_range(80.0, 178.0)
		)
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(sprite, "position", target, randf_range(0.8, 1.6))
		tween.tween_property(
			sprite, "rotation", sprite.rotation + randf_range(3.0, 9.0), randf_range(0.8, 1.6)
		)
	await get_tree().create_timer(1.7).timeout


func _show_ending_menu() -> void:
	var menu := EndingUI.instantiate() as EndingMenu
	add_child(menu)
	menu.replay_requested.connect(
		func() -> void:
			menu.queue_free()
			ending_active = false
			_on_new_game()
	)
	menu.title_requested.connect(
		func() -> void:
			menu.queue_free()
			_show_title()
	)
	await get_tree().process_frame


func _change_room(room_id: String, spawn_override: Variant = null, with_fade: bool = true) -> void:
	if with_fade:
		await _fade_to(1.0, 0.22)
	_build_room(room_id, spawn_override)
	if with_fade:
		await _fade_to(0.0, 0.28)


func _build_room(room_id: String, spawn_override: Variant = null) -> void:
	var scene_path: String = RoomDB.scene_path(room_id)
	if scene_path.is_empty():
		push_error("Unknown room: " + room_id)
		return

	current_room = room_id
	_clear_world()
	background.visible = false

	var room_scene := load(scene_path) as PackedScene
	if room_scene == null:
		push_error("Missing room scene for: " + room_id)
		return
	var room_instance := room_scene.instantiate() as RoomDefinition
	if room_instance == null:
		push_error("Room scene root must use room_definition.gd: " + room_id)
		return
	room_data = room_instance.to_runtime_data()
	world_root = room_instance
	world_root.name = "World_" + room_id
	add_child(world_root)

	var world_size: Vector2 = room_instance.world_size
	var player_bounds: Rect2 = room_instance.player_bounds
	var spawn_position: Vector2 = room_instance.default_spawn_position()
	if spawn_override is Vector2:
		spawn_position = spawn_override
	elif spawn_override is String or spawn_override is StringName:
		spawn_position = room_instance.spawn_position(StringName(str(spawn_override)))

	fx_root = FXLayer.new()
	fx_root.name = "Atmosphere"
	fx_root.z_index = 80
	add_child(fx_root)
	fx_root.configure(str(room_data.get("fx", "none")), world_size)

	var actor_root: Node2D = room_instance.actor_parent()
	player = PlayerActor.new()
	player.costume = "robed" if bool(GameState.get_flag("robed", false)) else "normal"
	player.carrying = bool(GameState.get_flag("carrying_box", false))
	actor_root.add_child(player)
	player.position = spawn_position
	player.set_world_bounds(player_bounds)
	player.update_camera_limits(world_size)
	player.footstep.connect(_on_player_footstep)

	lighting_root = RoomLighting.new()
	lighting_root.name = "RoomLighting"
	add_child(lighting_root)
	lighting_root.configure(room_id, player)

	interactables.clear()
	var interaction_root := world_root.get_node_or_null("Interactions")
	if interaction_root != null:
		for child in interaction_root.get_children():
			var marker := child as InteractionPoint
			if marker == null:
				continue
			var data := {
				"id": marker.interaction_id,
				"event": marker.event_name,
				"prompt": marker.prompt,
				"pos": marker.position,
				"radius": marker.radius,
				"one_shot": marker.one_shot
			}
			marker.visible = false
			_spawn_interactable(data)

	var npc_root := world_root.get_node_or_null("NPCSpawns")
	if npc_root != null:
		for child in npc_root.get_children():
			var marker := child as NPCSpawnPoint
			if marker == null:
				continue
			marker.visible = false
			_spawn_actor(
				{
					"kind": marker.kind,
					"pos": marker.position,
					"facing": marker.facing,
					"animated": marker.animated
				}
			)
	_spawn_progress_props(room_id)

	triggers.clear()
	var trigger_root := world_root.get_node_or_null("Triggers")
	if trigger_root != null:
		for child in trigger_root.get_children():
			var marker := child as TriggerMarker
			if marker == null:
				continue
			marker.visible = false
			triggers.append(
				{
					"id": marker.trigger_id,
					"event": marker.event_name,
					"rect": Rect2(marker.position - marker.size * 0.5, marker.size),
					"one_shot": marker.one_shot,
					"disabled": false
				}
			)

	guards.clear()
	peel_nodes.clear()
	if room_id == "chase":
		_spawn_chase_entities_from_scene()

	AudioManager.play_music(
		str(room_data.get("music", "")), float(room_data.get("music_volume", -13.0)), 0.55
	)
	AudioManager.play_ambient(
		str(room_data.get("ambient", "")), float(room_data.get("ambient_volume", -18.0))
	)
	hud.update_seals(GameState.get_counter("seals"))
	_refresh_objective()
	if bool(GameState.get_flag("started", false)) and room_id != "surface_ending":
		GameState.set_checkpoint(room_id, player.position)


func _clear_world() -> void:
	if is_instance_valid(hud):
		hud.clear_quest_target()
	nearest_interactable = null
	interactables.clear()
	triggers.clear()
	guards.clear()
	peel_nodes.clear()
	if is_instance_valid(world_root):
		world_root.free()
	if is_instance_valid(fx_root):
		fx_root.free()
	if is_instance_valid(lighting_root):
		lighting_root.free()
	world_root = null
	fx_root = null
	lighting_root = null
	player = null


func _spawn_collider(rect: Rect2) -> void:
	var body := StaticBody2D.new()
	body.position = rect.position + rect.size * 0.5
	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = rect.size
	collision.shape = shape
	body.add_child(collision)
	world_root.add_child(body)


func _spawn_interactable(data: Dictionary):
	var node := Interactable.new()
	node.configure(data)
	world_root.add_child(node)
	node.activated.connect(_on_interactable_activated)
	interactables.append(node)
	return node


func _actor_root() -> Node2D:
	var room := world_root as RoomDefinition
	if room != null:
		return room.actor_parent()
	return world_root


func _spawn_actor(data: Dictionary):
	var actor := Actor.new()
	actor.configure(data)
	actor.position = data.get("pos", Vector2.ZERO)
	_actor_root().add_child(actor)
	return actor


func _room_marker(path: String, fallback: Vector2) -> Vector2:
	if is_instance_valid(world_root):
		var marker := world_root.get_node_or_null(path) as Marker2D
		if marker != null:
			return marker.position
	return fallback


func _spawn_chase_entities_from_scene() -> void:
	var peel_root := world_root.get_node_or_null("PeelSpawns")
	if peel_root != null:
		for marker in peel_root.get_children():
			var peel := Sprite2D.new()
			peel.texture = load("res://assets/props/banana_peel.png")
			peel.position = marker.position
			peel.z_index = 3
			peel.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			peel.set_meta("used", false)
			_actor_root().add_child(peel)
			peel_nodes.append(peel)
	var guard_root := world_root.get_node_or_null("GuardSpawns")
	if guard_root != null:
		for child in guard_root.get_children():
			var marker := child as GuardSpawnPoint
			if marker == null:
				continue
			var guard_node := Guard.new()
			guard_node.position = marker.position
			guard_node.move_speed = marker.speed
			guard_node.target = player
			_actor_root().add_child(guard_node)
			guard_node.caught_player.connect(_on_guard_caught)
			guards.append(guard_node)


func _spawn_progress_props(room_id: String) -> void:
	if room_id == "cult_hq":
		var delivery_positions := [
			_room_marker("ProgressMarkers/DeliveryStatue", Vector2(94, 214)),
			_room_marker("ProgressMarkers/DeliveryEngine", Vector2(546, 214)),
			_room_marker("ProgressMarkers/DeliveryArchive", Vector2(320, 198))
		]
		for index in range(GameState.get_counter("boxes_delivered")):
			_spawn_static_sprite("res://assets/props/sacred_box.png", delivery_positions[index])
	elif room_id == "engine_room":
		if GameState.is_claimed("fuel_left"):
			_spawn_static_sprite(
				"res://assets/props/banana_fuel.png",
				_room_marker("ProgressMarkers/FuelLeft", Vector2(142, 111))
			)
		if GameState.is_claimed("fuel_right"):
			_spawn_static_sprite(
				"res://assets/props/banana_fuel.png",
				_room_marker("ProgressMarkers/FuelRight", Vector2(160, 111))
			)
		if GameState.is_claimed("fuel_apple"):
			_spawn_static_sprite(
				"res://assets/props/apple.png",
				_room_marker("ProgressMarkers/FuelApple", Vector2(178, 111))
			)
	elif room_id == "quarters" and GameState.is_claimed("locker_4"):
		_spawn_actor(
			{
				"kind": "cavendish",
				"pos": _room_marker("ProgressMarkers/Cavendish", Vector2(200, 122)),
				"facing": 0
			}
		)


func _spawn_static_sprite(texture_path: String, world_position: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(texture_path)
	sprite.position = world_position
	sprite.z_index = 3
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_actor_root().add_child(sprite)
	return sprite


func _refresh_objective() -> void:
	if not is_instance_valid(hud) or room_data.is_empty():
		return
	var boxes := GameState.get_counter("boxes_delivered")
	var seals := GameState.get_counter("seals")
	var fuel := GameState.get_counter("fuel_loaded")
	var carrying := bool(GameState.get_flag("carrying_box", false))
	var objective := str(room_data.get("objective", ""))
	if current_room == "temple_interior" and bool(GameState.get_flag("prayed", false)):
		objective = "Leave the temple"
	elif current_room == "sewer_explore" and bool(GameState.get_flag("window_seen", false)):
		objective = "Descend the hidden stairs"
	elif current_room == "cult_hq":
		if carrying:
			var target := int(GameState.get_flag("box_target", 0))
			var names := ["purple mark", "engine machinery", "central desk"]
			objective = "Deliver the box to the " + names[clampi(target, 0, 2)]
		elif boxes < 3:
			objective = "Deliver three Sacred Boxes (" + str(boxes) + "/3)"
		elif seals < 3:
			objective = "Earn three security seals (" + str(seals) + "/3)"
		else:
			objective = "Use the sealed exit"
	elif current_room == "storage":
		objective = (
			"Take Sacred Box " + str(mini(boxes + 1, 3)) + "/3"
			if not carrying
			else "Return to headquarters"
		)
	elif current_room == "engine_room":
		if GameState.is_claimed("engine_complete"):
			objective = "Return to headquarters"
		elif fuel < 3:
			objective = "Load three fuel units (" + str(fuel) + "/3)"
		else:
			objective = "Activate the Ripening Engine"
	elif current_room == "statue_room" and GameState.is_claimed("statue_polished"):
		objective = "Return to headquarters"
	elif current_room == "quarters" and GameState.is_claimed("locker_4"):
		objective = "Return to headquarters"
	hud.set_objective(objective)
	_refresh_quest_marker()


func _quest_event_for_state() -> String:
	var boxes: int = GameState.get_counter("boxes_delivered")
	var seals: int = GameState.get_counter("seals")
	var fuel: int = GameState.get_counter("fuel_loaded")
	var carrying: bool = bool(GameState.get_flag("carrying_box", false))
	match current_room:
		"temple_exterior":
			return "enter_temple"
		"temple_interior":
			return "leave_temple" if bool(GameState.get_flag("prayed", false)) else "pray_at_altar"
		"street":
			return "fall_into_manhole"
		"sewer_explore":
			return (
				"descend_to_lobby"
				if bool(GameState.get_flag("window_seen", false))
				else "inspect_cult_window"
			)
		"cult_lobby":
			return "cult_induction"
		"cult_hq":
			if carrying:
				var target_index: int = int(GameState.get_flag("box_target", 0))
				return ["deliver_box_statue", "deliver_box_engine", "deliver_box_archive"][
					clampi(target_index, 0, 2)
				]
			if boxes < 3:
				return (
					"go_storage"
					if bool(GameState.get_flag("foreman_briefed", false))
					else "talk_foreman"
				)
			if seals < 3:
				if not GameState.is_claimed("statue_polished"):
					return "go_statue"
				if not GameState.is_claimed("engine_complete"):
					return "go_engine"
				if not GameState.is_claimed("locker_4"):
					return "go_quarters"
				return "talk_foreman"
			return "attempt_escape"
		"storage":
			return "return_from_storage" if carrying else "pick_up_box"
		"statue_room":
			return (
				"return_from_statue"
				if GameState.is_claimed("statue_polished")
				else "polish_statue"
			)
		"engine_room":
			if GameState.is_claimed("engine_complete"):
				return "return_from_engine"
			if fuel < 3:
				if not GameState.is_claimed("fuel_left"):
					return "load_banana_fuel_left"
				if not GameState.is_claimed("fuel_right"):
					return "load_banana_fuel_right"
				return "load_apple"
			return "activate_engine"
		"quarters":
			return (
				"return_from_quarters"
				if GameState.is_claimed("locker_4")
				else "search_locker_4"
			)
		"chase":
			return "finish_chase"
	return ""


func _quest_position_for_event(event_name: String) -> Variant:
	for candidate in interactables:
		if not is_instance_valid(candidate):
			continue
		if str(candidate.event_name) != event_name:
			continue
		if not candidate.is_available() or not InteractionRules.is_available(event_name):
			continue
		return candidate.global_position
	for trigger in triggers:
		if str(trigger.get("event", "")) != event_name:
			continue
		var rect: Rect2 = trigger.get("rect", Rect2())
		return rect.get_center()
	return null


func _refresh_quest_marker() -> void:
	if not is_instance_valid(hud) or not is_instance_valid(player) or busy or ending_active:
		if is_instance_valid(hud):
			hud.clear_quest_target()
		return
	var quest_event: String = _quest_event_for_state()
	if quest_event.is_empty():
		hud.clear_quest_target()
		return
	var target_value: Variant = _quest_position_for_event(quest_event)
	if target_value is Vector2:
		var target_position: Vector2 = target_value
		hud.set_quest_target(target_position, player, quest_event)
	else:
		hud.clear_quest_target()


func _on_player_footstep() -> void:
	if busy or current_room.is_empty():
		return
	var volume := -22.0
	var pitch := randf_range(0.92, 1.08)
	if current_room == "sewer_explore":
		volume = -17.0
		pitch *= 0.82
	AudioManager.play_sfx("res://assets/audio/footstep.wav", volume, pitch)


func _spawn_visual_burst(texture_path: String, origin: Vector2, count: int) -> void:
	if not is_instance_valid(world_root):
		return
	for index in range(count):
		var sprite := Sprite2D.new()
		sprite.texture = load(texture_path)
		sprite.position = origin
		sprite.scale = Vector2.ONE * randf_range(0.25, 0.55)
		sprite.z_index = 40
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		world_root.add_child(sprite)
		var angle := randf_range(0.0, TAU)
		var burst_distance: float = randf_range(18.0, 42.0)
		var target: Vector2 = origin + Vector2.from_angle(angle) * burst_distance
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(sprite, "position", target, randf_range(0.45, 0.8))
		tween.tween_property(sprite, "modulate:a", 0.0, randf_range(0.45, 0.8))
		tween.tween_property(sprite, "rotation", randf_range(-4.0, 4.0), randf_range(0.45, 0.8))
		tween.set_parallel(false)
		tween.tween_callback(sprite.queue_free)


func _make_fall_streak_field(parent: Node2D) -> Node2D:
	var field: Node2D = Node2D.new()
	field.name = "FallSpeedStreaks"
	field.z_index = 22
	parent.add_child(field)
	for index in range(30):
		var streak: ColorRect = ColorRect.new()
		streak.position = Vector2(
			18.0 + float((index * 43) % 284), float((index * 67) % 560) - 80.0
		)
		streak.size = Vector2(1.0 + float(index % 2), 9.0 + float((index * 5) % 25))
		streak.color = Color(0.66, 0.84, 0.9, 0.14 + float(index % 4) * 0.06)
		streak.mouse_filter = Control.MOUSE_FILTER_IGNORE
		field.add_child(streak)
	return field


func _make_fall_debris(parent: Node2D) -> Array[Polygon2D]:
	var pieces: Array[Polygon2D] = []
	for index in range(9):
		var piece: Polygon2D = Polygon2D.new()
		piece.polygon = PackedVector2Array(
			[Vector2(-2.0, -1.0), Vector2(2.0, -2.0), Vector2(3.0, 1.0), Vector2(-1.0, 2.0)]
		)
		piece.color = Color(0.28 + float(index % 3) * 0.06, 0.31, 0.34, 0.9)
		piece.position = Vector2(38.0 + float((index * 71) % 244), 185.0 + float(index * 47))
		piece.rotation = float(index) * 0.41
		piece.z_index = 24
		parent.add_child(piece)
		pieces.append(piece)
	return pieces


func _make_fall_shoe(parent: Node2D, origin: Vector2) -> Polygon2D:
	var shoe: Polygon2D = Polygon2D.new()
	shoe.name = "LostShoe"
	shoe.polygon = PackedVector2Array(
		[
			Vector2(-5.0, -2.0),
			Vector2(1.0, -3.0),
			Vector2(6.0, 1.0),
			Vector2(6.0, 4.0),
			Vector2(-5.0, 4.0)
		]
	)
	shoe.color = Color(0.09, 0.075, 0.09, 1.0)
	shoe.position = origin
	shoe.z_index = 32
	parent.add_child(shoe)
	return shoe


func _fall_impact(stage: Node2D, flash: ColorRect, direction: float, strength: float) -> void:
	stage.position = Vector2(direction * strength, -strength * 0.45)
	flash.modulate.a = 0.42
	var impact_tween: Tween = stage.create_tween()
	impact_tween.set_parallel(true)
	(
		impact_tween
		. tween_property(stage, "position", Vector2.ZERO, 0.15)
		. set_trans(Tween.TRANS_ELASTIC)
		. set_ease(Tween.EASE_OUT)
	)
	impact_tween.tween_property(flash, "modulate:a", 0.0, 0.11)


func _make_cutscene_actor(sheet_path: String, screen_position: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(sheet_path)
	sprite.region_enabled = true
	sprite.region_rect = Rect2(0, 0, 16, 16)
	sprite.position = screen_position
	sprite.scale = Vector2(2.0, 2.0)
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return sprite


func _start_shake(strength: float, duration: float) -> void:
	shake_strength = maxf(shake_strength, strength)
	shake_time = maxf(shake_time, duration)


func _update_camera_shake(delta: float) -> void:
	if not is_instance_valid(player) or not is_instance_valid(player.camera):
		return
	if shake_time > 0.0:
		shake_time -= delta
		player.camera.offset = Vector2(
			randf_range(-shake_strength, shake_strength),
			randf_range(-shake_strength, shake_strength)
		)
		shake_strength = maxf(0.0, shake_strength - delta * 3.0)
	else:
		player.camera.offset = Vector2.ZERO


func _fade_to(alpha: float, duration: float) -> void:
	var tween := create_tween()
	tween.tween_property(fade_rect, "modulate:a", alpha, maxf(0.01, duration))
	await tween.finished


func _release_interaction_key() -> void:
	while Input.is_action_pressed("interact") or Input.is_action_pressed("ui_accept"):
		await get_tree().process_frame


func _toggle_pause() -> void:
	if busy or dialogue.is_open or ending_active:
		return
	paused_by_menu = not paused_by_menu
	get_tree().paused = paused_by_menu
	if paused_by_menu:
		_show_pause_layer()
	else:
		_hide_pause_layer()


func _show_pause_layer() -> void:
	pause_layer = PauseUI.instantiate() as PauseMenu
	add_child(pause_layer)
	pause_layer.resume_requested.connect(_toggle_pause)
	pause_layer.title_requested.connect(_return_to_title_from_pause)


func _return_to_title_from_pause() -> void:
	get_tree().paused = false
	paused_by_menu = false
	_hide_pause_layer()
	_show_title()


func _hide_pause_layer() -> void:
	if is_instance_valid(pause_layer):
		pause_layer.queue_free()
	pause_layer = null
