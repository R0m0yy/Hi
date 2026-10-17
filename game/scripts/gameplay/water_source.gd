class_name WaterSource
extends Interactable
## A fresh-water spring (Haven's cave): drink as much as you like.

@export var title := "fresh spring"


func actions(_player: Node) -> Array:
	return [{"action": "interact", "text": "Drink from the " + title}]


func interact(player: Node) -> void:
	if player and player.has_method("play_action"):
		player.play_action("gather")
	Game.stats["thirst"] = minf(Game.stats["thirst"] + 40.0, Game.max_stats["thirst"])
	Game.stats_changed.emit()
	Game.record("drink")
	Game.notify("Cool, fresh water", "")
	AudioManager.play("drink", global_position)
