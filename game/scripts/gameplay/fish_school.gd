class_name FishSchool
extends Node3D
## A school of one species that roams a patch of water: boids-style
## separation, alignment and cohesion, a wandering goal inside its home
## radius, depth limits between the seabed and the surface, and a quick
## scatter away from a nearby swimmer. Caught fish come back after a while.

@export var species := "snapper"
@export var count := 8
@export var home_radius := 7.0
@export var respawn_seconds := 90.0

var fish: Array[Fish] = []
var _goal := Vector3.ZERO
var _goal_timer := 0.0
var _rng := RandomNumberGenerator.new()
var _model: PackedScene
var _speed := 1.6
var _pending := 0.0
var _player: Node3D
var _lost := 0


func _ready() -> void:
	_rng.seed = hash(name)
	var def: Dictionary = ItemDB.FISH[species]
	_speed = def["speed"]
	_model = load(def["model"])
	_goal = global_position
	for i in count:
		_spawn_fish(global_position + Vector3(_rng.randf_range(-1.5, 1.5), _rng.randf_range(-0.4, 0.4), _rng.randf_range(-1.5, 1.5)))


func _spawn_fish(pos: Vector3) -> void:
	var f := Fish.new()
	f.name = "Fish%d" % fish.size()
	add_child(f)
	f.setup(species, self, _model, _rng)
	f.top_level = true
	f.global_position = _clamp_depth(pos)
	f.velocity = Vector3(_rng.randf_range(-1, 1), 0.0, _rng.randf_range(-1, 1)).normalized() * _speed * 0.5
	fish.append(f)


func on_fish_lost(f: Fish) -> void:
	fish.erase(f)
	_lost += 1
	if _pending <= 0.0:
		_pending = respawn_seconds


func _physics_process(delta: float) -> void:
	if fish.is_empty() and _lost == 0:
		return
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node3D
	_goal_timer -= delta
	if _goal_timer <= 0.0:
		_goal_timer = _rng.randf_range(4.0, 9.0)
		var a := _rng.randf() * TAU
		var r := _rng.randf() * home_radius
		_goal = _clamp_depth(global_position + Vector3(cos(a) * r, _rng.randf_range(-1.0, 1.0), sin(a) * r))
	if _lost > 0:
		_pending -= delta
		if _pending <= 0.0:
			_lost -= 1
			_spawn_fish(_goal)
			_pending = respawn_seconds if _lost > 0 else 0.0
	var centre := Vector3.ZERO
	var heading := Vector3.ZERO
	for f in fish:
		centre += f.global_position
		heading += f.velocity
	if fish.is_empty():
		return
	centre /= fish.size()
	heading /= fish.size()
	var threat := Vector3.INF
	if _player and _player.has_method("water_depth") and (_player.get("mode") as int) != 0:
		threat = _player.global_position + Vector3.UP * 0.6
	for f in fish:
		var p := f.global_position
		var steer := Vector3.ZERO
		steer += (centre - p) * 0.6                    # cohesion
		steer += (heading - f.velocity) * 0.8          # alignment
		steer += (_goal - p).limit_length(3.0) * 0.5   # wander goal
		for o in fish:
			if o == f:
				continue
			var d := p - o.global_position
			var dl := d.length()
			if dl < 0.6 and dl > 0.001:
				steer += d / dl * (0.6 - dl) * 6.0    # separation
		var max_speed := _speed
		if threat != Vector3.INF:
			var away := p - threat
			var ad := away.length()
			if ad < 3.2:
				steer += away.normalized() * (3.2 - ad) * 5.0
				max_speed = _speed * 2.4
		# Depth limits.
		var ground := World.height_at(p.x, p.z) + 0.45
		var surface := World.water_level() - 0.45
		if p.y < ground + 0.3:
			steer.y += (ground + 0.3 - p.y) * 6.0
		if p.y > surface - 0.2:
			steer.y -= (p.y - surface + 0.2) * 6.0
		if World.depth_at(p.x, p.z) < 0.9:
			steer += (global_position - p).normalized() * 3.0  # head back to open water
		f.velocity += steer * delta
		f.velocity.y *= 0.96
		var sp := f.velocity.length()
		if sp > max_speed:
			f.velocity = f.velocity / sp * max_speed
		elif sp < _speed * 0.35:
			f.velocity = f.velocity.normalized() * _speed * 0.35 if sp > 0.001 else Vector3.FORWARD * 0.2
		var np := p + f.velocity * delta
		np = _clamp_depth(np)
		f.global_position = np
		var flat := Vector3(f.velocity.x, f.velocity.y * 0.5, f.velocity.z)
		if flat.length() > 0.05:
			var target := Basis.looking_at(-flat.normalized(), Vector3.UP)
			f.global_basis = f.global_basis.orthonormalized().slerp(target, 1.0 - exp(-6.0 * delta))
		f.set_swim_rate(clampf(f.velocity.length() / _speed, 0.4, 2.6))


func _clamp_depth(p: Vector3) -> Vector3:
	var ground := World.height_at(p.x, p.z) + 0.35
	var surface := World.water_level() - 0.35
	if surface < ground:
		p.y = (ground + surface) * 0.5
	else:
		p.y = clampf(p.y, ground, surface)
	return p
