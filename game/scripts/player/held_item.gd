class_name HeldItem
extends Node
## Shows the selected tool in the character's right hand (a BoneAttachment3D
## on the hand bone). Tool models are authored with the grip at the origin
## and the shaft along +Y; OFFSETS turn them into the fist (bones point
## down the limb with local Z forward).

## Tool -> [pitch degrees about the bone's X, offset along the bone].
## On the explorer's hand bone, local Z runs out of the thumb side of the
## fist, so 90 points the shaft straight out of the fist. The rod sits at 60:
## near-level while waiting for a bite, raised high while reeling.
const GRIPS := {
	"hatchet": [80.0, 0.04],
	"spear": [90.0, 0.04],
	"fishing_rod": [60.0, 0.04],
}


static func grip_transform(id: String) -> Transform3D:
	var g: Array = GRIPS.get(id, [90.0, 0.04])
	return Transform3D(Basis.from_euler(Vector3(deg_to_rad(g[0]), 0.0, 0.0)), Vector3(0.0, g[1], 0.0))


## The first of these bones found on the model's skeleton holds the tool.
@export var bone_names: PackedStringArray = ["DEF-hand.R", "hand.R"]

var current_id := ""
var node: Node3D
var _attach: BoneAttachment3D


func _ready() -> void:
	rebind.call_deferred()


func rebind() -> void:
	var player := get_parent() as PlayerController
	if _attach and is_instance_valid(_attach):
		_attach.queue_free()
	_attach = null
	node = null
	var skels := player.model.find_children("*", "Skeleton3D", true, false)
	if skels.is_empty():
		return
	var skel := skels[0] as Skeleton3D
	var bone := ""
	for b in bone_names:
		if skel.find_bone(b) >= 0:
			bone = b
			break
	if bone.is_empty():
		push_warning("HeldItem: no hand bone on %s" % player.model.name)
		return
	_attach = BoneAttachment3D.new()
	_attach.name = "HandAttachment"
	_attach.bone_name = bone
	skel.add_child(_attach)
	var id := current_id
	current_id = ""
	show_item(id)


func show_item(id: String) -> void:
	if id == current_id:
		return
	current_id = id
	if node and is_instance_valid(node):
		node.queue_free()
	node = null
	if _attach == null or ItemDB.kind(id) != "tool":
		return
	var path := ItemDB.model_path(id)
	if path.is_empty():
		return
	node = (load(path) as PackedScene).instantiate()
	MaterialLibrary.apply(node)
	node.transform = grip_transform(id)
	_attach.add_child(node)


func set_visible_in_hand(v: bool) -> void:
	if node:
		node.visible = v


## World position of the rod tip (or the hand when no tip marker exists).
func tip_position() -> Vector3:
	if node:
		var tip := node.find_child("Tip", true, false) as Node3D
		if tip:
			return tip.global_position
		return node.global_position
	if _attach:
		return _attach.global_position
	return (get_parent() as Node3D).global_position + Vector3.UP
