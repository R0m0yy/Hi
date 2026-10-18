class_name Boat
extends Interactable
## A rowboat or raft the player boards and steers (W/S throttle, A/D turn).
## It floats on the water surface, bobs, and stops when the water gets too
## shallow. Interact again to step ashore (or slip into the water).

signal boarded(driver: Node)
signal left(driver: Node)

@export var title := "rowboat"
@export var max_speed := 5.5
@export var reverse_speed := 2.0
@export var accel := 2.2
@export var turn_rate := 1.5
@export var draft := 0.45
@export var needs_repair := false
@export var repair_cost := {"wood": 6, "rope": 2}
## Seat in the boat's local space.
@export var seat := Vector3(0.0, 0.15, -0.2)
@export var visual_path: NodePath
## Animation the driver plays while aboard.
@export var driver_animation := "row"

var driver: Node = null
var speed := 0.0
var _yaw := 0.0
var _t := 0.0
var _visual: Node3D


var _wake: GPUParticles3D


func _ready() -> void:
	_visual = get_node_or_null(visual_path) as Node3D
	_yaw = global_rotation.y
	super._ready()
	add_to_group("boats")
	_wake = _make_wake()
	add_child(_wake)
	_wake.position = Vector3(0, 0.05, -1.2)


static func _make_wake() -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = "Wake"
	p.amount = 64
	p.lifetime = 2.2
	p.local_coords = false
	p.emitting = false
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(0.45, 0.0, 0.1)
	pm.gravity = Vector3.ZERO
	pm.spread = 30.0
	pm.initial_velocity_min = 0.1
	pm.initial_velocity_max = 0.35
	pm.scale_min = 0.6
	pm.scale_max = 1.2
	var curve := CurveTexture.new()
	var c := Curve.new()
	c.add_point(Vector2(0.0, 0.4))
	c.add_point(Vector2(0.3, 1.0))
	c.add_point(Vector2(1.0, 1.6))
	curve.curve = c
	pm.scale_curve = curve
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 0.2, 1.0])
	grad.colors = PackedColorArray([Color(1, 0.98, 0.9, 0.0), Color(1, 0.98, 0.9, 0.6), Color(1, 0.98, 0.9, 0.0)])
	var gt := GradientTexture1D.new()
	gt.gradient = grad
	pm.color_ramp = gt
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(0.55, 0.55)
	quad.orientation = PlaneMesh.FACE_Y
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = _foam_texture()
	quad.material = mat
	p.draw_pass_1 = quad
	return p


## A soft foam blob with a broken edge; overlapping blobs read as a trail.
static func _foam_texture() -> Texture2D:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 41
	var bumps: Array[Vector3] = []  # x, y, radius of the lumps that make the outline
	for i in 9:
		var a := TAU * i / 9.0 + rng.randf_range(-0.3, 0.3)
		var r := rng.randf_range(0.25, 0.45)
		bumps.append(Vector3(cos(a) * (0.62 - r * 0.5), sin(a) * (0.62 - r * 0.5), r))
	for y in 64:
		for x in 64:
			var p := Vector2(x - 31.5, y - 31.5) / 31.5
			var cover := clampf(1.0 - p.length() / 0.5, 0.0, 1.0)
			for b in bumps:
				cover = maxf(cover, clampf(1.0 - p.distance_to(Vector2(b.x, b.y)) / b.z, 0.0, 1.0))
			var alpha := smoothstep(0.05, 0.45, cover) * (0.55 + 0.45 * cover)
			img.set_pixel(x, y, Color(1, 1, 1, alpha))
	return ImageTexture.create_from_image(img)


func focus_position() -> Vector3:
	return global_position


func actions(_player: Node) -> Array:
	if driver != null:
		return []
	if needs_repair:
		var cost := _cost_text()
		if Game.inventory.has_items(repair_cost):
			return [{"action": "interact", "text": "Repair %s (%s)" % [title, cost]}]
		return [{"action": "", "text": "Damaged %s: repair needs %s" % [title, cost]}]
	return [{"action": "interact", "text": "Board " + title}]


func interact(player: Node) -> void:
	if driver != null or player == null:
		return
	if needs_repair:
		if Game.inventory.remove_items(repair_cost):
			needs_repair = false
			player.play_action("chop")
			AudioManager.play("hammer", global_position)
			Game.notify("The %s is seaworthy again" % title, "")
			Game.record("repair:" + title)
			_save()
		return
	driver = player
	speed = 0.0
	player.board(self)
	boarded.emit(player)
	AudioManager.play("boat_board", global_position)


## Called by the driver when interact is pressed aboard.
func disembark() -> void:
	if driver == null:
		return
	var player := driver
	var land := World.find_land_near(global_position, 5.0)
	var spot: Vector3
	if is_nan(land.y):
		spot = global_position + global_basis.x * 1.4 + Vector3.UP * 0.2
	else:
		spot = land + Vector3.UP * 0.3
	driver = null
	speed = 0.0
	player.unboard(spot)
	left.emit(player)
	_save()


func seat_transform() -> Transform3D:
	return global_transform * Transform3D(Basis(), seat)


func _physics_process(delta: float) -> void:
	_t += delta
	if driver != null:
		var throttle := Input.get_axis("move_back", "move_forward")
		var steer := Input.get_axis("move_right", "move_left")
		if Game.ui_open or not Game.is_playing():
			throttle = 0.0
			steer = 0.0
		var target := throttle * (max_speed if throttle > 0.0 else reverse_speed)
		speed = move_toward(speed, target, accel * delta)
		var grip := clampf(absf(speed) / max_speed + 0.4, 0.0, 1.0)
		_yaw += steer * turn_rate * grip * delta * (1.0 if speed >= -0.1 else -1.0)
	else:
		speed = move_toward(speed, 0.0, accel * 0.6 * delta)
	var forward := Vector3(sin(_yaw), 0.0, cos(_yaw))
	var next := global_position + forward * speed * delta
	var probe := next + forward * signf(speed) * 1.6
	if absf(speed) > 0.01 and World.height_at(probe.x, probe.z) > World.water_level() - draft:
		speed = -speed * 0.25  # bump against the shallows
		AudioManager.play("boat_bump", global_position, -6.0)
	else:
		global_position.x = next.x
		global_position.z = next.z
	if _wake:
		_wake.emitting = absf(speed) > 1.0
		_wake.amount_ratio = clampf(absf(speed) / max_speed, 0.2, 1.0)
	var surface := World.surface_at(global_position)
	global_position.y = lerpf(global_position.y, surface + sin(_t * 1.3) * 0.04, 1.0 - exp(-6.0 * delta))
	global_rotation = Vector3(sin(_t * 1.1) * 0.03 + speed * 0.006, _yaw, sin(_t * 0.9 + 1.0) * 0.035)


func _cost_text() -> String:
	var parts := []
	for id in repair_cost:
		parts.append("%d %s" % [repair_cost[id], ItemDB.display_name(id).to_lower()])
	return ", ".join(parts)


func _save() -> void:
	save_state({"repaired": not needs_repair, "pos": [global_position.x, global_position.y, global_position.z], "yaw": _yaw})


func load_state(data: Dictionary) -> void:
	if data.is_empty():
		return
	if bool(data.get("repaired", false)):
		needs_repair = false
	if data.has("pos"):
		var p: Array = data["pos"]
		global_position = Vector3(p[0], p[1], p[2])
		_yaw = float(data.get("yaw", _yaw))
		global_rotation.y = _yaw


## Saved on demand by SaveManager so the boat is where it was left.
func capture_state() -> void:
	_save()
