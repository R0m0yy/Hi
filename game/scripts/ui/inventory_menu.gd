class_name InventoryMenu
extends MenuBase
## The pack and crafting screen. Click (or press A on) one slot then another
## to move or swap items; the top row is the hotbar. Recipes on the right
## show what they need and craft with one press.

var _slots: Array[ItemSlot] = []
var _picked := -1
var _detail_name: Label
var _detail_desc: Label
var _use_button: Button
var _recipes: VBoxContainer
var _focus_slot := 0


func _ready() -> void:
	super._ready()
	var col := _build_frame(Vector2(1460, 760))
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 36)
	col.add_child(top)
	# Left: pack grid + details
	var left := VBoxContainer.new()
	left.add_theme_constant_override("separation", 14)
	left.add_child(MenuBase.header("Pack", "Top row is your hotbar. Pick a slot, then another to move it."))
	var grid := GridContainer.new()
	grid.columns = 6
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	for i in Game.INVENTORY_SIZE:
		var s := ItemSlot.new(92)
		s.bind(Game.inventory, i, str(i + 1) if i < Game.HOTBAR_SIZE else "")
		s.slot_pressed.connect(_on_slot)
		s.focus_entered.connect(func() -> void: _show_detail(s.index))
		s.mouse_entered.connect(func() -> void: _show_detail(s.index))
		grid.add_child(s)
		_slots.append(s)
	left.add_child(grid)
	var detail := PanelContainer.new()
	var dsb := UITheme.panel_box(14)
	dsb.bg_color = UITheme.PANEL_LIGHT
	dsb.set_content_margin_all(14)
	detail.add_theme_stylebox_override("panel", dsb)
	detail.custom_minimum_size = Vector2(0, 150)
	var dcol := VBoxContainer.new()
	_detail_name = UITheme.label("", 26, UITheme.SAND, true)
	_detail_desc = UITheme.label("", 19, UITheme.INK_DIM)
	_detail_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_detail_desc.custom_minimum_size = Vector2(560, 0)
	dcol.add_child(_detail_name)
	dcol.add_child(_detail_desc)
	_use_button = MenuBase.button("Eat", _use_detail)
	_use_button.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	dcol.add_child(_use_button)
	detail.add_child(dcol)
	left.add_child(detail)
	top.add_child(left)
	# Right: crafting
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 14)
	right.add_child(MenuBase.header("Craft", "Everything is made by hand from what the islands give you."))
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(640, 560)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_recipes = VBoxContainer.new()
	_recipes.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_recipes.add_theme_constant_override("separation", 10)
	scroll.add_child(_recipes)
	right.add_child(scroll)
	top.add_child(right)
	var footer := HBoxContainer.new()
	footer.alignment = BoxContainer.ALIGNMENT_END
	footer.add_child(UITheme.label("%s / %s close" % [InputBindings.glyph("inventory"), InputBindings.glyph("cancel")], 18, UITheme.INK_DIM))
	col.add_child(footer)
	Game.inventory.changed.connect(_refresh)


func _on_open() -> void:
	_picked = -1
	_refresh()
	_slots[_focus_slot].grab_focus()
	_show_detail(Game.selected)


## _input, not _unhandled_input: the focused pack slot would otherwise take Tab
## for focus navigation, and the pause menu would swallow Escape first.
func _input(event: InputEvent) -> void:
	if not is_open:
		return
	if event.is_action_pressed("inventory") or event.is_action_pressed("pause") or event.is_action_pressed("cancel") and _picked < 0:
		close()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("cancel") and _picked >= 0:
		_picked = -1
		_refresh()
		get_viewport().set_input_as_handled()


func _on_slot(s: ItemSlot) -> void:
	_focus_slot = s.index
	if _picked < 0:
		if Game.inventory.get_slot(s.index) != null:
			_picked = s.index
	else:
		Game.inventory.swap(_picked, s.index)
		_picked = -1
		AudioManager.play("ui_click")
	_refresh()
	_show_detail(s.index)


func _show_detail(i: int) -> void:
	var s = Game.inventory.get_slot(i)
	if s == null:
		_detail_name.text = "Empty slot"
		_detail_desc.text = ""
		_use_button.visible = false
		return
	var def := ItemDB.item(s["id"])
	_detail_name.text = def.get("name", s["id"]) + ("  ×%d" % s["count"] if int(s["count"]) > 1 else "")
	var extra := ""
	if def.get("kind") == "food":
		extra = "\nFood %+d · Water %+d" % [int(def.get("food", 0)), int(def.get("water", 0))]
	elif s.has("dur"):
		extra = "\nDurability %d / %d" % [int(s["dur"]), int(ItemDB.max_durability(s["id"]))]
	_detail_desc.text = def.get("desc", "") + extra
	_use_button.visible = def.get("kind") == "food"
	_use_button.text = "Drink" if s["id"] == "coconut" else "Eat"
	_use_button.set_meta("slot", i)


func _use_detail() -> void:
	var i := int(_use_button.get_meta("slot", -1))
	if i >= 0 and Game.consume_slot(i):
		AudioManager.play("eat")
	_show_detail(i)


func _refresh() -> void:
	for s in _slots:
		s.highlight = s.index == _picked
		s.refresh()
	for c in _recipes.get_children():
		c.queue_free()
	for r in ItemDB.RECIPES:
		_recipes.add_child(_recipe_row(r))


func _recipe_row(r: Dictionary) -> Control:
	var can := Game.inventory.has_items(r["in"])
	var row := PanelContainer.new()
	var sb := UITheme.panel_box(14)
	sb.bg_color = UITheme.PANEL_LIGHT if can else Color(0.04, 0.1, 0.14, 0.7)
	sb.border_color = UITheme.SAND if can else Color(1, 1, 1, 0.08)
	sb.set_content_margin_all(10)
	sb.shadow_size = 0
	row.add_theme_stylebox_override("panel", sb)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	var icon := TextureRect.new()
	icon.texture = ItemDB.icon(r["out"])
	icon.custom_minimum_size = Vector2(64, 64)
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	h.add_child(icon)
	var info := VBoxContainer.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.add_child(UITheme.label(ItemDB.display_name(r["out"]), 23, UITheme.INK if can else UITheme.INK_DIM, true))
	var needs := HBoxContainer.new()
	needs.add_theme_constant_override("separation", 12)
	for id in r["in"]:
		var have := Game.inventory.count(id)
		var need := int(r["in"][id])
		var cell := HBoxContainer.new()
		cell.add_theme_constant_override("separation", 4)
		var ic := TextureRect.new()
		ic.texture = ItemDB.icon(id)
		ic.custom_minimum_size = Vector2(28, 28)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		cell.add_child(ic)
		cell.add_child(UITheme.label("%d/%d" % [mini(have, need), need], 18, UITheme.GOOD if have >= need else UITheme.CORAL))
		cell.tooltip_text = ItemDB.display_name(id)
		needs.add_child(cell)
	info.add_child(needs)
	h.add_child(info)
	var b := MenuBase.button("Craft", func() -> void: _craft(r))
	b.disabled = not can
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(b)
	row.add_child(h)
	return row


func _craft(r: Dictionary) -> void:
	if not Game.inventory.remove_items(r["in"]):
		return
	var left := Game.inventory.add(r["out"], int(r["count"]))
	if left > 0:
		Game.notify("Pack full: dropped the %s" % ItemDB.display_name(r["out"]), r["out"])
	Game.notify("Crafted %s" % ItemDB.display_name(r["out"]), r["out"])
	Game.record("craft:" + String(r["out"]))
	AudioManager.play("craft")
