extends Node
## End-to-end gameplay test (runner node, loaded by gameplay_test.gd) on the real main scene with simulated input.
## Plays the opening survival loop: gather wood, fibre and stone, craft
## rope and a hatchet, chop a palm, take the rod from the camp chest, fish,
## cook, eat, dive (oxygen), spear a fish, build a shelter, sleep, repair
## and sail the rowboat, save, reload and check everything came back, and
## die and respawn.
##   godot --headless --path game --script res://tools/gameplay_test.gd

var failures := 0
var player: PlayerController
var world: Node


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = Game
	game.reset()
	game.pending_start = "new"
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://savegame.json"))
	get_tree().change_scene_to_file("res://scenes/main.tscn")
	await _frames(20)
	world = get_tree().current_scene
	player = get_tree().get_first_node_in_group("player") as PlayerController
	_check(game.is_playing(), "new game starts in play mode")
	_check(game.inventory.count("coconut") == 1, "starts with a coconut")
	_check(game.current_objective().get("id", "") == "wood", "first objective is wood")
	var stats0: Dictionary = game.stats.duplicate()

	# --- Gather wood from driftwood --------------------------------------
	var drift := _find(func(n): return n is Pickup and n.item_id == "wood" and n.respawn_seconds > 0.0)
	await _approach(drift)
	_check(player.focus == drift, "driftwood is the interaction focus")
	var acts: Array = drift.actions(player)
	_check(not acts.is_empty() and acts[0]["action"] == "interact", "prompt offers to collect wood (%s)" % (acts[0]["text"] if acts.size() else "none"))
	await _tap("interact")
	_check(game.inventory.count("wood") == 3, "collected 3 wood (have %d)" % game.inventory.count("wood"))
	_check(not drift.is_available(), "driftwood disappears after pickup")
	var other := _find(func(n): return n is Pickup and n.item_id == "wood" and n.respawn_seconds > 0.0 and n != drift)
	await _approach(other)
	await _tap("interact")
	_check(game.current_objective().get("id", "") == "fiber", "wood objective complete (now %s)" % game.current_objective().get("id", ""))

	# --- Fibre from bushes ------------------------------------------------
	for i in 2:
		var bush := _find(func(n): return n is Pickup and n.item_id == "fiber" and n.is_available() and n.amount == 2)
		await _approach(bush)
		await _tap("interact")
	_check(game.inventory.count("fiber") >= 4, "gathered fibre (have %d)" % game.inventory.count("fiber"))
	var bush_hidden := _find(func(n): return n is Pickup and n.item_id == "fiber" and not n.is_available())
	_check(bush_hidden != null, "harvested bush instance is hidden")

	# --- Craft rope through the pack screen -------------------------------
	await _tap("inventory")
	var inv_menu: InventoryMenu = world.inventory_menu
	_check(inv_menu.is_open and game.ui_open, "inventory opens with the inventory action")
	var rope_button := _recipe_button(inv_menu, "rope")
	_check(rope_button != null and not rope_button.disabled, "rope recipe is craftable")
	rope_button.pressed.emit()
	await _frames(2)
	_check(game.inventory.count("rope") == 1, "crafted rope")
	await _tap("inventory")
	_check(not inv_menu.is_open and not game.ui_open, "inventory closes")

	# --- Stones -------------------------------------------------------------
	for i in 2:
		var pebble := _find(func(n): return n is Pickup and n.item_id == "stone" and n.is_available())
		await _approach(pebble)
		await _tap("interact")
	_check(game.inventory.count("stone") >= 2, "picked up stones (have %d)" % game.inventory.count("stone"))

	# --- Hatchet and chopping -----------------------------------------------
	_craft(inv_menu, "hatchet")
	_check(game.inventory.count("hatchet") == 1, "crafted a stone hatchet")
	_select("hatchet")
	await _frames(3)
	_check(player.held.current_id == "hatchet" and player.held.node != null, "hatchet shows in the hand")
	var palm := _find(func(n): return n is ResourceNode and n.kind == "palm")
	await _approach(palm, 1.3)
	var palm_acts: Array = palm.actions(player)
	_check(palm_acts.any(func(a): return a["action"] == "use_tool"), "palm offers chopping with the hatchet")
	var wood_before: int = game.inventory.count("wood")
	for i in 3:
		await _tap("use_tool")
		await _frames(8)
	_check(game.inventory.count("wood") >= wood_before + 3, "chopping gives wood (%d -> %d)" % [wood_before, game.inventory.count("wood")])
	_check(int(game.counters.get("chop", 0)) == 3, "three chops recorded")
	await _tap("interact")
	_check(game.inventory.count("coconut") >= 2, "shaking the palm drops a coconut")

	# --- Camp chest: take the fishing rod -----------------------------------
	var chest := _find(func(n): return n is StorageBox)
	await _approach(chest)
	await _tap("interact")
	var storage: StorageMenu = world.storage_menu
	_check(storage.is_open, "camp chest opens")
	storage._take_all()
	await _frames(2)
	_check(game.inventory.count("fishing_rod") == 1, "took the fishing rod")
	storage.close()
	await _frames(2)
	_check(game.current_objective().get("id", "") == "catch", "objective is now catching a fish (%s)" % game.current_objective().get("id", ""))

	# --- Fishing --------------------------------------------------------------
	_select("fishing_rod")
	var shore := _shore_spot(Vector3(30.0, 0.0, 22.0), Vector3(1, 0, 0))
	player.teleport(shore, 90.0)
	await _frames(15)
	var rod := player.fishing
	Input.action_press("use_tool")
	await _frames(50)
	Input.action_release("use_tool")
	await _frames(60)
	_check(rod.state == FishingRod.S.WAIT, "bobber lands in the water and waits (state %d)" % rod.state)
	var t := 0
	while rod.state != FishingRod.S.BITE and t < 900:
		await _frames(1)
		t += 1
	_check(rod.state == FishingRod.S.BITE, "a fish bites within 15 s")
	await _tap("use_tool")
	_check(rod.state == FishingRod.S.REEL, "hooked the fish")
	var fish_before := _raw_fish_count()
	t = 0
	while rod.state == FishingRod.S.REEL and t < 3000:
		if rod.tension < 0.62:
			Input.action_press("use_tool")
		else:
			Input.action_release("use_tool")
		await _frames(1)
		t += 1
	Input.action_release("use_tool")
	_check(_raw_fish_count() == fish_before + 1, "reeled in a fish (raw fish %d)" % _raw_fish_count())
	_check(int(game.counters.get("catch", 0)) >= 1, "catch recorded")

	# --- Cooking --------------------------------------------------------------
	_select("hatchet")
	await _frames(5)
	var fire := _find(func(n): return n is CookingStation)
	await _approach(fire, 1.4)
	_check(player.focus == fire, "campfire is the focus")
	await _tap("interact")
	_check(player.is_busy(), "cooking keeps the player busy")
	await _frames(160)
	_check(_cooked_count() == 1, "cooked the fish")

	# --- Eating ---------------------------------------------------------------
	game.stats["hunger"] = 40.0
	_select_kind_suffix("_cooked")
	await _tap("use_tool")
	_check(game.stats["hunger"] > 60.0, "eating a cooked meal restores hunger (%.0f)" % game.stats["hunger"])
	_check(int(game.counters.get("eat_cooked", 0)) == 1, "cooked meal recorded")

	# --- Diving and oxygen ------------------------------------------------------
	var school := _find(func(n): return n is FishSchool and n.species in ["snapper", "tang"] and not n.fish.is_empty())
	var fish: Fish = school.fish[0]
	player.teleport(Vector3(fish.global_position.x - 2.0, 0.0, fish.global_position.z), 90.0)
	await _frames(30)
	_check(player.mode == PlayerController.Mode.SWIM, "swimming over the reef")
	Input.action_press("dive")
	await _frames(200)
	_check(player.mode == PlayerController.Mode.DIVE and player.is_head_underwater(), "diving underwater")
	_check(game.stats["oxygen"] < 100.0 - 5.0, "holding breath uses oxygen (%.0f)" % game.stats["oxygen"])
	var dive_depth := World.water_level() - player.global_position.y
	_check(dive_depth > 1.0 and dive_depth <= player.max_dive_depth + 0.15, "dive stays within reach of the fish (%.1f m down)" % dive_depth)
	var reveal := float(get_tree().current_scene.get("_reveal"))
	_check(reveal > 0.9, "water clears around the diver (reveal %.2f)" % reveal)

	# --- Spearfishing -----------------------------------------------------------
	game.inventory.add("wood", 2)
	game.inventory.add("stone", 1)
	game.inventory.add("rope", 1)
	_craft(inv_menu, "spear")
	_select("spear")
	await _frames(3)
	var caught_spear := false
	for attempt in 12:
		var target := _nearest_fish()
		if target == null:
			break
		var d := target.global_position - player.global_position
		player.model.rotation.y = atan2(d.x, d.z)
		if Vector2(d.x, d.z).length() > 2.5:
			player.global_position = target.global_position - Vector3(d.x, 0, d.z).normalized() * 1.6 + Vector3.DOWN * 0.4
		await _frames(2)
		await _tap("use_tool")
		await _frames(30)
		if int(game.counters.get("spear_catch", 0)) > 0:
			caught_spear = true
			break
	_check(caught_spear, "speared a fish underwater")
	Input.action_release("dive")
	await _frames(150)
	_check(player.mode == PlayerController.Mode.SWIM, "resurfaced after releasing dive")
	var o2 := float(game.stats["oxygen"])
	await _frames(60)
	_check(game.stats["oxygen"] > o2 or game.stats["oxygen"] >= 99.0, "oxygen recovers at the surface (%.0f)" % game.stats["oxygen"])

	# --- Building a shelter ------------------------------------------------------
	game.inventory.add("wood", 8)
	game.inventory.add("palm_frond", 6)
	game.inventory.add("rope", 2)
	_craft(inv_menu, "shelter_kit")
	_select("shelter_kit")
	player.teleport(Vector3(4.0, 2.0, 12.0), 0.0)
	await _frames(20)
	await _tap("use_tool")
	await _frames(5)
	_check(player.builder.active, "placement mode starts")
	var placed := false
	for yaw in [0.0, 90.0, 180.0, 270.0, 45.0, 135.0]:
		player.model.rotation.y = deg_to_rad(yaw)
		await _frames(4)
		if player.builder.valid:
			await _tap("use_tool")
			await _frames(4)
			placed = game.structures.size() == 1
			break
	_check(placed, "placed a lean-to shelter")
	var shelter := get_tree().current_scene.find_child("Structure_0", true, false)
	_check(shelter != null, "the shelter exists in the world")

	# --- Sleeping ----------------------------------------------------------------
	var bed := _find(func(n): return n is ShelterBed and n.save_id == "structure_0")
	await _approach(bed, 1.2)
	var hours_before: float = game.time_hours + game.day * 24.0
	await _tap("interact")
	await _frames(90)
	_check(game.time_hours + game.day * 24.0 > hours_before + 1.5, "sleeping passes time")
	_check(game.respawn_point.distance_to(bed.global_position) < 4.0, "respawn point moves to the shelter")

	# --- Day and night ------------------------------------------------------------
	var dn := get_tree().current_scene.get_node("DayNight") as DayNight
	var sun := get_tree().current_scene.get_node("DaylightRig/Sun") as DirectionalLight3D
	var hour_saved: float = game.time_hours
	game.time_hours = 12.0
	await _frames(3)
	var noon_energy := sun.light_energy
	var noon_dir := -sun.global_basis.z
	game.time_hours = 23.0
	await _frames(3)
	_check(sun.light_energy < noon_energy * 0.4, "night is darker than noon (%.2f vs %.2f)" % [sun.light_energy, noon_energy])
	_check(dn.sample(23.0)["daylight"] < 0.3 and dn.sample(12.0)["daylight"] > 0.99, "daylight shader global follows the clock")
	await _frames(40)
	_check(AudioManager.get("_night") > 0.9, "night ambience fades in after dark")
	game.time_hours = 16.5
	await _frames(3)
	_check((-sun.global_basis.z).angle_to(noon_dir) > deg_to_rad(5.0), "the sun moves across the day")
	game.time_hours = hour_saved
	await _frames(3)

	# --- Rowboat ----------------------------------------------------------------
	game.inventory.add("wood", 6)
	game.inventory.add("rope", 2)
	var boat: Boat = _find(func(n): return n is Boat and n.title == "rowboat")
	_check(boat.needs_repair, "the rowboat starts damaged")
	await _approach(boat, 1.6, true)
	await _tap("interact")
	_check(not boat.needs_repair, "repaired the rowboat")
	await _frames(5)
	await _tap("interact")
	_check(player.mode == PlayerController.Mode.BOAT and boat.driver == player, "boarded the rowboat")
	var boat_start: Vector3 = boat.global_position
	Input.action_press("move_forward")
	await _frames(180)
	Input.action_release("move_forward")
	var moved := Vector2(boat.global_position.x - boat_start.x, boat.global_position.z - boat_start.z).length()
	_check(moved > 3.0, "the rowboat moves under control (%.1f m)" % moved)
	_check(player.global_position.distance_to(boat.global_position) < 1.5, "the player rides in the boat")
	await _frames(30)
	await _tap("interact")
	await _frames(5)
	_check(player.mode != PlayerController.Mode.BOAT and boat.driver == null, "stepped out of the boat")

	# --- More islands: discovery, salvage and the signal fire -----------------------
	_check(get_tree().get_nodes_in_group("island").size() == 3, "three islands are loaded")
	var pk: Node3D = get_tree().current_scene.get_node("PalmKey")
	var pk_land: Vector3 = World.find_land_near(pk.global_position + Vector3(-6, 0, 4), 20.0)
	player.teleport(pk_land + Vector3.UP * 0.4, 0.0)
	await _frames(20)
	_check(Game.discovered.has("palm_key"), "reaching Palm Key discovers it")
	var wreck := _find(func(n): return n is Searchable and n.get_parent().name == "WreckRibs" and pk.is_ancestor_of(n))
	_check(wreck != null, "Palm Key has a searchable shipwreck")
	var wood_pk: int = Game.inventory.count("wood")
	await _approach(wreck, 2.2, true)
	await _tap("interact")
	_check(Game.inventory.count("wood") > wood_pk, "salvaged wood from the wreck")
	var look: Node3D = get_tree().current_scene.get_node("LookoutIsle")
	var signal_fire := _find(func(n): return n is SignalFire)
	_check(signal_fire != null and look.is_ancestor_of(signal_fire), "Lookout Isle has the signal fire")
	Game.inventory.add("wood", 10)
	Game.inventory.add("palm_frond", 4)
	await _approach(signal_fire, 1.6)
	_check(Game.discovered.has("lookout"), "reaching Lookout Isle discovers it")
	await _tap("interact")
	await _frames(5)
	_check(signal_fire.is_lit, "lit the signal fire")
	_check(world_menu("rescue_screen").is_open, "the rescue ending appears")
	world_menu("rescue_screen").close()
	await _frames(3)
	_check(Game.is_playing() and not Game.ui_open, "keep exploring after the rescue")

	# --- Needs over time -----------------------------------------------------------
	_check(game.stats["thirst"] < stats0["thirst"], "thirst drops over time (%.0f)" % game.stats["thirst"])

	# --- Save and load -----------------------------------------------------------
	var boat_pos: Vector3 = boat.global_position
	var drift_id: String = drift.save_id
	var wood_saved: int = game.inventory.count("wood")
	var obj_saved: int = game.objective_index
	_check(SaveManager.save_game(), "game saved")
	game.inventory.clear()
	SaveManager.load_and_restart()
	await _frames(25)
	player = get_tree().get_first_node_in_group("player") as PlayerController
	_check(game.is_playing(), "loaded game is playing")
	_check(game.inventory.count("wood") == wood_saved, "inventory restored (%d wood)" % game.inventory.count("wood"))
	_check(game.objective_index == obj_saved, "objective restored")
	_check(get_tree().current_scene.find_child("Structure_0", true, false) != null, "shelter rebuilt from the save")
	var boat2: Boat = _find(func(n): return n is Boat and n.title == "rowboat")
	_check(not boat2.needs_repair and boat2.global_position.distance_to(boat_pos) < 1.0, "rowboat state and position restored")
	var drift2 := _find(func(n): return n is Pickup and n.save_id == drift_id)
	_check(drift2 != null and not drift2.is_available(), "collected driftwood stays collected")

	# --- Death and respawn -----------------------------------------------------------
	game.damage(500.0)
	await _frames(3)
	_check(game.state == "dead" and world_menu("death_screen").is_open, "running out of health shows the death screen")
	world_menu("death_screen").respawn_requested.emit()
	world_menu("death_screen").close()
	await _frames(10)
	_check(game.is_playing() and player.global_position.distance_to(game.respawn_point) < 3.0, "respawned at the shelter")
	_check(game.stats["health"] > 0.0, "health restored on respawn")

	print("gameplay_test: %s (%d failure(s))" % ["PASS" if failures == 0 else "FAIL", failures])
	get_tree().quit(1 if failures else 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func world_menu(name: String) -> MenuBase:
	return get_tree().current_scene.get(name)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _tap(action: String) -> void:
	_send(action, true)
	await get_tree().physics_frame
	await get_tree().physics_frame
	_send(action, false)
	await get_tree().physics_frame


## Real input events, so both action state and _unhandled_input see them.
func _send(action: String, pressed: bool) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = pressed
	ev.strength = 1.0 if pressed else 0.0
	Input.parse_input_event(ev)


func _find(pred: Callable) -> Node:
	var best: Node = null
	var best_d := INF
	for n in get_tree().get_nodes_in_group("interactable") + get_tree().get_nodes_in_group("fish_schools_tmp"):
		if pred.call(n):
			var d: float = (n as Node3D).global_position.distance_to(player.global_position)
			if d < best_d:
				best_d = d
				best = n
	if best == null:
		for n in get_tree().current_scene.find_children("*", "", true, false):
			if pred.call(n):
				return n
	return best


## Puts the player `dist` metres from the target, facing it, trying spots
## around it until the target is the interaction focus (as a player would
## shuffle into place).
func _approach(target: Node3D, dist: float = 1.1, water_ok := false) -> void:
	if target == null:
		_check(false, "approach target exists")
		return
	var tp := target.global_position
	var spots := []
	for ring in [dist, dist * 0.7, dist * 1.4]:
		for i in 12:
			var a := TAU * i / 12.0
			var p: Vector3 = tp + Vector3(cos(a), 0, sin(a)) * ring
			var h: float = World.height_at(p.x, p.z)
			if water_ok:
				h = maxf(h, -0.5)
			elif h < World.water_level() + 0.1:
				continue
			if _blocked(Vector3(p.x, h + 0.9, p.z)):
				continue
			spots.append(Vector3(p.x, h + 0.3, p.z))
	spots.sort_custom(func(a, b): return a.y > b.y)
	for spot in spots:
		var d: Vector3 = tp - spot
		player.teleport(spot, rad_to_deg(atan2(d.x, d.z)))
		await _frames(10)
		if player.focus == target or not (target is Interactable):
			return
	await _frames(4)


func _blocked(p: Vector3) -> bool:
	var space := player.get_world_3d().direct_space_state
	var q := PhysicsShapeQueryParameters3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 0.3
	q.shape = sphere
	q.transform = Transform3D(Basis(), p)
	q.exclude = [player.get_rid()]
	for hit in space.intersect_shape(q, 4):
		if not (hit["collider"] is StaticBody3D and hit["collider"].get_parent() is IslandManager):
			return true
	return false


func _shore_spot(from: Vector3, dir: Vector3) -> Vector3:
	var p := from
	for i in 60:
		var nxt := p + dir * 0.5
		if World.height_at(nxt.x, nxt.z) < World.water_level() + 0.25:
			break
		p = nxt
	p.y = World.height_at(p.x, p.z) + 0.3
	return p


func _recipe_button(menu: InventoryMenu, out: String) -> Button:
	menu._refresh()
	var i := 0
	for r in ItemDB.RECIPES:
		if r["out"] == out:
			var row := menu._recipes.get_child(menu._recipes.get_child_count() - ItemDB.RECIPES.size() + i)
			for b in row.find_children("*", "Button", true, false):
				return b
		i += 1
	return null


func _craft(menu: InventoryMenu, out: String) -> void:
	for r in ItemDB.RECIPES:
		if r["out"] == out:
			menu._craft(r)


func _select(id: String) -> void:
	var game = Game
	for i in game.inventory.size():
		var s = game.inventory.get_slot(i)
		if s != null and s["id"] == id:
			if i >= game.HOTBAR_SIZE:
				game.inventory.swap(i, game.HOTBAR_SIZE - 1)
				i = game.HOTBAR_SIZE - 1
			game.select(i)
			return


func _select_kind_suffix(suffix: String) -> void:
	var game = Game
	for i in game.inventory.size():
		var s = game.inventory.get_slot(i)
		if s != null and String(s["id"]).ends_with(suffix):
			_select(s["id"])
			return


func _raw_fish_count() -> int:
	var game = Game
	var n := 0
	for sp in ItemDB.FISH:
		n += game.inventory.count(ItemDB.FISH[sp]["item"])
	return n


func _cooked_count() -> int:
	var game = Game
	var n := 0
	for s in game.inventory.slots:
		if s != null and String(s["id"]).ends_with("_cooked"):
			n += int(s["count"])
	return n


func _nearest_fish() -> Fish:
	var best: Fish = null
	var bd := INF
	for f in get_tree().get_nodes_in_group("fish"):
		var d: float = (f as Node3D).global_position.distance_to(player.global_position)
		if d < bd and (f as Fish).alive:
			bd = d
			best = f
	return best


func _check(ok: bool, what: String) -> void:
	print("  [%s] %s" % ["ok" if ok else "FAIL", what])
	if not ok:
		failures += 1
