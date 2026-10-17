class_name StorageMenu
extends MenuBase
## Chest contents beside the pack. Press a slot to move that stack across.

var box: StorageBox
var _title: Label
var _chest_grid: GridContainer
var _pack_slots: Array[ItemSlot] = []
var _chest_slots: Array[ItemSlot] = []


func _ready() -> void:
	super._ready()
	var col := _build_frame(Vector2(1300, 640))
	_title = UITheme.label("Chest", 40, UITheme.INK, true)
	col.add_child(_title)
	col.add_child(UITheme.label("Press a stack to move it to the other side.", 19, UITheme.INK_DIM))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 48)
	var left := VBoxContainer.new()
	left.add_child(UITheme.label("Chest", 24, UITheme.SAND, true))
	_chest_grid = GridContainer.new()
	_chest_grid.columns = 4
	_chest_grid.add_theme_constant_override("h_separation", 10)
	_chest_grid.add_theme_constant_override("v_separation", 10)
	left.add_child(_chest_grid)
	left.add_child(MenuBase.button("Take all", _take_all))
	row.add_child(left)
	var right := VBoxContainer.new()
	right.add_child(UITheme.label("Pack", 24, UITheme.SAND, true))
	var pack := GridContainer.new()
	pack.columns = 6
	pack.add_theme_constant_override("h_separation", 10)
	pack.add_theme_constant_override("v_separation", 10)
	for i in Game.INVENTORY_SIZE:
		var s := ItemSlot.new(88)
		s.bind(Game.inventory, i)
		s.slot_pressed.connect(_from_pack)
		pack.add_child(s)
		_pack_slots.append(s)
	right.add_child(pack)
	row.add_child(right)
	col.add_child(row)
	Game.inventory.changed.connect(_refresh)


func show_box(b: StorageBox) -> void:
	box = b
	for c in _chest_grid.get_children():
		c.queue_free()
	_chest_slots.clear()
	for i in box.inventory.size():
		var s := ItemSlot.new(88)
		s.bind(box.inventory, i)
		s.slot_pressed.connect(_from_chest)
		_chest_grid.add_child(s)
		_chest_slots.append(s)
	if not box.inventory.changed.is_connected(_refresh):
		box.inventory.changed.connect(_refresh)
	_title.text = box.title.capitalize()
	open()


func _on_open() -> void:
	_refresh()
	if not _chest_slots.is_empty():
		_chest_slots[0].grab_focus.call_deferred()


func close() -> void:
	if box and box.inventory.changed.is_connected(_refresh):
		box.inventory.changed.disconnect(_refresh)
	super.close()


func _unhandled_input(event: InputEvent) -> void:
	if is_open and (event.is_action_pressed("cancel") or event.is_action_pressed("pause") or event.is_action_pressed("inventory") or event.is_action_pressed("interact")):
		close()
		get_viewport().set_input_as_handled()


func _from_chest(s: ItemSlot) -> void:
	var item = box.inventory.get_slot(s.index)
	if item == null:
		return
	var id: String = item["id"]
	var before := Game.inventory.count(id)
	box.inventory.transfer_slot(s.index, Game.inventory)
	var got := Game.inventory.count(id) - before
	if got > 0:
		Game.record("collect:" + id, got)
	AudioManager.play("pickup")


func _from_pack(s: ItemSlot) -> void:
	Game.inventory.transfer_slot(s.index, box.inventory)
	AudioManager.play("ui_click")


func _take_all() -> void:
	for i in box.inventory.size():
		if box.inventory.get_slot(i) != null:
			var id: String = box.inventory.get_slot(i)["id"]
			var before := Game.inventory.count(id)
			box.inventory.transfer_slot(i, Game.inventory)
			var got := Game.inventory.count(id) - before
			if got > 0:
				Game.record("collect:" + id, got)
	AudioManager.play("pickup")


func _refresh() -> void:
	for s in _pack_slots:
		s.refresh()
	for s in _chest_slots:
		s.refresh()
