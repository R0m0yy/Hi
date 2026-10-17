class_name ResourceNode
extends Interactable
## Palms and rocks: renewable sources that regrow over world time.
##   palm: shake (hands) for coconuts and fronds, chop (hatchet) for wood
##   rock: pick loose stones (hands), split (hatchet) for more stone

@export_enum("palm", "rock") var kind := "palm"
@export var visual_path: NodePath

const SPEC := {
	"palm": {
		"hand": {"item": "coconut", "max": 3, "regrow": 200.0, "verb": "Shake palm", "bonus": "palm_frond"},
		"tool": {"item": "wood", "max": 6, "regrow": 75.0, "verb": "Chop wood", "tool": "hatchet", "event": "chop"},
	},
	"rock": {
		"hand": {"item": "stone", "max": 2, "regrow": 150.0, "verb": "Pick loose stone"},
		"tool": {"item": "stone", "max": 6, "regrow": 80.0, "verb": "Split stone", "tool": "hatchet", "event": "split"},
	},
}

var _hand := 0.0
var _tool := 0.0
var _stamp := 0.0
var _visual: Node3D
var _cooldown := 0.0


func _ready() -> void:
	_visual = (get_node_or_null(visual_path) if not visual_path.is_empty() else get_parent()) as Node3D
	var spec: Dictionary = SPEC[kind]
	_hand = spec["hand"]["max"]
	_tool = spec["tool"]["max"]
	_stamp = Game.world_time
	super._ready()


func _regrow() -> void:
	var spec: Dictionary = SPEC[kind]
	var dt := maxf(Game.world_time - _stamp, 0.0)
	_stamp = Game.world_time
	_hand = minf(_hand + dt / spec["hand"]["regrow"], spec["hand"]["max"])
	_tool = minf(_tool + dt / spec["tool"]["regrow"], spec["tool"]["max"])


func actions(player: Node) -> Array:
	_regrow()
	var spec: Dictionary = SPEC[kind]
	var out := []
	if _hand >= 1.0:
		out.append({"action": "interact", "text": spec["hand"]["verb"]})
	var tool_spec: Dictionary = spec["tool"]
	if Game.selected_item() == tool_spec["tool"]:
		if _tool >= 1.0:
			out.append({"action": "use_tool", "text": tool_spec["verb"]})
		else:
			out.append({"action": "", "text": "Needs time to recover"})
	elif out.is_empty() and player != null:
		out.append({"action": "", "text": "%s needs a %s" % [tool_spec["verb"], ItemDB.display_name(tool_spec["tool"])]})
	return out


func interact(player: Node) -> void:
	_regrow()
	if _hand < 1.0:
		return
	var hand: Dictionary = SPEC[kind]["hand"]
	_hand -= 1.0
	if player and player.has_method("play_action"):
		player.play_action("gather")
	Game.give(hand["item"], 1)
	if hand.has("bonus") and Game.rng.randf() < 0.75:
		Game.give(hand["bonus"], 1)
	AudioManager.play("rustle" if kind == "palm" else "stone_pick", global_position)
	Interactable.wobble(_visual, 3.0 if kind == "palm" else 0.0)
	_save()


func accepts_tool(tool_id: String) -> bool:
	return tool_id == SPEC[kind]["tool"]["tool"]


func use_tool(player: Node, tool_id: String) -> bool:
	if not accepts_tool(tool_id):
		return false
	_regrow()
	if _tool < 1.0:
		Game.notify("It needs time to recover", "")
		return true
	var spec: Dictionary = SPEC[kind]["tool"]
	_tool -= 1.0
	if player and player.has_method("play_action"):
		player.play_action("chop")
	var amount := 1 + (1 if Game.rng.randf() < 0.35 else 0)
	Game.give(spec["item"], amount)
	Game.record(spec["event"])
	if player and player.has_method("wear_selected"):
		player.wear_selected(2.0)
	AudioManager.play("chop" if kind == "palm" else "rock_hit", global_position)
	Interactable.wobble(_visual, 5.0 if kind == "palm" else 0.0)
	_save()
	return true


func load_state(data: Dictionary) -> void:
	if data.is_empty():
		return
	_hand = float(data.get("hand", _hand))
	_tool = float(data.get("tool", _tool))
	_stamp = float(data.get("stamp", Game.world_time))


func _save() -> void:
	save_state({"hand": _hand, "tool": _tool, "stamp": _stamp})
