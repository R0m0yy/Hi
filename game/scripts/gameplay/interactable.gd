class_name Interactable
extends Node3D
## Something the player can use. The player picks the closest available one
## in reach (group "interactable") and the HUD shows its actions, e.g.
##   [{"action": "interact", "text": "Shake palm"},
##    {"action": "use_tool", "text": "Chop", "tool": "hatchet"}]
## State that must survive saving lives in Game.world[save_id].

## Horizontal reach in metres, measured from focus_position().
@export var reach := 1.9
## Stable id for saving. Defaults to the node path.
@export var save_id := ""
## Tie-breaker when several things are in reach: higher wins (scatter
## plants and pebbles sit below props and boats).
@export var priority := 0.0


func _ready() -> void:
	add_to_group("interactable")
	if save_id.is_empty():
		save_id = String(get_path()).replace("/root/", "")
	load_state(Game.get_world(save_id))


## Prompt actions available to `player` right now; empty means not usable.
func actions(_player: Node) -> Array:
	return []


func interact(_player: Node) -> void:
	pass


## Return true when this object consumed a tool use (chop, split...).
func use_tool(_player: Node, _tool_id: String) -> bool:
	return false


func accepts_tool(_tool_id: String) -> bool:
	return false


func focus_position() -> Vector3:
	return global_position


func load_state(_data: Dictionary) -> void:
	pass


func save_state(data: Dictionary) -> void:
	Game.set_world(save_id, data)


## Small "hit" wobble on a visual node (palms, rocks, bushes).
static func wobble(node: Node3D, strength: float = 4.0) -> void:
	if node == null or not node.is_inside_tree():
		return
	var base := node.rotation
	var tw := node.create_tween()
	tw.tween_property(node, "rotation:z", base.z + deg_to_rad(strength), 0.06)
	tw.tween_property(node, "rotation:z", base.z - deg_to_rad(strength * 0.6), 0.1)
	tw.tween_property(node, "rotation:z", base.z, 0.12)
