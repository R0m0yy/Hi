@tool
class_name Campfire
extends StylizedAsset
## Campfire: flickers the generated "Flame" mesh and the warm light.
## Cooking hooks into `is_lit` later (Phase 6).

@export var is_lit := true:
	set(v):
		is_lit = v
		_update_visibility()
@export var light_energy := 2.2
@export var flicker_speed := 9.0

@onready var _light: OmniLight3D = $FireLight
@onready var _sparks: GPUParticles3D = $Sparks

var _flame: Node3D
var _t := 0.0


func _ready() -> void:
	super._ready()
	_flame = find_child("Flame", true, false) as Node3D
	_update_visibility()


func _process(delta: float) -> void:
	if not is_lit or _flame == null:
		return
	_t += delta * flicker_speed
	var n := sin(_t) * 0.5 + sin(_t * 1.7 + 1.3) * 0.3 + sin(_t * 3.1 + 0.4) * 0.2
	_flame.scale = Vector3(1.0 + n * 0.06, 1.0 + n * 0.14, 1.0 - n * 0.05)
	_flame.rotation.y += delta * 0.8
	_light.light_energy = light_energy * (1.0 + n * 0.18)


func _update_visibility() -> void:
	if not is_inside_tree():
		return
	if _flame:
		_flame.visible = is_lit
	if _light:
		_light.visible = is_lit
	if _sparks:
		_sparks.emitting = is_lit
