class_name FishingRod
extends Node
## Rod fishing: hold use to charge the cast, release to throw the bobber,
## wait for a bite, press use within the window to hook, then hold to reel
## while keeping the line tension below breaking point.

signal state_changed(state: int)
signal reel_changed(tension: float, progress: float)

enum S { IDLE, CHARGE, CAST, WAIT, BITE, REEL }

const MIN_CAST := 3.0
const MAX_CAST := 14.0
const CAST_TIME := 0.75
const BITE_WINDOW := 1.1

var state := S.IDLE
var charge := 0.0
var species := ""
var tension := 0.0
var progress := 0.0
var _t := 0.0
var _wait := 0.0
var _from := Vector3.ZERO
var _target := Vector3.ZERO
var _pull := 0.0
var _pull_phase := 0.0
var _misses := 0
var _bobber: MeshInstance3D
var _line: MeshInstance3D
var _line_mesh: ImmediateMesh
var _rng := RandomNumberGenerator.new()

@onready var player: PlayerController = get_parent()


func _ready() -> void:
	_rng.randomize()
	_bobber = MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.09
	sphere.height = 0.18
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("e8453c")
	mat.roughness = 0.4
	sphere.material = mat
	_bobber.mesh = sphere
	var cap := MeshInstance3D.new()
	var cap_mesh := SphereMesh.new()
	cap_mesh.radius = 0.092
	cap_mesh.height = 0.1
	cap_mesh.is_hemisphere = true
	var white := StandardMaterial3D.new()
	white.albedo_color = Color("fff8e3")
	cap_mesh.material = white
	cap.mesh = cap_mesh
	cap.position.y = 0.0
	_bobber.add_child(cap)
	_bobber.top_level = true
	_bobber.visible = false
	add_child(_bobber)
	_line_mesh = ImmediateMesh.new()
	_line = MeshInstance3D.new()
	_line.mesh = _line_mesh
	_line.top_level = true
	_line.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var lm := StandardMaterial3D.new()
	lm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	lm.albedo_color = Color(1, 1, 1, 0.85)
	lm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_line.material_override = lm
	add_child(_line)


func busy() -> bool:
	return state != S.IDLE


func blocks_movement() -> bool:
	return state in [S.CHARGE, S.CAST, S.BITE, S.REEL]


func locks_facing() -> bool:
	return state != S.IDLE


func animation() -> String:
	match state:
		S.CHARGE:
			return "fish_idle"
		S.REEL:
			return "fish_reel"
	return "fish_idle"


func _physics_process(delta: float) -> void:
	var equipped := Game.selected_item() == "fishing_rod"
	var can_fish := player.mode == PlayerController.Mode.GROUND or player.mode == PlayerController.Mode.BOAT
	if state != S.IDLE and (not equipped or not can_fish or not Game.is_playing()):
		_reset()
		return
	if not equipped:
		return
	var active := Game.is_playing() and not Game.ui_open and not player.is_busy()
	var pressed := active and Input.is_action_just_pressed("use_tool")
	var held := active and Input.is_action_pressed("use_tool")
	if active and state != S.IDLE and Input.is_action_just_pressed("cancel"):
		_reel_in("")
		return
	match state:
		S.IDLE:
			if pressed and can_fish:
				state = S.CHARGE
				charge = 0.0
				state_changed.emit(state)
		S.CHARGE:
			charge = minf(charge + delta / 1.1, 1.0)
			if not held:
				_cast()
		S.CAST:
			_t += delta / CAST_TIME
			var p := _from.lerp(_target, _t)
			p.y += sin(_t * PI) * (1.5 + charge * 2.0)
			_bobber.global_position = p
			if _t >= 1.0:
				_land()
		S.WAIT:
			_wait -= delta
			var bob := sin(Time.get_ticks_msec() * 0.004) * 0.025
			if _wait < 1.2 and _rng.randf() < delta * 2.5:
				bob -= 0.06  # a nibble
				AudioManager.play("nibble", _target, -14.0)
			_bobber.global_position = Vector3(_target.x, World.surface_at(_target) + bob, _target.z)
			if pressed:
				_reel_in("Too early. Wait for the bobber to dip.")
			elif _wait <= 0.0:
				_bite()
		S.BITE:
			_wait -= delta
			_bobber.global_position = Vector3(_target.x, World.surface_at(_target) - 0.14, _target.z)
			if pressed:
				_hook()
			elif _wait <= 0.0:
				_misses += 1
				if _misses >= 2:
					_reel_in("The fish lost interest.")
				else:
					Game.notify("Missed it! Wait for another bite.", "")
					state = S.WAIT
					_wait = _rng.randf_range(3.0, 6.0)
					state_changed.emit(state)
		S.REEL:
			_reel(delta, held)
	_draw_line()


func _cast() -> void:
	var fwd := player.model.global_basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var dist := lerpf(MIN_CAST, MAX_CAST, charge)
	_from = player.held.tip_position() if player.held else player.global_position + Vector3.UP * 1.5
	_target = player.global_position + fwd * dist
	_target.y = World.water_level()
	_t = 0.0
	_misses = 0
	state = S.CAST
	_bobber.visible = true
	_bobber.global_position = _from
	player.play_action("fish_cast", 0.6)
	AudioManager.play("cast", player.global_position)
	state_changed.emit(state)


func _land() -> void:
	var depth := World.depth_at(_target.x, _target.z)
	if depth < 0.4:
		_bobber.global_position = Vector3(_target.x, World.height_at(_target.x, _target.z) + 0.05, _target.z)
		_reel_in("The bobber landed on dry ground. Cast into the water.")
		return
	AudioManager.play("plop", _target)
	state = S.WAIT
	# Deeper water and dawn/dusk bite a little sooner.
	var hour := Game.time_hours
	var good_hour := (hour > 5.5 and hour < 8.5) or (hour > 17.0 and hour < 19.5)
	_wait = _rng.randf_range(2.5, 7.0) * (0.75 if good_hour else 1.0) * (0.85 if depth > 4.0 else 1.0)
	species = ItemDB.roll_fish(depth, _rng)
	state_changed.emit(state)


func _bite() -> void:
	state = S.BITE
	_wait = BITE_WINDOW
	AudioManager.play("bite", _target)
	state_changed.emit(state)


func _hook() -> void:
	state = S.REEL
	tension = 0.2
	progress = 0.15
	_pull_phase = 0.0
	AudioManager.play("hook", _target)
	state_changed.emit(state)


func _reel(delta: float, held: bool) -> void:
	var fish: Dictionary = ItemDB.FISH[species]
	var strength: float = fish["strength"]
	_pull_phase += delta * (1.4 + strength * 2.2)
	# The fish fights in surges: pull goes 0..1.
	_pull = clampf(0.5 + 0.5 * sin(_pull_phase) + (0.35 if sin(_pull_phase * 0.37) > 0.8 else 0.0), 0.0, 1.0) * strength
	if held:
		progress += (0.24 - _pull * 0.16) * delta
		tension += (0.22 + _pull * 0.85) * delta
	else:
		progress -= _pull * 0.06 * delta
		tension -= 0.6 * delta
	tension = clampf(tension, 0.0, 1.2)
	reel_changed.emit(tension, progress)
	var tip := player.held.tip_position() if player.held else player.global_position
	var p := _target.lerp(Vector3(tip.x, _target.y, tip.z), clampf(progress, 0.0, 1.0) * 0.85)
	p.y = World.surface_at(p) - 0.05 + sin(Time.get_ticks_msec() * 0.03) * 0.03 * _pull
	_bobber.global_position = p
	if tension >= 1.0:
		player.wear_selected(8.0)
		AudioManager.play("line_snap", player.global_position)
		_reel_in("The line snapped! Ease off when the tension climbs.")
	elif progress >= 1.0:
		var item: String = fish["item"]
		Game.give(item, 1, true)
		Game.notify("Caught a %s!" % fish["name"], item)
		Game.record("catch")
		Game.record("catch:" + species)
		player.wear_selected(3.0)
		AudioManager.play("catch", player.global_position)
		_reset()
		player.play_action("gather", 0.6)
	elif progress <= 0.0:
		_reel_in("It got away.")


func _reel_in(message: String) -> void:
	if not message.is_empty():
		Game.notify(message, "")
	_reset()


func _reset() -> void:
	state = S.IDLE
	tension = 0.0
	progress = 0.0
	_bobber.visible = false
	_line_mesh.clear_surfaces()
	state_changed.emit(state)


func _draw_line() -> void:
	_line_mesh.clear_surfaces()
	if state == S.IDLE or state == S.CHARGE or player.held == null:
		return
	var a := player.held.tip_position()
	var b := _bobber.global_position
	_line_mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
	var sag := 0.0 if state == S.REEL else clampf(a.distance_to(b) * 0.06, 0.1, 0.8)
	for i in 13:
		var t := i / 12.0
		var p := a.lerp(b, t)
		p.y -= sin(t * PI) * sag
		_line_mesh.surface_add_vertex(p)
	_line_mesh.surface_end()
