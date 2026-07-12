extends CanvasLayer

signal start_new
signal quit_requested

const SETTINGS_PATH: String = "user://beneath_the_peel_settings.cfg"

var selector_target_y: float = 0.0
var active_overlay: Control = null
var previous_focus: Control = null
var settings: ConfigFile = ConfigFile.new()
var narrator_time: float = 0.0

@onready var root: Control = %Root
@onready var content: HBoxContainer = %Content
@onready var title_block: VBoxContainer = %TitleBlock
@onready var menu_panel: PanelContainer = %MenuPanel
@onready var narrator_accent: TextureRect = %NarratorAccent
@onready var selector: TextureRect = %Selector
@onready var begin_button: Button = %BeginButton
@onready var options_button: Button = %OptionsButton
@onready var credits_button: Button = %CreditsButton
@onready var quit_button: Button = %QuitButton
@onready var options_overlay: Control = %OptionsOverlay
@onready var master_slider: HSlider = %MasterSlider
@onready var volume_value: Label = %VolumeValue
@onready var fullscreen_toggle: CheckButton = %FullscreenToggle
@onready var options_back_button: Button = %OptionsBackButton
@onready var info_overlay: Control = %InfoOverlay
@onready var info_back_button: Button = %InfoBackButton


func _ready() -> void:
	layer = 50
	process_mode = Node.PROCESS_MODE_ALWAYS
	_connect_menu_buttons()
	_load_settings()
	master_slider.value_changed.connect(_on_master_volume_changed)
	fullscreen_toggle.toggled.connect(_on_fullscreen_toggled)
	options_back_button.pressed.connect(_close_overlay)
	info_back_button.pressed.connect(_close_overlay)
	AudioManager.play_music("res://assets/audio/temple_drone.wav", -24.0, 0.8)
	AudioManager.play_ambient("res://assets/audio/rain_loop.wav", -25.0)
	begin_button.grab_focus()
	_on_button_focused(begin_button)
	_animate_intro()


func _process(delta: float) -> void:
	selector.position.y = lerpf(selector.position.y, selector_target_y, minf(1.0, delta * 18.0))
	narrator_time += delta
	var pulse: float = 0.32 + sin(narrator_time * 0.72) * 0.035
	narrator_accent.modulate.a = pulse


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and active_overlay != null:
		_close_overlay()
		get_viewport().set_input_as_handled()


func _connect_menu_buttons() -> void:
	begin_button.pressed.connect(func() -> void: start_new.emit())
	options_button.pressed.connect(_show_options)
	credits_button.pressed.connect(_show_credits)
	quit_button.pressed.connect(func() -> void: quit_requested.emit())
	for button_value in _menu_buttons():
		var button: Button = button_value as Button
		button.focus_entered.connect(_on_button_focused.bind(button))
		button.mouse_entered.connect(_focus_button.bind(button))


func _focus_button(button: Button) -> void:
	button.grab_focus()


func _menu_buttons() -> Array:
	return [begin_button, options_button, credits_button, quit_button]


func _animate_intro() -> void:
	content.modulate.a = 0.0
	narrator_accent.modulate.a = 0.0

	var tween: Tween = create_tween()
	tween.set_parallel(true)

	tween.tween_property(
		content,
		"modulate:a",
		1.0,
		0.45
	)

	(
		tween
		.tween_property(
			narrator_accent,
			"modulate:a",
			0.32,
			0.9
		)
		.set_delay(0.2)
	)


func _on_button_focused(button: Button) -> void:
	if not is_instance_valid(button) or not button.is_visible_in_tree():
		return
	selector.visible = active_overlay == null
	selector_target_y = (
		button.global_position.y - root.global_position.y + (button.size.y - selector.size.y) * 0.5
	)
	AudioManager.play_sfx("res://assets/audio/dialogue_tick.wav", -25.0, 1.08)


func _show_options() -> void:
	_show_overlay(options_overlay, options_back_button)


func _show_credits() -> void:
	_show_overlay(info_overlay, info_back_button)


func _show_overlay(overlay: Control, focus_target: Control) -> void:
	if active_overlay != null:
		active_overlay.visible = false
	previous_focus = get_viewport().gui_get_focus_owner()
	active_overlay = overlay
	active_overlay.visible = true
	selector.visible = false
	focus_target.grab_focus()
	active_overlay.modulate.a = 0.0
	var tween: Tween = create_tween()
	tween.tween_property(active_overlay, "modulate:a", 1.0, 0.16)


func _close_overlay() -> void:
	if active_overlay == null:
		return
	active_overlay.visible = false
	active_overlay = null
	selector.visible = true
	if is_instance_valid(previous_focus):
		previous_focus.grab_focus()
	else:
		begin_button.grab_focus()
	var focus_owner: Control = get_viewport().gui_get_focus_owner()
	if focus_owner is Button:
		_on_button_focused(focus_owner as Button)


func _load_settings() -> void:
	var error_code: Error = settings.load(SETTINGS_PATH)
	var master_volume: float = 82.0
	var fullscreen_enabled: bool = (
		DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	)
	if error_code == OK:
		master_volume = float(settings.get_value("audio", "master_percent", master_volume))
		fullscreen_enabled = bool(settings.get_value("display", "fullscreen", fullscreen_enabled))
	master_slider.value = master_volume
	fullscreen_toggle.button_pressed = fullscreen_enabled
	_apply_master_volume(master_volume)
	_apply_fullscreen(fullscreen_enabled)
	_update_volume_label(master_volume)


func _save_settings() -> void:
	settings.set_value("audio", "master_percent", master_slider.value)
	settings.set_value("display", "fullscreen", fullscreen_toggle.button_pressed)
	var error_code: Error = settings.save(SETTINGS_PATH)
	if error_code != OK:
		push_warning("Unable to save menu settings: " + str(error_code))


func _on_master_volume_changed(value: float) -> void:
	_apply_master_volume(value)
	_update_volume_label(value)
	_save_settings()


func _on_fullscreen_toggled(enabled: bool) -> void:
	_apply_fullscreen(enabled)
	_save_settings()


func _apply_master_volume(percent: float) -> void:
	var bus_index: int = AudioServer.get_bus_index("Master")
	if bus_index < 0:
		return
	var linear_value: float = clampf(percent / 100.0, 0.0, 1.0)
	AudioServer.set_bus_mute(bus_index, linear_value <= 0.001)
	AudioServer.set_bus_volume_db(bus_index, linear_to_db(maxf(0.001, linear_value)))


func _apply_fullscreen(enabled: bool) -> void:
	DisplayServer.window_set_mode(
		DisplayServer.WINDOW_MODE_FULLSCREEN if enabled else DisplayServer.WINDOW_MODE_WINDOWED
	)


func _update_volume_label(value: float) -> void:
	volume_value.text = str(int(round(value))) + "%"
