class_name PlayerController
extends CharacterBody3D
## The player. Camera-relative movement on land with stamina-limited
## running and jumping, automatic swimming in deep water, diving while the
## dive action is held (breath runs out), boarding boats, interacting with
## the closest object in reach and using the tool in the selected hotbar
## slot. Drives the skeletal animations of the character model and the
## survival needs in Game.

enum Mode { GROUND, SWIM, DIVE, BOAT }

signal focus_changed(target: Node)
signal busy_changed(label: String, progress: float)
signal mode_changed(mode: int)

const LOOPING := ["idle", "walk", "run", "swim", "swim_idle", "dive", "fish_reel", "fish_idle",
		"cook", "row", "sit", "fall", "sleep"]
## Fallbacks for clips a character model may not have.
const FALLBACK := {"swim_idle": "swim", "fish_idle": "idle", "row": "idle", "sit": "idle",
		"jump": "idle", "fall": "idle", "eat": "gather", "drink": "gather", "sleep": "idle",
		"spear_thrust": "spear_throw", "interact": "gather", "hurt": "idle"}

@export var walk_speed := 3.4
@export var run_speed := 6.4
@export var swim_speed := 2.4
@export var swim_sprint_speed := 3.8
@export var dive_speed := 2.2
@export var jump_velocity := 6.2
@export var acceleration := 14.0
@export var turn_speed := 12.0
@export var gravity := 22.0
## Water deeper than this (metres) at the player's position means swimming.
@export var swim_depth := 1.0
## How far below the surface the body origin floats while swimming.
@export var float_depth := 1.05
@export var seabed_clearance := 0.6
## Height of the eyes above the body origin (for "is the head underwater").
@export var head_height := 1.25

@onready var model: Node3D = $Model

var mode := Mode.GROUND
var focus: Interactable
var boat: Boat
var held: HeldItem
var fishing: FishingRod
var spear: SpearAttack
var builder: Builder
var anim: AnimationPlayer
var _rig: IsometricCamera
var _action_lock := 0.0
var _busy := 0.0
var _busy_total := 0.0
var _busy_label := ""
var _busy_done: Callable
var _focus_timer := 0.0
var _sprinting := false
var _step_accum := 0.0


func _ready() -> void:
	add_to_group("player")
	MaterialLibrary.apply(model)
	_find_animation_player()
	_rig = get_tree().get_first_node_in_group("camera_rig") as IsometricCamera
	held = get_node_or_null("HeldItem") as HeldItem
	fishing = get_node_or_null("FishingRod") as FishingRod
	spear = get_node_or_null("SpearAttack") as SpearAttack
	builder = get_node_or_null("Builder") as Builder
	Game.hotbar_changed.connect(_on_hotbar_changed)
	Game.inventory.changed.connect(_on_selection_changed)
	_on_selection_changed.call_deferred()


func _find_animation_player() -> void:
	var found := model.find_children("*", "AnimationPlayer", true, false)
	if found.is_empty():
		return
	anim = found[0] as AnimationPlayer
	for clip in LOOPING:
		if anim.has_animation(clip):
			anim.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	anim.play(_clip("idle"))


## Swaps the visual character (used when the model is replaced).
func set_model(scene: PackedScene) -> void:
	var old := model
	model = scene.instantiate()
	model.name = "Model"
	add_child(model)
	model.rotation = old.rotation
	old.queue_free()
	MaterialLibrary.apply(model)
	_find_animation_player()
	if held:
		held.rebind()


func can_control() -> bool:
	return Game.is_playing() and not Game.ui_open and _busy <= 0.0 and mode != Mode.BOAT \
			and not (fishing and fishing.blocks_movement())


func _physics_process(delta: float) -> void:
	if mode == Mode.BOAT:
		_boat_process(delta)
		return
	var control := can_control()
	var wish := _wish_direction() if control else Vector3.ZERO
	_update_mode(control)
	var exertion := 0.0
	var stamina: float = Game.stats.get("stamina", 100.0)
	var want_sprint := control and Input.is_action_pressed("sprint") and wish != Vector3.ZERO
	if want_sprint and (_sprinting or stamina > 12.0) and stamina > 0.5:
		_sprinting = true
	else:
		_sprinting = false
	match mode:
		Mode.GROUND:
			var speed := run_speed if _sprinting else walk_speed
			if builder and builder.active:
				speed = walk_speed * 0.8
			_move_horizontal(wish * speed, delta)
			if not is_on_floor():
				velocity.y -= gravity * delta
			elif control and Input.is_action_just_pressed("jump") and not (fishing and fishing.busy()):
				velocity.y = jump_velocity
				play_action("jump", 0.35)
				AudioManager.play("jump", global_position, -8.0)
			else:
				velocity.y = -0.5
			if _sprinting:
				exertion = 14.0
		Mode.SWIM:
			var speed := swim_sprint_speed if _sprinting else swim_speed
			_move_horizontal(wish * speed, delta)
			velocity.y = (_surface_y() - float_depth - global_position.y) * 6.0
			exertion = 9.0 if _sprinting else (1.2 if wish != Vector3.ZERO else 0.0)
		Mode.DIVE:
			_move_horizontal(wish * swim_speed * (1.25 if _sprinting else 0.9), delta)
			var floor_y := _ground_y() + seabed_clearance
			var target := maxf(floor_y, global_position.y - 4.0)
			velocity.y = clampf((target - global_position.y) * 4.0, -dive_speed, dive_speed)
			exertion = 8.0 if _sprinting else 0.0
	move_and_slide()
	Game.tick_needs(delta, exertion, is_head_underwater())
	_face(wish, delta)
	_animate(delta)
	_footsteps(delta)
	_update_busy(delta)
	_focus_timer -= delta
	if _focus_timer <= 0.0:
		_focus_timer = 0.1
		_update_focus()
	if control:
		_handle_buttons()


func _handle_buttons() -> void:
	if Input.is_action_just_pressed("interact") and focus != null and not (builder and builder.active):
		var acts := focus.actions(self)
		for a in acts:
			if a.get("action", "") == "interact":
				focus.interact(self)
				_focus_timer = 0.0
				break
	if Input.is_action_just_pressed("use_tool"):
		_use_tool()
	for i in Game.HOTBAR_SIZE:
		if Input.is_action_just_pressed("hotbar_%d" % (i + 1)):
			Game.select(i)
	if Input.is_action_just_pressed("hotbar_next"):
		Game.select(Game.selected + 1)
	if Input.is_action_just_pressed("hotbar_prev"):
		Game.select(Game.selected - 1)


func _use_tool() -> void:
	var id := Game.selected_item()
	if builder and builder.active:
		return  # the builder handles confirm
	if fishing and (id == "fishing_rod" or fishing.busy()):
		return  # the rod reads press/hold/release itself
	if focus and id != "" and focus.accepts_tool(id):
		focus.use_tool(self, id)
		return
	match ItemDB.kind(id):
		"food":
			if Game.consume_slot(Game.selected):
				play_action("eat")
				AudioManager.play("drink" if id == "coconut" else "eat", global_position)
		"placeable":
			if builder and mode == Mode.GROUND:
				builder.begin(id)
		"tool":
			if id == "spear" and spear:
				spear.thrust()
			elif id == "hatchet":
				play_action("chop")
				AudioManager.play("swing", global_position, -6.0)


func _on_hotbar_changed(_i: int) -> void:
	_on_selection_changed()


func _on_selection_changed() -> void:
	if held:
		held.show_item(Game.selected_item())


## Wears the tool in the selected slot; announces it if it breaks.
func wear_selected(amount: float) -> void:
	var id := Game.selected_item()
	if Game.inventory.wear(Game.selected, amount):
		Game.notify("Your %s broke" % ItemDB.display_name(id), id)
		AudioManager.play("break", global_position)


# ---------------------------------------------------------------------------
# Busy actions (cooking, resting): hold the player still with a progress bar
# ---------------------------------------------------------------------------

func start_busy(seconds: float, label: String, anim_name: String, on_done: Callable) -> void:
	if _busy > 0.0:
		return
	_busy = seconds
	_busy_total = seconds
	_busy_label = label
	_busy_done = on_done
	velocity = Vector3.ZERO
	_play(anim_name, 0.2)
	_action_lock = seconds
	busy_changed.emit(label, 0.0)


func is_busy() -> bool:
	return _busy > 0.0


func _update_busy(delta: float) -> void:
	if _busy <= 0.0:
		return
	_busy -= delta
	busy_changed.emit(_busy_label, clampf(1.0 - _busy / _busy_total, 0.0, 1.0))
	if _busy <= 0.0:
		_busy = 0.0
		busy_changed.emit("", 1.0)
		if _busy_done.is_valid():
			_busy_done.call()


# ---------------------------------------------------------------------------
# Interaction focus
# ---------------------------------------------------------------------------

func _update_focus() -> void:
	var best: Interactable = null
	var best_score := INF
	var fwd := model.global_basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	if mode == Mode.GROUND or mode == Mode.SWIM or mode == Mode.DIVE:
		for node in get_tree().get_nodes_in_group("interactable"):
			var it := node as Interactable
			if it == null:
				continue
			var p := it.focus_position()
			var d := p - global_position
			var flat := Vector2(d.x, d.z).length()
			if flat > it.reach or d.y > 2.6 or d.y < -2.2:
				continue
			if it.actions(self).is_empty():
				continue
			var facing := 1.0 if flat < 0.4 else fwd.dot(Vector3(d.x, 0.0, d.z) / flat)
			var score := flat / it.reach - facing * 0.6 - it.priority
			if score < best_score:
				best_score = score
				best = it
	if best != focus:
		focus = best
		focus_changed.emit(focus)


# ---------------------------------------------------------------------------
# Boats
# ---------------------------------------------------------------------------

func board(b: Boat) -> void:
	boat = b
	mode = Mode.BOAT
	mode_changed.emit(mode)
	velocity = Vector3.ZERO
	$CollisionShape3D.disabled = true
	focus = null
	focus_changed.emit(null)
	_play(b.driver_animation, 0.25)
	if _rig:
		_rig.zoom_size = maxf(_rig.zoom_size, 24.0)
	Game.record("board")


func unboard(spot: Vector3) -> void:
	boat = null
	$CollisionShape3D.disabled = false
	global_position = spot
	velocity = Vector3.ZERO
	mode = Mode.GROUND
	_update_mode(true)
	mode_changed.emit(mode)
	if _rig:
		_rig.zoom_size = 17.0


func _boat_process(delta: float) -> void:
	if boat == null:
		mode = Mode.GROUND
		return
	var seat := boat.seat_transform()
	global_position = seat.origin
	model.global_rotation = Vector3(0.0, boat.global_rotation.y, 0.0)
	velocity = boat.global_basis.z * boat.speed
	Game.tick_needs(delta, 3.0 if absf(boat.speed) > 0.5 else 0.0, false)
	if anim:
		var want := _clip(boat.driver_animation)
		if anim.current_animation != want:
			anim.play(want, 0.25)
		anim.speed_scale = 0.6 + absf(boat.speed) / boat.max_speed * 0.8
	if Game.is_playing() and not Game.ui_open and Input.is_action_just_pressed("interact"):
		boat.disembark()


# ---------------------------------------------------------------------------
# Movement and animation
# ---------------------------------------------------------------------------

## Plays a one-shot action (gather, chop, cook...) and holds locomotion
## animations until it finishes.
func play_action(anim_name: String, lock: float = -1.0) -> void:
	if anim == null:
		return
	var clip := _clip(anim_name)
	if not anim.has_animation(clip):
		return
	anim.play(clip, 0.12)
	anim.speed_scale = 1.0
	_action_lock = lock if lock >= 0.0 else anim.get_animation(clip).length


func _clip(name: String) -> String:
	if anim == null:
		return name
	if anim.has_animation(name):
		return name
	var fb: String = FALLBACK.get(name, "idle")
	return fb if anim.has_animation(fb) else "idle"


func _play(name: String, blend: float = 0.2) -> void:
	if anim:
		anim.play(_clip(name), blend)


func _wish_direction() -> Vector3:
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	if input == Vector2.ZERO:
		return Vector3.ZERO
	var yaw := deg_to_rad(_rig.yaw_degrees) if _rig else 0.0
	var right := Vector3(cos(yaw), 0.0, -sin(yaw))
	var back := Vector3(sin(yaw), 0.0, cos(yaw))
	return (right * input.x + back * input.y).limit_length(1.0)


func _move_horizontal(target: Vector3, delta: float) -> void:
	var t := 1.0 - exp(-acceleration * delta)
	velocity.x = lerpf(velocity.x, target.x, t)
	velocity.z = lerpf(velocity.z, target.z, t)


func _update_mode(control: bool) -> void:
	var depth := water_depth()
	var before := mode
	var dive_held := control and Input.is_action_pressed("dive")
	match mode:
		Mode.GROUND:
			if depth > swim_depth and global_position.y < _surface_y() - float_depth + 0.25:
				mode = Mode.SWIM
		Mode.SWIM:
			if depth < swim_depth - 0.15:
				mode = Mode.GROUND
			elif dive_held and depth > swim_depth + 0.8 and Game.stats.get("oxygen", 100.0) > 5.0:
				mode = Mode.DIVE
		Mode.DIVE:
			var out_of_air: bool = Game.stats.get("oxygen", 100.0) <= 0.0
			if not dive_held or out_of_air or depth < swim_depth:
				velocity.y = dive_speed
				mode = Mode.SWIM
	if mode != before:
		mode_changed.emit(mode)
		if mode == Mode.SWIM and before == Mode.GROUND:
			AudioManager.play("splash", global_position)
		elif mode == Mode.DIVE:
			AudioManager.play("dive", global_position)
		elif before == Mode.DIVE:
			AudioManager.play("surface", global_position)


func _face(wish: Vector3, delta: float) -> void:
	if fishing and fishing.locks_facing():
		return
	var flat := Vector3(velocity.x, 0.0, velocity.z)
	if flat.length() < 0.2 and wish == Vector3.ZERO:
		return
	var dir := wish if wish != Vector3.ZERO else flat.normalized()
	face_direction(dir, delta)


func face_direction(dir: Vector3, delta: float = 1.0) -> void:
	var target := atan2(dir.x, dir.z)  # the model faces +Z
	model.rotation.y = lerp_angle(model.rotation.y, target, 1.0 - exp(-turn_speed * delta))


func _animate(delta: float) -> void:
	if anim == null:
		return
	if _action_lock > 0.0:
		_action_lock -= delta
		return
	var speed := Vector2(velocity.x, velocity.z).length()
	var want := "idle"
	var rate := 1.0
	match mode:
		Mode.GROUND:
			if not is_on_floor() and velocity.y < -2.0:
				want = "fall"
			elif speed > walk_speed * 1.15:
				want = "run"
				rate = speed / run_speed * 1.1
			elif speed > 0.3:
				want = "walk"
				rate = speed / walk_speed * 1.05
		Mode.SWIM:
			want = "swim" if speed > 0.4 else "swim_idle"
			rate = 0.7 + speed / swim_speed * 0.5
		Mode.DIVE:
			want = "dive"
			rate = 0.8 + speed / swim_speed * 0.4
	if fishing and fishing.busy():
		want = fishing.animation()
		rate = 1.0
	var clip := _clip(want)
	if anim.current_animation != clip:
		anim.play(clip, 0.2)
	anim.speed_scale = maxf(rate, 0.4)


func _footsteps(delta: float) -> void:
	if mode != Mode.GROUND or not is_on_floor():
		return
	var speed := Vector2(velocity.x, velocity.z).length()
	if speed < 0.5:
		return
	_step_accum += speed * delta
	var stride := 1.25 if _sprinting else 0.9
	if _step_accum >= stride:
		_step_accum = 0.0
		var on_grass := false
		AudioManager.play("step_grass" if on_grass else "step_sand", global_position, -10.0 if not _sprinting else -6.0, 0.12)


## Depth of water (metres) between the surface and the ground under the player.
func water_depth() -> float:
	return _surface_y() - _ground_y()


func is_head_underwater() -> bool:
	return mode == Mode.DIVE and global_position.y + head_height < _surface_y() - 0.1


func _surface_y() -> float:
	return World.surface_at(global_position)


func _ground_y() -> float:
	return World.height_at(global_position.x, global_position.z)


## Puts the player at `pos` facing `yaw_deg` (spawning, loading, respawning).
func teleport(pos: Vector3, yaw_deg: float = 0.0) -> void:
	if boat:
		boat.driver = null
		boat = null
		$CollisionShape3D.disabled = false
	global_position = pos
	velocity = Vector3.ZERO
	model.rotation.y = deg_to_rad(yaw_deg)
	mode = Mode.GROUND
	_update_mode(false)
	if _rig:
		_rig.snap_to_target()
