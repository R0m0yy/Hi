extends Node
## Saves and loads the game (autoload "SaveManager") as JSON in user://,
## plus player settings in user://settings.cfg.
## A save holds the survival state, inventory, time, objectives, every world
## object's state (resources, pickups, chests, boats), placed structures and
## the player's position. Loading reloads the main scene and restores it.

const SAVE_PATH := "user://savegame.json"
const SETTINGS_PATH := "user://settings.cfg"
const VERSION := 1

var settings := {"music": 0.7, "sfx": 0.85, "ambience": 0.8, "fullscreen": false, "objectives": true,
		"ui_scale": 1.0, "toggle_dive": false}
var last_error := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	load_settings()
	apply_settings.call_deferred()


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)


func save_game() -> bool:
	if not Game.is_playing() and Game.state != "dead":
		return false
	var player := get_tree().get_first_node_in_group("player") as PlayerController
	for b in get_tree().get_nodes_in_group("boats"):
		b.capture_state()
	var pdata := {}
	if player:
		var pos := player.global_position
		if player.boat:
			var land := World.find_land_near(player.boat.global_position, 8.0)
			pos = land if not is_nan(land.y) else Game.respawn_point
		pdata = {"pos": [pos.x, pos.y + 0.2, pos.z], "yaw": player.model.rotation.y}
	var data := {
		"version": VERSION,
		"saved_at": Time.get_datetime_string_from_system(),
		"player": pdata,
		"stats": Game.stats,
		"inventory": Game.inventory.to_data(),
		"selected": Game.selected,
		"world_time": Game.world_time,
		"time_hours": Game.time_hours,
		"day": Game.day,
		"respawn": [Game.respawn_point.x, Game.respawn_point.y, Game.respawn_point.z],
		"objective_index": Game.objective_index,
		"objective_progress": Game.objective_progress,
		"counters": Game.counters,
		"world": Game.world,
		"structures": Game.structures,
		"discovered": Game.discovered,
	}
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		last_error = error_string(FileAccess.get_open_error())
		return false
	f.store_string(JSON.stringify(data, "\t"))
	f.close()
	Game.notify("Game saved", "")
	return true


## Reads the save into Game. Returns false if there is none or it is broken.
func read_save() -> bool:
	if not has_save():
		return false
	var data = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	if not (data is Dictionary) or int(data.get("version", 0)) != VERSION:
		last_error = "unreadable save"
		return false
	Game.reset()
	for k in data.get("stats", {}):
		if Game.stats.has(k):
			Game.stats[k] = float(data["stats"][k])
	Game.inventory.from_data(data.get("inventory", []))
	Game.selected = int(data.get("selected", 0))
	Game.world_time = float(data.get("world_time", 0.0))
	Game.time_hours = float(data.get("time_hours", 8.0))
	Game.day = int(data.get("day", 1))
	var r: Array = data.get("respawn", [25.5, 1.5, 22.5])
	Game.respawn_point = Vector3(r[0], r[1], r[2])
	Game.objective_index = int(data.get("objective_index", 0))
	Game.objective_progress = int(data.get("objective_progress", 0))
	Game.counters = data.get("counters", {})
	Game.world = data.get("world", {})
	Game.structures = data.get("structures", [])
	Game.discovered = data.get("discovered", {})
	Game.pending_player = data.get("player", {})
	return true


func load_and_restart() -> void:
	if read_save():
		Game.pending_start = "load"
		get_tree().paused = false
		get_tree().reload_current_scene()
	else:
		Game.notify("Could not load the save (%s)" % last_error, "")


func _unhandled_input(event: InputEvent) -> void:
	if not Game.is_playing() or Game.ui_open:
		return
	if event.is_action_pressed("quick_save"):
		save_game()
	elif event.is_action_pressed("quick_load"):
		load_and_restart()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS_PATH) != OK:
		return
	for k in settings:
		settings[k] = cfg.get_value("settings", k, settings[k])


func save_settings() -> void:
	var cfg := ConfigFile.new()
	for k in settings:
		cfg.set_value("settings", k, settings[k])
	cfg.save(SETTINGS_PATH)


func apply_settings() -> void:
	AudioManager.set_bus_volume("Music", settings["music"])
	AudioManager.set_bus_volume("SFX", settings["sfx"])
	AudioManager.set_bus_volume("Ambience", settings["ambience"])
	if DisplayServer.get_name() != "headless":
		var want := DisplayServer.WINDOW_MODE_FULLSCREEN if settings["fullscreen"] else DisplayServer.WINDOW_MODE_WINDOWED
		if DisplayServer.window_get_mode() != want and (settings["fullscreen"] or DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN):
			DisplayServer.window_set_mode(want)
	for hud in get_tree().get_nodes_in_group("hud"):
		hud.set_objectives_visible(settings["objectives"])
	get_tree().root.content_scale_factor = clampf(float(settings["ui_scale"]), 0.75, 1.5)
