class_name SignalFire
extends Interactable
## The signal fire on Lookout Isle. Building it up and lighting it is the
## goal of the story: a passing ship sees the smoke.

signal lit

const COST := {"wood": 10, "palm_frond": 4}

var is_lit := false
var _fire: Node


func _ready() -> void:
	_fire = get_parent()
	super._ready()
	_apply()


func actions(_player: Node) -> Array:
	if is_lit:
		return [{"action": "", "text": "The signal fire is burning"}]
	if Game.inventory.has_items(COST):
		return [{"action": "interact", "text": "Light the signal fire (10 wood, 4 palm fronds)"}]
	return [{"action": "", "text": "Signal fire: bring 10 wood and 4 palm fronds"}]


func interact(player: Node) -> void:
	if is_lit or not Game.inventory.remove_items(COST):
		return
	player.play_action("cook")
	is_lit = true
	_apply()
	save_state({"lit": true})
	AudioManager.play("build", global_position)
	Game.record("signal_fire")
	Game.notify("The signal fire roars. Smoke rises high above Lookout Isle!", "")
	lit.emit()
	Game.rescued.emit()


func load_state(data: Dictionary) -> void:
	is_lit = bool(data.get("lit", false))


func _apply() -> void:
	if _fire and "is_lit" in _fire:
		_fire.is_lit = is_lit
		if is_lit and "light_energy" in _fire:
			_fire.light_energy = 4.0
