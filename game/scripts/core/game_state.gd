extends Node
## Global game state (autoload "Game"): survival stats, the player's
## inventory and hotbar, world time, objectives, and the per-object world
## state that SaveManager persists. Gameplay nodes read and write here;
## UI listens to the signals.

signal stats_changed
signal hotbar_changed(index: int)
signal notified(text: String, item_id: String)
signal objective_changed
signal player_died
signal state_changed(state: String)
signal hour_changed(hour: int)
signal storage_requested(box: Node)
signal rescued

const HOTBAR_SIZE := 6
const INVENTORY_SIZE := 24
const STAT_NAMES := ["health", "hunger", "thirst", "stamina", "oxygen"]
## Real seconds per in-game hour.
const SECONDS_PER_HOUR := 60.0

## Needs, per real second.
const HUNGER_RATE := 100.0 / 840.0
const THIRST_RATE := 100.0 / 600.0
const OXYGEN_DRAIN := 100.0 / 35.0
const OXYGEN_RECOVER := 40.0
const STAMINA_RECOVER := 22.0
const STAMINA_DELAY := 0.8

const OBJECTIVES := [
	{"id": "wood", "text": "Collect wood from driftwood on the beach", "event": "collect:wood", "count": 4},
	{"id": "fiber", "text": "Gather plant fibre from bushes or beach grass", "event": "collect:fiber", "count": 3},
	{"id": "rope", "text": "Open the crafting menu and twist some rope", "event": "craft:rope", "count": 1},
	{"id": "stone", "text": "Pick up stones near the camp", "event": "collect:stone", "count": 2},
	{"id": "hatchet", "text": "Craft a stone hatchet", "event": "craft:hatchet", "count": 1},
	{"id": "chop", "text": "Chop wood from a palm with the hatchet", "event": "chop", "count": 3},
	{"id": "rod", "text": "Take the fishing rod from the camp chest", "event": "collect:fishing_rod", "count": 1},
	{"id": "catch", "text": "Catch a fish with the rod", "event": "catch", "count": 1},
	{"id": "cook", "text": "Cook your fish at the campfire", "event": "cook", "count": 1},
	{"id": "eat", "text": "Eat a cooked meal", "event": "eat_cooked", "count": 1},
	{"id": "spear", "text": "Craft a spear and spear a fish underwater", "event": "spear_catch", "count": 1},
	{"id": "shelter", "text": "Build a lean-to shelter", "event": "place:shelter", "count": 1},
	{"id": "boat", "text": "Repair the rowboat on the east shore", "event": "repair:rowboat", "count": 1},
	{"id": "palm_key", "text": "Row north-east to Palm Key", "event": "discover:palm_key", "count": 1},
	{"id": "lookout", "text": "Find Lookout Isle to the south-west", "event": "discover:lookout", "count": 1},
	{"id": "signal", "text": "Light the signal fire on Lookout Isle's plateau", "event": "signal_fire", "count": 1},
]

## Where discovery objectives point the HUD compass: event -> island node name.
const OBJECTIVE_TARGETS := {
	"discover:palm_key": "PalmKey",
	"discover:lookout": "LookoutIsle",
	"signal_fire": "LookoutIsle",
}

var state := "menu"
var inventory := Inventory.new(INVENTORY_SIZE)
var selected := 0
var stats := {}
var max_stats := {"health": 100.0, "hunger": 100.0, "thirst": 100.0, "stamina": 100.0, "oxygen": 100.0}
## Seconds since the save was started; drives respawn timers.
var world_time := 0.0
var time_hours := 7.5
var day := 1
var respawn_point := Vector3(25.5, 1.5, 22.5)
var objective_index := 0
var objective_progress := 0
var counters := {}
## save_id -> Dictionary, owned by the matching world object.
var world := {}
## Player-placed structures: [{type, pos, rot, data}]
var structures: Array = []
var discovered := {}
var rng := RandomNumberGenerator.new()
## True while a menu that takes input is open.
var ui_open := false
## Set before reloading the main scene: "new", "load" or "" (title screen).
var pending_start := ""
## Player placement restored after loading: {"pos": [x,y,z], "yaw": rad}.
var pending_player := {}

var _stamina_wait := 0.0
var _last_hour := -1


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	reset()


func reset() -> void:
	inventory.clear()
	selected = 0
	for s in STAT_NAMES:
		stats[s] = max_stats[s]
	world_time = 0.0
	time_hours = 7.5
	day = 1
	respawn_point = Vector3(25.5, 1.5, 22.5)
	objective_index = 0
	objective_progress = 0
	counters = {}
	world = {}
	structures = []
	discovered = {}
	rng.seed = 20261017
	inventory.add("coconut", 1)
	stats_changed.emit()
	objective_changed.emit()
	hotbar_changed.emit(selected)


func set_state(s: String) -> void:
	state = s
	state_changed.emit(s)


func is_playing() -> bool:
	return state == "playing"


func _process(delta: float) -> void:
	if state != "playing":
		return
	world_time += delta
	time_hours += delta / SECONDS_PER_HOUR
	if time_hours >= 24.0:
		time_hours -= 24.0
		day += 1
	var h := int(time_hours)
	if h != _last_hour:
		_last_hour = h
		hour_changed.emit(h)


# ---------------------------------------------------------------------------
# Survival stats
# ---------------------------------------------------------------------------

## Called by the player every physics frame with what it is doing.
## exertion: stamina cost per second (0 when resting); underwater: breath held.
func tick_needs(delta: float, exertion: float, underwater: bool) -> void:
	if state != "playing":
		return
	_add("hunger", -HUNGER_RATE * delta * (1.0 + exertion * 0.02))
	_add("thirst", -THIRST_RATE * delta * (1.0 + exertion * 0.02))
	if exertion > 0.0:
		_add("stamina", -exertion * delta)
		_stamina_wait = STAMINA_DELAY
	else:
		_stamina_wait -= delta
		if _stamina_wait <= 0.0:
			var rate := STAMINA_RECOVER * (0.5 if stats["hunger"] < 15.0 else 1.0)
			_add("stamina", rate * delta)
	if underwater:
		_add("oxygen", -OXYGEN_DRAIN * delta)
	else:
		_add("oxygen", OXYGEN_RECOVER * delta)
	var hurt := 0.0
	if stats["oxygen"] <= 0.0:
		hurt += 9.0
	if stats["hunger"] <= 0.0:
		hurt += 0.7
	if stats["thirst"] <= 0.0:
		hurt += 0.9
	if hurt > 0.0:
		damage(hurt * delta)
	elif stats["hunger"] > 40.0 and stats["thirst"] > 40.0:
		_add("health", 0.6 * delta)
	stats_changed.emit()


func damage(amount: float) -> void:
	if stats["health"] <= 0.0:
		return
	_add("health", -amount)
	stats_changed.emit()
	if stats["health"] <= 0.0:
		set_state("dead")
		player_died.emit()


func heal(amount: float) -> void:
	_add("health", amount)
	stats_changed.emit()


func _add(stat: String, amount: float) -> void:
	stats[stat] = clampf(stats[stat] + amount, 0.0, max_stats[stat])


func stat_ratio(stat: String) -> float:
	return stats[stat] / max_stats[stat]


## Eats or drinks one item from `slot`. Returns false if it is not food.
func consume_slot(slot: int) -> bool:
	var s = inventory.get_slot(slot)
	if s == null or ItemDB.kind(s["id"]) != "food":
		return false
	var def := ItemDB.item(s["id"])
	_add("hunger", def.get("food", 0.0))
	_add("thirst", def.get("water", 0.0))
	var h: float = def.get("health", 0.0)
	if h < 0.0:
		damage(-h)
		notify("Raw fish doesn't sit well. Cook it next time.", s["id"])
	elif h > 0.0:
		heal(h)
	if String(s["id"]).ends_with("_cooked"):
		record("eat_cooked")
	record("eat")
	inventory.take_from_slot(slot, 1)
	stats_changed.emit()
	return true


func respawn_stats() -> void:
	stats["health"] = 60.0
	stats["hunger"] = maxf(stats["hunger"], 45.0)
	stats["thirst"] = maxf(stats["thirst"], 45.0)
	stats["stamina"] = max_stats["stamina"]
	stats["oxygen"] = max_stats["oxygen"]
	stats_changed.emit()


# ---------------------------------------------------------------------------
# Inventory helpers
# ---------------------------------------------------------------------------

## Adds to the inventory, announces it, and counts it for objectives.
func give(id: String, count: int = 1, quiet := false) -> int:
	var left := inventory.add(id, count)
	var got := count - left
	if got > 0:
		if not quiet:
			notify("+%d %s" % [got, ItemDB.display_name(id)], id)
		record("collect:" + id, got)
	if left > 0:
		notify("Your pack is full", "")
	return left


func selected_item() -> String:
	var s = inventory.get_slot(selected)
	return s["id"] if s != null else ""


func select(index: int) -> void:
	selected = wrapi(index, 0, HOTBAR_SIZE)
	hotbar_changed.emit(selected)


func notify(text: String, item_id: String = "") -> void:
	notified.emit(text, item_id)


func open_storage(box: Node) -> void:
	storage_requested.emit(box)


# ---------------------------------------------------------------------------
# Objectives
# ---------------------------------------------------------------------------

func record(event: String, amount: int = 1) -> void:
	counters[event] = int(counters.get(event, 0)) + amount
	if objective_index >= OBJECTIVES.size():
		return
	var obj: Dictionary = OBJECTIVES[objective_index]
	if obj["event"] != event:
		return
	objective_progress += amount
	if objective_progress >= int(obj["count"]):
		notify("Objective complete: " + obj["text"], "")
		_advance_objective()
	objective_changed.emit()


func _advance_objective() -> void:
	objective_index += 1
	objective_progress = 0
	# Skip goals that are already satisfied (e.g. collected earlier).
	while objective_index < OBJECTIVES.size():
		var obj: Dictionary = OBJECTIVES[objective_index]
		var done := int(counters.get(obj["event"], 0))
		var ev: String = obj["event"]
		if ev.begins_with("collect:"):
			done = inventory.count(ev.substr(8))
		if done < int(obj["count"]) or ev in ["catch", "cook", "eat_cooked", "spear_catch", "chop"]:
			break
		objective_index += 1


func current_objective() -> Dictionary:
	if objective_index >= OBJECTIVES.size():
		return {}
	return OBJECTIVES[objective_index]


func discover(island_id: String, island_name: String) -> void:
	if discovered.has(island_id):
		return
	discovered[island_id] = true
	notify("Discovered " + island_name, "")
	record("discover:" + island_id)


# ---------------------------------------------------------------------------
# Time of day
# ---------------------------------------------------------------------------

func clock_text() -> String:
	var h := int(time_hours)
	var m := int((time_hours - h) * 60.0)
	return "Day %d  %02d:%02d" % [day, h, m]


func is_night() -> bool:
	return time_hours >= 20.0 or time_hours < 5.5


func advance_hours(hours: float) -> void:
	time_hours += hours
	while time_hours >= 24.0:
		time_hours -= 24.0
		day += 1
	world_time += hours * SECONDS_PER_HOUR


# ---------------------------------------------------------------------------
# World object state
# ---------------------------------------------------------------------------

func get_world(save_id: String) -> Dictionary:
	return world.get(save_id, {})


func set_world(save_id: String, data: Dictionary) -> void:
	world[save_id] = data
