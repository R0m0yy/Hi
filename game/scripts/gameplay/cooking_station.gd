class_name CookingStation
extends Interactable
## A campfire: cooks raw fish into meals, one at a time.

const COOK_SECONDS := 2.2


func actions(_player: Node) -> Array:
	var raw := _first_raw()
	if raw.is_empty():
		return [{"action": "", "text": "Campfire: bring raw fish to cook"}]
	return [{"action": "interact", "text": "Cook %s (%d)" % [ItemDB.display_name(raw), Game.inventory.count(raw)]}]


func interact(player: Node) -> void:
	var raw := _first_raw()
	if raw.is_empty() or player == null:
		return
	AudioManager.play("sizzle", global_position)
	player.start_busy(COOK_SECONDS, "Cooking " + ItemDB.display_name(raw), "cook", func() -> void:
		if Game.inventory.remove(raw, 1):
			Game.give(ItemDB.item(raw)["cooks_to"], 1)
			Game.record("cook"))


func _first_raw() -> String:
	for s in Game.inventory.slots:
		if s != null and ItemDB.item(s["id"]).has("cooks_to"):
			return s["id"]
	return ""
