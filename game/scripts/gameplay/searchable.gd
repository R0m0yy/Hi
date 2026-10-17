class_name Searchable
extends Interactable
## Wreckage, barrels and crates: search once for supplies.

@export var title := "barrel"
@export var loot := {}

var _searched := false


func actions(_player: Node) -> Array:
	if _searched:
		return []
	return [{"action": "interact", "text": "Search " + title}]


func interact(player: Node) -> void:
	if _searched:
		return
	_searched = true
	if player and player.has_method("play_action"):
		player.play_action("gather")
	AudioManager.play("rummage", global_position)
	for id in loot:
		Game.give(id, int(loot[id]))
	save_state({"searched": true})


func load_state(data: Dictionary) -> void:
	_searched = bool(data.get("searched", false))
