extends Node2D

const LIGHT_TEXTURE := preload("res://assets/fx/radial_light.png")

var canvas_modulate: CanvasModulate


func configure(room_id: String, player_node: Node2D) -> void:
	var profile := _profile(room_id)
	if profile.is_empty():
		return

	canvas_modulate = CanvasModulate.new()
	canvas_modulate.color = profile.get("ambient", Color.WHITE)
	add_child(canvas_modulate)

	var player_light: Dictionary = profile.get("player", {})
	if not player_light.is_empty() and is_instance_valid(player_node):
		var light := _make_light(player_light)
		light.position = Vector2(0, -2)
		player_node.add_child(light)

	for light_data in profile.get("static", []):
		var static_light := _make_light(light_data)
		static_light.position = light_data.get("pos", Vector2.ZERO)
		add_child(static_light)


func _make_light(data: Dictionary) -> PointLight2D:
	var light := PointLight2D.new()
	light.texture = LIGHT_TEXTURE
	light.texture_scale = float(data.get("scale", 1.0))
	light.energy = float(data.get("energy", 0.7))
	light.color = data.get("color", Color(1.0, 0.72, 0.38))
	light.shadow_enabled = false
	light.z_index = 100
	return light


func _profile(room_id: String) -> Dictionary:
	var profile: Dictionary = {}
	match room_id:
		"temple_exterior":
			profile = {
				"ambient": Color(0.73, 0.77, 0.91),
				"static":
				[
					{"pos": Vector2(145, 89), "scale": 0.52, "energy": 0.55},
					{"pos": Vector2(175, 89), "scale": 0.52, "energy": 0.55}
				]
			}
		"temple_interior":
			profile = {
				"ambient": Color(0.68, 0.64, 0.78),
				"player": {"scale": 0.78, "energy": 0.34, "color": Color(0.82, 0.87, 1.0)},
				"static":
				[
					{"pos": Vector2(132, 41), "scale": 0.62, "energy": 0.85},
					{"pos": Vector2(188, 41), "scale": 0.62, "energy": 0.85}
				]
			}
		"street":
			profile = {
				"ambient": Color(0.70, 0.75, 0.90),
				"player": {"scale": 0.72, "energy": 0.28, "color": Color(0.72, 0.82, 1.0)}
			}
		"sewer_explore":
			profile = {
				"ambient": Color(0.52, 0.61, 0.69),
				"player": {"scale": 1.28, "energy": 0.82, "color": Color(0.70, 0.88, 0.92)},
				"static":
				[
					{
						"pos": Vector2(486, 105),
						"scale": 0.72,
						"energy": 0.45,
						"color": Color(0.82, 0.33, 0.28)
					}
				]
			}
		"cult_lobby", "cult_hq", "storage", "statue_room", "engine_room", "quarters":
			profile = {
				"ambient": Color(0.66, 0.58, 0.72),
				"player": {"scale": 0.86, "energy": 0.38, "color": Color(0.92, 0.76, 0.52)}
			}
		"chase":
			profile = {
				"ambient": Color(0.74, 0.52, 0.56),
				"player": {"scale": 0.92, "energy": 0.42, "color": Color(1.0, 0.65, 0.35)}
			}
		_:
			profile = {}
	return profile
