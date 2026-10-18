extends Node
## See demo_video.gd. Drives the explorer with simulated controller input
## (walking is steered with the move actions, buttons are real input events),
## so everything on screen is the normal game reacting to input. A few items
## are handed over between scenes to keep the video short.

var world: GameWorld
var player: PlayerController


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	# Title screen.
	Game.pending_start = ""
	get_tree().change_scene_to_file("res://scenes/main.tscn")
	await _frames(60)

	# New game: gather on the beach.
	Game.reset()
	Game.pending_start = "new"
	get_tree().change_scene_to_file("res://scenes/main.tscn")
	await _frames(20)
	world = get_tree().current_scene
	player = world.player
	await _frames(40)
	var drift := _nearest(func(n): return n is Pickup and n.item_id == "wood" and n.is_available())
	await _stage(drift.global_position, 5.0)
	await _walk_to(drift.global_position, 1.0)
	_log("at driftwood %.1f m" % player.global_position.distance_to(drift.global_position))
	await _tap("interact")
	await _frames(40)
	_log("after driftwood")
	for i in 2:
		var bush := _nearest(func(n): return n is Pickup and n.item_id == "fiber" and n.is_available())
		if bush.global_position.distance_to(player.global_position) > 7.0:
			await _stage(bush.global_position, 4.0)
		await _walk_to(bush.global_position, 0.9)
		await _tap("interact")
		await _frames(30)

	_log("after bushes")
	# Crafting.
	# Top up what the hatchet needs so the video stays short.
	Game.inventory.add("fiber", 4)
	Game.inventory.add("stone", 2)
	if Game.inventory.count("wood") < 2:
		Game.inventory.add("wood", 2 - Game.inventory.count("wood"))
	await _tap("inventory")
	await _frames(35)
	_craft("rope")
	await _frames(30)
	_craft("hatchet")
	await _frames(45)
	await _tap("inventory")
	await _frames(10)

	# Chop a palm.
	_select("hatchet")
	var palm := _nearest(func(n): return n is ResourceNode and n.kind == "palm")
	if palm.global_position.distance_to(player.global_position) > 7.0:
		await _stage(palm.global_position, 4.0)
	await _walk_to(palm.global_position, 1.6)
	_face(palm.global_position)
	for i in 3:
		await _tap("use_tool")
		await _frames(32)

	_log("after chopping")
	# Fishing from the shore.
	Game.inventory.add("fishing_rod", 1)
	_select("fishing_rod")
	await _walk_to(Vector3(31.5, 0.0, 22.0), 0.6)
	_face(Vector3(40.0, 0.0, 22.0))
	await _frames(10)
	var rod := player.fishing
	Input.action_press("use_tool")
	await _frames(40)
	Input.action_release("use_tool")
	await _frames(70)
	if rod.state == FishingRod.S.WAIT:
		rod._bite()  # skip most of the wait for the video
	var t := 0
	while rod.state != FishingRod.S.BITE and t < 120:
		await _frames(1)
		t += 1
	await _frames(8)
	await _tap("use_tool")
	t = 0
	while rod.state == FishingRod.S.REEL and t < 600:
		if rod.tension < 0.6:
			Input.action_press("use_tool")
		else:
			Input.action_release("use_tool")
		await _frames(1)
		t += 1
	Input.action_release("use_tool")
	await _frames(50)

	_log("after fishing")
	# Swim out, dive and spear a fish.
	Game.inventory.add("spear", 1)
	_select("spear")
	var school := _nearest(func(n): return n is FishSchool and n.species == "tang" and not n.fish.is_empty()) as FishSchool
	if school:
		var sp := school.global_position
		player.teleport(Vector3(sp.x - 6.0, World.water_level(), sp.z), 90.0)
		await _frames(20)
		await _walk_to(sp, 2.5, 5.0)
	_log("at school (depth %.1f)" % World.depth_at(player.global_position.x, player.global_position.z))
	Input.action_press("dive")
	await _frames(70)
	_log("diving")
	for attempt in 6:
		var fish := _nearest_fish()
		if fish == null:
			break
		_face(fish.global_position)
		await _frames(4)
		await _tap("use_tool")
		await _frames(26)
		if int(Game.counters.get("spear_catch", 0)) > 0:
			break
	await _frames(30)
	Input.action_release("dive")
	await _frames(70)

	_log("after spearing")
	# Row the repaired rowboat.
	var boat := _nearest(func(n): return n is Boat and n.title == "rowboat") as Boat
	boat.needs_repair = false
	player.teleport(_dry_spot_near(boat.global_position), 0.0)
	_face(boat.global_position)
	await _frames(15)
	await _tap("interact")
	await _frames(10)
	_log("boarded? boat driver=%s" % [boat.driver != null])
	_press("move_forward", 1.0)
	await _frames(110)
	_press("move_left", 0.8)
	await _frames(45)
	_press("move_left", 0.0)
	await _frames(70)
	_press("move_forward", 0.0)
	await _frames(30)

	_log("after rowing")
	# Evening at camp: time-lapse into the night.
	await _tap("interact")
	await _frames(10)
	var fire := _nearest(func(n): return n is CookingStation)
	player.teleport(_dry_spot_near(fire.global_position, 2.2), 0.0)
	_face(fire.global_position)
	Game.time_hours = 16.5
	await _frames(20)
	for i in 180:
		Game.time_hours = lerpf(16.5, 22.5, i / 179.0)
		await _frames(1)
	await _frames(70)
	print("demo_video: done")
	get_tree().quit()


func _log(what: String) -> void:
	print("demo: %-28s pos=%s mode=%d wood=%d fiber=%d rope=%d hatchet=%d fish=%d spear_catch=%d obj=%s" % [
		what, player.global_position.snapped(Vector3.ONE * 0.1), player.mode, Game.inventory.count("wood"),
		Game.inventory.count("fiber"), Game.inventory.count("rope"), Game.inventory.count("hatchet"),
		Game.inventory.count("fish_snapper_raw") + Game.inventory.count("fish_tang_raw"),
		int(Game.counters.get("spear_catch", 0)), Game.current_objective().get("id", "")])


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

## Waits n rendered frames (30 per second of video under --fixed-fps 30).
func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _tap(action: String) -> void:
	_send(action, true)
	await _frames(2)
	_send(action, false)
	await _frames(1)


func _send(action: String, pressed: bool) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = pressed
	ev.strength = 1.0 if pressed else 0.0
	Input.parse_input_event(ev)


func _press(action: String, strength: float) -> void:
	if strength > 0.0:
		Input.action_press(action, strength)
	else:
		Input.action_release(action)


## Steers with the move actions (camera-relative, as a player would) until
## within `stop` metres of `goal`; gives up after `timeout` seconds.
func _walk_to(goal: Vector3, stop: float, timeout := 8.0) -> void:
	var yaw := deg_to_rad(world.camera.yaw_degrees)
	var right := Vector3(cos(yaw), 0.0, -sin(yaw))
	var back := Vector3(sin(yaw), 0.0, cos(yaw))
	var frames := int(timeout * 30.0)
	for i in frames:
		var d := goal - player.global_position
		d.y = 0.0
		if d.length() <= stop:
			break
		var dir := d.normalized()
		var x := dir.dot(right)
		var y := dir.dot(back)
		_press("move_right", maxf(x, 0.0))
		_press("move_left", maxf(-x, 0.0))
		_press("move_back", maxf(y, 0.0))
		_press("move_forward", maxf(-y, 0.0))
		await _frames(1)
	for a in ["move_right", "move_left", "move_back", "move_forward"]:
		Input.action_release(a)
	await _frames(6)


## Cuts to a dry spot `dist` metres from `p` (the short walk after it is real).
func _stage(p: Vector3, dist: float) -> void:
	var spot := _dry_spot_near(p, dist)
	var d := p - spot
	player.teleport(spot, rad_to_deg(atan2(d.x, d.z)))
	await _frames(12)


func _face(p: Vector3) -> void:
	var d := p - player.global_position
	player.face_direction(Vector3(d.x, 0.0, d.z).normalized())


func _craft(out: String) -> void:
	for r in ItemDB.RECIPES:
		if r["out"] == out:
			world.inventory_menu._craft(r)


func _select(id: String) -> void:
	for i in Game.inventory.size():
		var s = Game.inventory.get_slot(i)
		if s != null and s["id"] == id:
			if i >= Game.HOTBAR_SIZE:
				Game.inventory.swap(i, Game.HOTBAR_SIZE - 1)
				i = Game.HOTBAR_SIZE - 1
			Game.select(i)
			return


func _nearest(pred: Callable) -> Node3D:
	var best: Node3D = null
	var bd := INF
	for n in get_tree().current_scene.find_children("*", "", true, false):
		if n is Node3D and pred.call(n):
			var d := (n as Node3D).global_position.distance_to(player.global_position)
			if d < bd:
				bd = d
				best = n
	return best


func _nearest_fish() -> Fish:
	var best: Fish = null
	var bd := INF
	for f in get_tree().get_nodes_in_group("fish"):
		var fish := f as Fish
		var d := fish.global_position.distance_to(player.global_position)
		if fish.alive and d < bd:
			bd = d
			best = fish
	return best


func _dry_spot_near(p: Vector3, dist := 1.8) -> Vector3:
	var best := p
	var best_h := -INF
	for i in 16:
		var a := TAU * i / 16.0
		var q := p + Vector3(cos(a), 0.0, sin(a)) * dist
		var h := World.height_at(q.x, q.z)
		if h > best_h:
			best_h = h
			best = Vector3(q.x, h + 0.3, q.z)
	return best
