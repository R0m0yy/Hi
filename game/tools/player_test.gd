extends SceneTree
## Headless player-controller test with simulated input:
## idle -> walk -> run toward the sea -> swim -> dive -> resurface.
##   godot --headless --path game --script res://tools/player_test.gd

var _frame := 0
var _phase := 0
var _phase_start := 0
var _failures := 0
var _player  # PlayerController (untyped: this script compiles before the autoloads exist)
var _start := Vector3.ZERO
var _dive_start_y := 0.0
var _done := {}


const GROUND := 0
const SWIM := 1
const DIVE := 2


func _initialize() -> void:
	_begin.call_deferred()


func _begin() -> void:
	var game := root.get_node("Game")
	game.reset()
	game.pending_start = "new"
	change_scene_to_file("res://scenes/main.tscn")


func _process(_delta: float) -> bool:
	_frame = Engine.get_physics_frames()  # phases are timed in physics ticks (60 Hz)
	if _player == null:
		_player = get_first_node_in_group("player")
		return false
	var since := _frame - _phase_start
	match _phase:
		0:  # settle
			if since >= 45:
				_check(_player.is_on_floor(), "player lands on terrain (y=%.2f)" % _player.global_position.y)
				_check(_anim() == "idle", "idle animation at rest (%s)" % _anim())
				_start = _player.global_position
				Input.action_press("move_right")
				_next()
		1:  # walk
			if since >= 40:
				var moved: float = (_player.global_position - _start).length()
				_check(moved > 1.5, "walking moves the player (%.2f m)" % moved)
				_check(_anim() == "walk", "walk animation while walking (%s)" % _anim())
				Input.action_press("sprint")
				_next()
		2:  # run until swimming (or timeout)
			if since >= 25 and _once("run"):
				_check(_anim() == "run", "run animation while sprinting (%s)" % _anim())
			if _player.mode == SWIM or since > 900:
				_check(_player.mode == SWIM, "entered swimming at x=%.1f z=%.1f" % [_player.global_position.x, _player.global_position.z])
				Input.action_release("sprint")
				_next()
		3:  # swim out to deeper water, then dive
			if since >= 40 and _once("swim"):
				_check(_anim() == "swim", "swim animation in deep water (%s)" % _anim())
				var y: float = _player.global_position.y
				_check(absf(y - (-_player.float_depth)) < 0.35, "floats at chest depth (y=%.2f)" % y)
			if since > 40 and (_player.water_depth() > 3.5 or since > 1200):
				_dive_start_y = _player.global_position.y
				Input.action_press("dive")
				_next()
		4:  # dive
			if since >= 70:
				_check(_player.mode == DIVE, "dive mode while holding dive")
				_check(_player.global_position.y < _dive_start_y - 0.8, "dives down (y=%.2f)" % _player.global_position.y)
				_check(_anim() == "dive", "dive animation underwater (%s)" % _anim())
				Input.action_release("dive")
				Input.action_release("move_right")
				_next()
		5:  # resurface
			if since >= 90:
				_check(_player.mode == SWIM, "back to swimming after releasing dive")
				_check(absf(_player.global_position.y + _player.float_depth) < 0.35, "resurfaced (y=%.2f)" % _player.global_position.y)
				var rig := get_first_node_in_group("camera_rig") as Node3D
				var gap := Vector2(rig.global_position.x - _player.global_position.x, rig.global_position.z - _player.global_position.z).length()
				_check(gap < 2.0, "camera follows the player (%.2f m behind)" % gap)
				print("player_test: %s (%d failure(s))" % ["PASS" if _failures == 0 else "FAIL", _failures])
				quit(1 if _failures else 0)
	return false


func _once(key: String) -> bool:
	if _done.has(key):
		return false
	_done[key] = true
	return true


func _anim() -> String:
	var ap := _player.model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	return ap.current_animation


func _next() -> void:
	_phase += 1
	_phase_start = _frame


func _check(ok: bool, what: String) -> void:
	print("  [%s] %s" % ["ok" if ok else "FAIL", what])
	if not ok:
		_failures += 1
