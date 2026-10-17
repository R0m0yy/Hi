class_name StorageBox
extends Interactable
## A chest with its own inventory. Opening it shows the storage panel.

signal opened(box: StorageBox)

@export var title := "Storage Chest"
@export var slots := 16
## Items placed in a fresh game (before any save data exists).
@export var starting_items := {}

var inventory: Inventory


func _ready() -> void:
	inventory = Inventory.new(slots)
	super._ready()
	inventory.changed.connect(func() -> void: save_state({"items": inventory.to_data()}))


func actions(_player: Node) -> Array:
	return [{"action": "interact", "text": "Open " + title}]


func interact(_player: Node) -> void:
	AudioManager.play("chest_open", global_position)
	Game.open_storage(self)


func load_state(data: Dictionary) -> void:
	if data.has("items"):
		inventory.from_data(data["items"])
	else:
		for id in starting_items:
			inventory.add(id, int(starting_items[id]))
