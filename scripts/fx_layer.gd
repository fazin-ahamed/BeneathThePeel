extends Node2D

var mode: String = ""
var world_size: Vector2 = Vector2(320, 180)
var particles: Array[Dictionary] = []
var elapsed: float = 0.0
var rng := RandomNumberGenerator.new()


func configure(value: String, size: Vector2) -> void:
	mode = value
	world_size = size
	rng.seed = 198731
	particles.clear()
	var count := 0
	match mode:
		"rain":
			count = int(world_size.x / 3.0)
		"dust":
			count = int(world_size.x / 14.0)
		"sewer":
			count = int(world_size.x / 10.0)
		"sparks":
			count = 24
		"dawn":
			count = 18
		_:
			count = 0
	for index in range(count):
		particles.append(_new_particle(index))
	queue_redraw()


func _new_particle(_index: int = 0) -> Dictionary:
	match mode:
		"rain":
			return {
				"pos":
				Vector2(rng.randf_range(0.0, world_size.x), rng.randf_range(0.0, world_size.y)),
				"speed": rng.randf_range(85.0, 145.0),
				"length": rng.randf_range(3.0, 7.0)
			}
		"dust", "dawn":
			return {
				"pos":
				Vector2(
					rng.randf_range(0.0, world_size.x), rng.randf_range(24.0, world_size.y - 10.0)
				),
				"speed": rng.randf_range(2.0, 7.0),
				"phase": rng.randf_range(0.0, TAU)
			}
		"sewer":
			return {
				"pos":
				Vector2(
					rng.randf_range(16.0, world_size.x - 16.0),
					rng.randf_range(world_size.y - 31.0, world_size.y - 7.0)
				),
				"speed": rng.randf_range(8.0, 20.0),
				"length": rng.randf_range(3.0, 12.0)
			}
		"sparks":
			return {
				"pos":
				Vector2(
					rng.randf_range(world_size.x * 0.37, world_size.x * 0.63),
					rng.randf_range(58.0, 120.0)
				),
				"speed": rng.randf_range(18.0, 48.0),
				"phase": rng.randf_range(0.0, TAU)
			}
	return {"pos": Vector2.ZERO}


func _process(delta: float) -> void:
	elapsed += delta
	if mode.is_empty() or mode == "none":
		return
	for particle in particles:
		var pos: Vector2 = particle.get("pos", Vector2.ZERO)
		match mode:
			"rain":
				pos += Vector2(-28.0, float(particle.get("speed", 100.0))) * delta
				if pos.y > world_size.y + 8.0:
					pos.y = -8.0
					pos.x = rng.randf_range(0.0, world_size.x)
				if pos.x < -8.0:
					pos.x = world_size.x + 8.0
			"dust", "dawn":
				var phase := float(particle.get("phase", 0.0))
				pos.x += sin(elapsed * 0.8 + phase) * delta * 2.0
				pos.y -= float(particle.get("speed", 3.0)) * delta
				if pos.y < 18.0:
					pos.y = world_size.y - 8.0
			"sewer":
				pos.x += float(particle.get("speed", 10.0)) * delta
				if pos.x > world_size.x:
					pos.x = 0.0
			"sparks":
				var phase := float(particle.get("phase", 0.0))
				pos += Vector2(cos(phase), -1.0) * float(particle.get("speed", 30.0)) * delta
				if pos.y < 42.0:
					pos = Vector2(
						rng.randf_range(world_size.x * 0.4, world_size.x * 0.6),
						rng.randf_range(90.0, 125.0)
					)
			_:
				pass
		particle["pos"] = pos
	queue_redraw()


func _draw() -> void:
	match mode:
		"rain":
			for particle in particles:
				var pos: Vector2 = particle["pos"]
				var length := float(particle.get("length", 5.0))
				draw_line(pos, pos + Vector2(-2.0, length), Color(0.36, 0.47, 0.67, 0.55), 1.0)
		"dust":
			for particle in particles:
				draw_rect(Rect2(particle["pos"], Vector2(1, 1)), Color(0.75, 0.62, 0.48, 0.28))
		"dawn":
			for particle in particles:
				draw_rect(Rect2(particle["pos"], Vector2(1, 1)), Color(1.0, 0.82, 0.48, 0.4))
		"sewer":
			for particle in particles:
				var pos: Vector2 = particle["pos"]
				draw_line(
					pos,
					pos + Vector2(float(particle.get("length", 6.0)), 0),
					Color(0.2, 0.61, 0.66, 0.42),
					1.0
				)
		"sparks":
			for particle in particles:
				draw_rect(Rect2(particle["pos"], Vector2(2, 2)), Color(1.0, 0.57, 0.18, 0.8))
		"alarm":
			var alpha := 0.08 + 0.08 * (sin(elapsed * 8.0) * 0.5 + 0.5)
			draw_rect(Rect2(Vector2.ZERO, world_size), Color(0.65, 0.02, 0.08, alpha))
