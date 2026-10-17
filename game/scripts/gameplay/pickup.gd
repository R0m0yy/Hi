class_name Pickup
extends Interactable
## A thing lying around that goes into the pack (driftwood, stones, shells,
## coconuts, fibre plants). Hides its visual when taken and comes back
## after `respawn_seconds` of world time (0 = never).

@export var item_id := "wood"
@export var amount := 1
@export var verb := "Pick up"
@export var respawn_seconds := 300.0
@export var visual_path: NodePath
@export var sound := "pickup"
@export var animation := "gather"

## Optional: a ScatterField instance this pickup stands for.
var scatter: ScatterField
var scatter_index := -1

var _available_at := 0.0
var _visual: Node3D


func _ready() -> void:
	_visual = get_node_or_null(visual_path) as Node3D
	super._ready()
	_apply_visibility()
	if respawn_seconds > 0.0:
		var t := Timer.new()
		t.wait_time = 2.0
		t.autostart = true
		t.timeout.connect(_apply_visibility)
		add_child(t)


func is_available() -> bool:
	return Game.world_time >= _available_at


func actions(_player: Node) -> Array:
	if not is_available():
		return []
	var label := "%s %s" % [verb, ItemDB.display_name(item_id)]
	if amount > 1:
		label += " ×%d" % amount
	return [{"action": "interact", "text": label}]


func interact(player: Node) -> void:
	if not is_available():
		return
	if player and player.has_method("play_action"):
		player.play_action(animation)
	Game.give(item_id, amount)
	AudioManager.play(sound, global_position)
	_available_at = INF if respawn_seconds <= 0.0 else Game.world_time + respawn_seconds
	save_state({"at": _available_at if respawn_seconds > 0.0 else -1.0})
	_apply_visibility()


func load_state(data: Dictionary) -> void:
	if data.has("at"):
		var at := float(data["at"])
		_available_at = INF if at < 0.0 else at


func _apply_visibility() -> void:
	var show := is_available()
	if _visual:
		_visual.visible = show
	if scatter and scatter_index >= 0:
		scatter.set_instance_visible(scatter_index, show)
