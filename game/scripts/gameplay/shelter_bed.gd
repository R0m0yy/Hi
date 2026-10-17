class_name ShelterBed
extends Interactable
## A lean-to: sleep until morning (or rest two hours by day), heal, set the
## respawn point and autosave.


func actions(_player: Node) -> Array:
	return [{"action": "interact", "text": "Sleep until morning" if Game.time_hours >= 18.0 or Game.time_hours < 5.0 else "Rest for two hours"}]


func interact(player: Node) -> void:
	if player == null:
		return
	player.start_busy(1.2, "Resting", "sit", func() -> void:
		var hours := 2.0
		if Game.time_hours >= 18.0:
			hours = 24.0 - Game.time_hours + 6.5
		elif Game.time_hours < 5.0:
			hours = 6.5 - Game.time_hours
		Game.advance_hours(hours)
		Game.stats["hunger"] = maxf(Game.stats["hunger"] - hours * 1.6, 5.0)
		Game.stats["thirst"] = maxf(Game.stats["thirst"] - hours * 2.0, 5.0)
		Game.stats["stamina"] = Game.max_stats["stamina"]
		Game.heal(10.0 + hours * 4.0)
		Game.respawn_point = global_position + global_basis.z * 1.8 + Vector3.UP * 0.5
		Game.record("sleep")
		Game.notify("You feel rested. Respawn point set.", "")
		SaveManager.save_game())
