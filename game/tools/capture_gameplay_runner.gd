extends Node
## See capture_gameplay.gd. Each shot sets up a situation through the same
## systems the player uses, waits for it to settle and saves a PNG.

var out_dir := "/tmp/pu_captures"
var only: Array = []
var player: PlayerController
var world: GameWorld


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--only="):
			only = Array(a.substr(7).split(","))
	DirAccess.make_dir_recursive_absolute(out_dir)
	_run.call_deferred()


func _wanted(name: String) -> bool:
	return only.is_empty() or name in only


func _run() -> void:
	if _wanted("title"):
		Game.pending_start = ""
		get_tree().change_scene_to_file("res://scenes/main.tscn")
		await _frames(90)
		await _shot("title")
	Game.reset()
	Game.pending_start = "new"
	get_tree().change_scene_to_file("res://scenes/main.tscn")
	await _frames(30)
	world = get_tree().current_scene
	player = world.player
	if _wanted("start"):
		await _frames(30)
		await _shot("start")
	if _wanted("gather"):
		var drift := _find(func(n): return n is Pickup and n.item_id == "wood" and n.amount == 3)
		await _approach(drift, 1.2)
		await _frames(20)
		await _shot("gather")
	# Give a mid-game kit so later shots show a lived-in pack.
	for id in ["wood", "stone", "fiber", "rope", "palm_frond", "shell"]:
		Game.inventory.add(id, 6)
	Game.inventory.add("hatchet", 1)
	Game.inventory.add("fishing_rod", 1)
	Game.inventory.add("spear", 1)
	Game.inventory.add("fish_snapper_raw", 2)
	Game.inventory.add("fish_tang_cooked", 1)
	Game.stats["hunger"] = 62.0
	Game.stats["thirst"] = 48.0
	Game.stats["stamina"] = 80.0
	Game.objective_index = 7
	Game.objective_changed.emit()
	if _wanted("inventory"):
		world.inventory_menu.open()
		await _frames(20)
		await _shot("inventory")
		world.inventory_menu.close()
	if _wanted("chop"):
		_select("hatchet")
		var palm := _find(func(n): return n is ResourceNode and n.kind == "palm")
		await _approach(palm, 1.3)
		player.play_action("chop")
		await _frames(12)
		await _shot("chop")
	if _wanted("fishing"):
		_select("fishing_rod")
		var shore := _shore_spot(Vector3(30.0, 0.0, 22.0), Vector3(1, 0, 0))
		player.teleport(shore, 90.0)
		await _frames(10)
		var rod := player.fishing
		rod.charge = 0.7
		rod._cast()
		await _frames(50)
		rod.species = "snapper"
		rod._bite()
		await _frames(3)
		rod._hook()
		rod.tension = 0.55
		rod.progress = 0.45
		await _frames(12)
		await _shot("fishing")
		rod._reset()
	if _wanted("dive"):
		_select("spear")
		var school := _school("tang")
		var fish: Fish = school.fish[0]
		player.teleport(Vector3(fish.global_position.x - 2.0, 0.0, fish.global_position.z), 90.0)
		await _frames(40)
		Input.action_press("dive")
		await _frames(120)
		await _shot("dive")
		Input.action_release("dive")
		await _frames(60)
	if _wanted("build"):
		Game.inventory.add("shelter_kit", 1)
		_select("shelter_kit")
		player.teleport(Vector3(4.0, 2.0, 12.0), 30.0)
		await _frames(20)
		player.builder.begin("shelter_kit")
		await _frames(20)
		await _shot("build")
		player.builder.end()
	if _wanted("camp"):
		Structures.spawn("shelter", 0, Vector3(6.0, World.height_at(6.0, 15.0), 15.0), 0.4)
		_select("hatchet")
		var fire := _find(func(n): return n is CookingStation)
		await _approach(fire, 1.6)
		await _frames(20)
		await _shot("camp")
	if _wanted("cook"):
		var fire2 := _find(func(n): return n is CookingStation)
		await _approach(fire2, 1.5)
		fire2.interact(player)
		await _frames(50)
		await _shot("cook")
		await _frames(100)
	if _wanted("storage"):
		var chest := _find(func(n): return n is StorageBox)
		await _approach(chest, 1.1)
		chest.interact(player)
		await _frames(20)
		await _shot("storage")
		world.storage_menu.close()
	if _wanted("boat"):
		var boat := _find(func(n): return n is Boat and n.title == "rowboat") as Boat
		boat.needs_repair = false
		await _approach(boat, 1.6)
		boat.interact(player)
		Input.action_press("move_forward")
		await _frames(150)
		await _shot("boat")
		Input.action_release("move_forward")
		await _frames(30)
	if _wanted("pause"):
		world.pause_menu.open()
		await _frames(10)
		await _shot("pause")
		world.pause_menu.close()
	print("capture_gameplay: done -> ", out_dir)
	get_tree().quit()


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out_dir.path_join(name + ".png"))
	print("  saved ", name)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _find(pred: Callable) -> Node:
	var best: Node = null
	var bd := INF
	for n in get_tree().current_scene.find_children("*", "", true, false):
		if pred.call(n):
			var d: float = (n as Node3D).global_position.distance_to(player.global_position) if player else 0.0
			if d < bd:
				bd = d
				best = n
	return best


func _school(species: String) -> FishSchool:
	for n in get_tree().current_scene.find_children("*", "FishSchool", true, false):
		if n.species == species and not n.fish.is_empty():
			return n
	return null


func _select(id: String) -> void:
	for i in Game.inventory.size():
		var s = Game.inventory.get_slot(i)
		if s != null and s["id"] == id:
			if i >= Game.HOTBAR_SIZE:
				Game.inventory.swap(i, Game.HOTBAR_SIZE - 1)
				i = Game.HOTBAR_SIZE - 1
			Game.select(i)
			return


func _approach(target: Node3D, dist: float) -> void:
	var tp := target.global_position
	var best := tp
	var best_score := -INF
	for i in 16:
		var a := TAU * i / 16.0
		var p := tp + Vector3(cos(a), 0, sin(a)) * dist
		var h := World.height_at(p.x, p.z)
		# Prefer dry spots on the camera side so the action is visible.
		var score := h * 2.0 + (p.z - tp.z) * 0.5
		if score > best_score:
			best_score = score
			best = Vector3(p.x, maxf(h, -0.4) + 0.3, p.z)
	var d := tp - best
	player.teleport(best, rad_to_deg(atan2(d.x, d.z)))
	await _frames(12)


func _shore_spot(from: Vector3, dir: Vector3) -> Vector3:
	var p := from
	for i in 60:
		var nxt := p + dir * 0.5
		if World.height_at(nxt.x, nxt.z) < World.water_level() + 0.25:
			break
		p = nxt
	p.y = World.height_at(p.x, p.z) + 0.3
	return p
