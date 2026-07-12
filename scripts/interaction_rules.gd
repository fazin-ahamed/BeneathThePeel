extends RefCounted


static func is_available(event_name: String) -> bool:
	var boxes := GameState.get_counter("boxes_delivered")
	var fuel := GameState.get_counter("fuel_loaded")
	var carrying := bool(GameState.get_flag("carrying_box", false))
	var target := int(GameState.get_flag("box_target", -1))
	var available := true

	match event_name:
		"enter_temple":
			available = not bool(GameState.get_flag("entered_temple", false))
		"pray_at_altar":
			available = not bool(GameState.get_flag("prayed", false))
		"fall_into_manhole":
			available = not bool(GameState.get_flag("washed_up", false))
		"inspect_cult_window":
			available = not bool(GameState.get_flag("window_seen", false))
		"cult_induction":
			available = not bool(GameState.get_flag("inducted", false))
		"deliver_box_statue":
			available = carrying and target == 0
		"deliver_box_engine":
			available = carrying and target == 1
		"deliver_box_archive":
			available = carrying and target == 2
		"pick_up_box":
			available = boxes < 3 and not carrying
		"polish_statue":
			available = not GameState.is_claimed("statue_polished")
		"load_banana_fuel_left":
			available = not GameState.is_claimed("fuel_left")
		"load_banana_fuel_right":
			available = not GameState.is_claimed("fuel_right")
		"load_apple":
			available = not GameState.is_claimed("fuel_apple")
		"activate_engine":
			available = not GameState.is_claimed("engine_complete")
		"search_locker_1":
			available = not GameState.is_claimed("locker_1")
		"search_locker_2":
			available = not GameState.is_claimed("locker_2")
		"search_locker_3":
			available = not GameState.is_claimed("locker_3")
		"search_locker_4":
			available = not GameState.is_claimed("locker_4")
		"search_locker_5":
			available = not GameState.is_claimed("locker_5")
		"attempt_escape":
			available = not GameState.is_claimed("escape_sequence")
		_:
			available = true

	return available


static func dynamic_prompt(event_name: String, fallback: String) -> String:
	match event_name:
		"pick_up_box":
			return "Take Sacred Box " + str(GameState.get_counter("boxes_delivered") + 1) + "/3"
		"activate_engine":
			return "Activate the engine (" + str(GameState.get_counter("fuel_loaded")) + "/3 fuel)"
		_:
			return fallback
