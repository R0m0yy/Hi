class_name GameWorld
extends Node3D
## The main scene's controller. Turns the islands into gameplay, spawns the
## fish, builds the HUD and menus, and runs the title -> play -> death ->
## respawn flow. Start straight into a new game with `-- --new-game`.

const START_POS := Vector3(25.5, 1.5, 22.5)
const START_YAW := 200.0

const ISLAND_PROFILES := {
	"HavenIsland": {
		"chest": {"fishing_rod": 1, "rope": 2, "coconut": 2},
		"loot": {
			"Barrel": {"rope": 2, "coconut": 1},
			"Crate": {"wood": 3, "shell": 1},
			"Barrel2": {"rope": 1, "fiber": 3},
			"WreckRibs": {"wood": 5, "rope": 1, "shell": 1},
		},
		"extras": [{"type": "spring", "name": "FreshSpring", "pos": [-6.3, -7.6], "reach": 2.4}],
		"fish_near": [Vector2(38.0, 21.0), Vector2(36.0, 31.0), Vector2(30.0, 35.0)],
	},
}

@onready var player: PlayerController = $Player
@onready var camera: IsometricCamera = $IsometricCamera

var hud: HUD
var inventory_menu: InventoryMenu
var storage_menu: StorageMenu
var pause_menu: PauseMenu
var main_menu: MainMenu
var death_screen: DeathScreen
var _title_yaw := 0.0


func _ready() -> void:
	var fish_root := Node3D.new()
	fish_root.name = "Fish"
	add_child(fish_root)
	var seed_value := 7
	for island in get_tree().get_nodes_in_group("island"):
		var profile: Dictionary = ISLAND_PROFILES.get(String(island.name), {})
		WorldPopulator.populate(island, profile)
		FishSpawner.spawn_for(island, fish_root, seed_value, profile.get("fish_near", []))
		seed_value += 11
	hud = HUD.new()
	add_child(hud)
	hud.bind_player(player)
	inventory_menu = InventoryMenu.new()
	add_child(inventory_menu)
	storage_menu = StorageMenu.new()
	add_child(storage_menu)
	Game.storage_requested.connect(_on_storage_requested)
	pause_menu = PauseMenu.new()
	add_child(pause_menu)
	death_screen = DeathScreen.new()
	add_child(death_screen)
	death_screen.respawn_requested.connect(_respawn)
	main_menu = MainMenu.new()
	add_child(main_menu)
	if "--new-game" in OS.get_cmdline_user_args() and Game.pending_start == "":
		Game.reset()
		Game.pending_start = "new"
	match Game.pending_start:
		"new":
			_start_new()
		"load":
			_start_loaded()
		_:
			_show_title()
	Game.pending_start = ""


func _on_storage_requested(box: Node) -> void:
	storage_menu.show_box(box)


func _show_title() -> void:
	Game.set_state("menu")
	hud.set_visible_hud(false)
	main_menu.open()
	AudioManager.set_loop("ocean", -8.0)
	AudioManager.set_loop("theme", -12.0, "Music")


func _start_new() -> void:
	Game.discovered["haven"] = true
	player.teleport(START_POS, START_YAW)
	_begin_play()
	Game.notify("You wash up on Haven Island. Find a way to survive.", "")


func _start_loaded() -> void:
	Structures.respawn_all()
	var p: Dictionary = Game.pending_player
	if p.has("pos"):
		var a: Array = p["pos"]
		player.teleport(Vector3(a[0], a[1], a[2]), rad_to_deg(float(p.get("yaw", 0.0))))
	else:
		player.teleport(Game.respawn_point)
	Game.pending_player = {}
	_begin_play()
	Game.notify("Welcome back. Day %d." % Game.day, "")


func _begin_play() -> void:
	Game.set_state("playing")
	Game.ui_open = false
	hud.set_visible_hud(true)
	camera.set_target(player)
	camera.yaw_degrees = 18.0
	camera.pitch_degrees = -40.0
	camera.zoom_size = 17.0
	camera.snap_to_target()
	Game.hotbar_changed.emit(Game.selected)
	AudioManager.set_loop("ocean", -6.0)
	AudioManager.set_loop("wind", -16.0)
	AudioManager.set_loop("theme", -14.0, "Music")


func _respawn() -> void:
	Game.respawn_stats()
	player.teleport(Game.respawn_point)
	Game.set_state("playing")
	Game.ui_open = false


func _process(delta: float) -> void:
	if Game.state == "menu":
		_title_yaw += delta * 3.0
		camera.set_view(Vector3(8.0, 0.0, 6.0), 64.0, 18.0 + _title_yaw, -34.0)
		return
	if Game.is_playing():
		_check_discovery()


func _unhandled_input(event: InputEvent) -> void:
	if not Game.is_playing():
		return
	if event.is_action_pressed("inventory") and not Game.ui_open:
		inventory_menu.open()
		get_viewport().set_input_as_handled()


func _check_discovery() -> void:
	for island in get_tree().get_nodes_in_group("island"):
		var id: String = island.get("island_id")
		if id == "" or Game.discovered.has(id):
			continue
		var r: float = island.get("discover_radius")
		var d := Vector2(player.global_position.x - island.global_position.x, player.global_position.z - island.global_position.z).length()
		if d < r:
			Game.discover(id, island.island_name)
