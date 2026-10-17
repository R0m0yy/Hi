class_name HUD
extends CanvasLayer
## In-game overlay: survival bars, oxygen, hotbar, interaction prompts,
## notifications, the current objective, clock and island name, cooking
## progress, the fishing tension meter, placement hints, an underwater
## vignette and a damage flash.

var player: PlayerController

var _bars := {}
var _oxygen_row: Control
var _hotbar: Array[ItemSlot] = []
var _prompt_box: VBoxContainer
var _prompt_panel: PanelContainer
var _feed: VBoxContainer
var _objective_title: Label
var _objective_text: Label
var _objective_count: Label
var _clock: Label
var _place_label: Label
var _busy_panel: PanelContainer
var _busy_label: Label
var _busy_bar: ProgressBar
var _fish_panel: PanelContainer
var _fish_tension: ProgressBar
var _fish_progress: ProgressBar
var _fish_hint: Label
var _bite_label: Label
var _vignette: ColorRect
var _vignette_mat: ShaderMaterial
var _flash: ColorRect
var _place_panel: PanelContainer
var _last_health := 100.0
var _root: Control


func _ready() -> void:
	layer = 5
	add_to_group("hud")
	_root = Control.new()
	_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = UITheme.get_theme()
	add_child(_root)
	_build_overlays()
	_build_stats()
	_build_hotbar()
	_build_prompt()
	_build_feed()
	_build_objective()
	_build_clock()
	_build_busy()
	_build_fishing()
	_build_placement()
	Game.stats_changed.connect(_on_stats)
	Game.hotbar_changed.connect(_on_hotbar_changed)
	Game.inventory.changed.connect(_refresh_hotbar)
	Game.notified.connect(_on_notified)
	Game.objective_changed.connect(_refresh_objective)
	InputBindings.device_changed.connect(_on_device_changed)
	_refresh_hotbar()
	_refresh_objective()
	_on_stats()


func bind_player(p: PlayerController) -> void:
	player = p
	p.focus_changed.connect(func(_t: Node) -> void: _refresh_prompt())
	p.busy_changed.connect(_on_busy)
	if p.fishing:
		p.fishing.state_changed.connect(_on_fishing_state)
		p.fishing.reel_changed.connect(_on_reel)
	if p.builder:
		p.builder.placement_changed.connect(_on_placement)
	_refresh_prompt()


func _on_hotbar_changed(_i: int) -> void:
	_refresh_hotbar()


func _on_device_changed(_pad: bool) -> void:
	_refresh_prompt()


func _process(delta: float) -> void:
	_clock.text = Game.clock_text()
	if player:
		var under := player.is_head_underwater()
		var target := 0.0
		if under:
			var depth := World.surface_at(player.global_position) - player.global_position.y
			target = clampf(0.45 + depth * 0.08, 0.0, 0.85)
		var cur: float = _vignette_mat.get_shader_parameter("strength")
		_vignette_mat.set_shader_parameter("strength", lerpf(cur, target, 1.0 - exp(-4.0 * delta)))
		if _prompt_panel.visible and player.focus:
			_refresh_prompt_soft()
	_flash.color.a = maxf(_flash.color.a - delta * 1.5, 0.0)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

func _build_overlays() -> void:
	_vignette = ColorRect.new()
	_vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = """
shader_type canvas_item;
uniform float strength = 0.0;
void fragment() {
	vec2 uv = UV - 0.5;
	float v = smoothstep(0.25, 0.85, length(uv * vec2(1.25, 1.0)));
	float caustic = sin(UV.x * 38.0 + TIME * 1.3) * sin(UV.y * 31.0 - TIME * 1.1) * 0.5 + 0.5;
	vec3 deep = vec3(0.02, 0.22, 0.38);
	COLOR = vec4(mix(deep, vec3(0.2, 0.6, 0.7), caustic * 0.15), strength * (0.18 + v * 0.75));
}"""
	_vignette_mat = ShaderMaterial.new()
	_vignette_mat.shader = sh
	_vignette_mat.set_shader_parameter("strength", 0.0)
	_vignette.material = _vignette_mat
	_root.add_child(_vignette)
	_flash = ColorRect.new()
	_flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_flash.color = Color(0.85, 0.15, 0.1, 0.0)
	_root.add_child(_flash)


func _build_stats() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	panel.position = Vector2(28, -28)
	panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	panel.offset_left = 28
	panel.offset_bottom = -28
	panel.offset_top = -28
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := UITheme.panel_box(16)
	sb.set_content_margin_all(14)
	panel.add_theme_stylebox_override("panel", sb)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 8)
	panel.add_child(col)
	for stat in ["oxygen", "health", "hunger", "thirst", "stamina"]:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		var icon := TextureRect.new()
		icon.texture = load("res://assets/ui/stat_%s.png" % stat)
		icon.custom_minimum_size = Vector2(26, 26)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.modulate = UITheme.STAT_COLORS[stat]
		row.add_child(icon)
		var bar := ProgressBar.new()
		bar.custom_minimum_size = Vector2(230, 16)
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bar.show_percentage = false
		bar.max_value = 100.0
		var bg := StyleBoxFlat.new()
		bg.bg_color = Color(0, 0, 0, 0.35)
		bg.set_corner_radius_all(8)
		var fill := StyleBoxFlat.new()
		fill.bg_color = UITheme.STAT_COLORS[stat]
		fill.set_corner_radius_all(8)
		bar.add_theme_stylebox_override("background", bg)
		bar.add_theme_stylebox_override("fill", fill)
		row.add_child(bar)
		col.add_child(row)
		_bars[stat] = bar
		if stat == "oxygen":
			_oxygen_row = row
	_root.add_child(panel)


func _build_hotbar() -> void:
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 10)
	bar.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	bar.grow_horizontal = Control.GROW_DIRECTION_BOTH
	bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	bar.offset_bottom = -26
	bar.offset_top = -26 - 84
	for i in Game.HOTBAR_SIZE:
		var slot := ItemSlot.new(84)
		slot.focus_mode = Control.FOCUS_NONE
		slot.bind(Game.inventory, i, str(i + 1))
		slot.slot_pressed.connect(func(s: ItemSlot) -> void: Game.select(s.index))
		bar.add_child(slot)
		_hotbar.append(slot)
	_root.add_child(bar)
	var name_label := UITheme.label("", 20, UITheme.INK_DIM)
	name_label.name = "SelectedName"
	name_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	name_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	name_label.offset_top = -26 - 84 - 34
	name_label.offset_bottom = -26 - 84 - 6
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_root.add_child(name_label)


func _build_prompt() -> void:
	_prompt_panel = PanelContainer.new()
	var sb := UITheme.panel_box(14)
	sb.set_content_margin_all(12)
	sb.content_margin_left = 16
	sb.content_margin_right = 18
	_prompt_panel.add_theme_stylebox_override("panel", sb)
	_prompt_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_prompt_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_prompt_panel.offset_bottom = -26 - 84 - 46
	_prompt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt_box = VBoxContainer.new()
	_prompt_box.add_theme_constant_override("separation", 8)
	_prompt_panel.add_child(_prompt_box)
	_prompt_panel.visible = false
	_root.add_child(_prompt_panel)


func _build_feed() -> void:
	_feed = VBoxContainer.new()
	_feed.set_anchors_and_offsets_preset(Control.PRESET_CENTER_RIGHT)
	_feed.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_feed.offset_right = -28
	_feed.offset_top = -40
	_feed.alignment = BoxContainer.ALIGNMENT_END
	_feed.add_theme_constant_override("separation", 8)
	_feed.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_feed)


func _build_objective() -> void:
	var panel := PanelContainer.new()
	panel.position = Vector2(28, 28)
	panel.custom_minimum_size = Vector2(420, 0)
	var sb := UITheme.panel_box(16)
	sb.set_content_margin_all(16)
	panel.add_theme_stylebox_override("panel", sb)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	var head := HBoxContainer.new()
	_objective_title = UITheme.label("OBJECTIVE", 15, UITheme.ACCENT, true)
	_objective_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(_objective_title)
	_objective_count = UITheme.label("", 16, UITheme.SAND, true)
	head.add_child(_objective_count)
	col.add_child(head)
	_objective_text = UITheme.label("", 21)
	_objective_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_objective_text.custom_minimum_size = Vector2(388, 0)
	col.add_child(_objective_text)
	panel.add_child(col)
	_root.add_child(panel)


func _build_clock() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	panel.offset_right = -28
	panel.offset_top = 28
	var sb := UITheme.panel_box(14)
	sb.set_content_margin_all(12)
	sb.content_margin_left = 18
	sb.content_margin_right = 18
	panel.add_theme_stylebox_override("panel", sb)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_clock = UITheme.label("Day 1  07:30", 22, UITheme.INK, true)
	panel.add_child(_clock)
	_root.add_child(panel)


func _build_busy() -> void:
	_busy_panel = PanelContainer.new()
	_busy_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_busy_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_busy_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_busy_panel.offset_top = 120
	_busy_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	_busy_label = UITheme.label("", 22)
	_busy_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(_busy_label)
	_busy_bar = _meter(UITheme.SAND, Vector2(280, 14))
	col.add_child(_busy_bar)
	_busy_panel.add_child(col)
	_busy_panel.visible = false
	_root.add_child(_busy_panel)


func _build_fishing() -> void:
	_fish_panel = PanelContainer.new()
	_fish_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER_RIGHT)
	_fish_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_fish_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_fish_panel.offset_right = -340
	_fish_panel.offset_top = 40
	_fish_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	col.add_child(UITheme.label("LINE TENSION", 14, UITheme.INK_DIM, true))
	_fish_tension = _meter(UITheme.CORAL, Vector2(300, 18))
	col.add_child(_fish_tension)
	col.add_child(UITheme.label("REEL", 14, UITheme.INK_DIM, true))
	_fish_progress = _meter(UITheme.ACCENT, Vector2(300, 18))
	col.add_child(_fish_progress)
	_fish_hint = UITheme.label("", 18, UITheme.INK)
	_fish_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_fish_hint.custom_minimum_size = Vector2(300, 0)
	col.add_child(_fish_hint)
	_fish_panel.add_child(col)
	_fish_panel.visible = false
	_root.add_child(_fish_panel)
	_bite_label = UITheme.label("!", 96, UITheme.SAND, true)
	_bite_label.add_theme_constant_override("outline_size", 16)
	_bite_label.add_theme_color_override("font_outline_color", Color(0.05, 0.1, 0.15))
	_bite_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_bite_label.offset_top = -260
	_bite_label.offset_left = -20
	_bite_label.visible = false
	_root.add_child(_bite_label)


func _build_placement() -> void:
	_place_panel = PanelContainer.new()
	_place_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	_place_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_place_panel.offset_top = 120
	_place_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_place_label = UITheme.label("", 22)
	_place_panel.add_child(_place_label)
	_place_panel.visible = false
	_root.add_child(_place_panel)


func _meter(color: Color, min_size: Vector2) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.custom_minimum_size = min_size
	bar.show_percentage = false
	bar.max_value = 1.0
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0, 0, 0, 0.4)
	bg.set_corner_radius_all(9)
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	fill.set_corner_radius_all(9)
	bar.add_theme_stylebox_override("background", bg)
	bar.add_theme_stylebox_override("fill", fill)
	return bar


# ---------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------

func _on_stats() -> void:
	for stat in _bars:
		(_bars[stat] as ProgressBar).value = Game.stats.get(stat, 0.0) / Game.max_stats[stat] * 100.0
	var under := player != null and player.is_head_underwater()
	_oxygen_row.visible = under or Game.stats.get("oxygen", 100.0) < 99.5
	var h: float = Game.stats.get("health", 100.0)
	if h < _last_health - 0.5:
		_flash.color.a = clampf(_flash.color.a + (_last_health - h) * 0.03, 0.0, 0.45)
	_last_health = h
	for stat in ["hunger", "thirst"]:
		var low: bool = Game.stats.get(stat, 100.0) < 20.0
		(_bars[stat] as ProgressBar).modulate = Color(1, 1, 1, 0.55 + 0.45 * absf(sin(Time.get_ticks_msec() * 0.006))) if low else Color.WHITE


func _refresh_hotbar() -> void:
	for slot in _hotbar:
		slot.highlight = slot.index == Game.selected
		slot.refresh()
	var id := Game.selected_item()
	var label := _root.get_node("SelectedName") as Label
	label.text = ItemDB.display_name(id) if id != "" else ""


func _refresh_prompt() -> void:
	for c in _prompt_box.get_children():
		c.queue_free()
	if player == null or player.focus == null:
		_prompt_panel.visible = false
		return
	var acts := player.focus.actions(player)
	if acts.is_empty():
		_prompt_panel.visible = false
		return
	for a in acts:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		var action: String = a.get("action", "")
		if action != "":
			row.add_child(UITheme.keycap(InputBindings.glyph(action)))
		row.add_child(UITheme.label(a.get("text", ""), 22, UITheme.INK if action != "" else UITheme.INK_DIM))
		_prompt_box.add_child(row)
	_prompt_panel.visible = true
	_prompt_panel.set_meta("sig", _sig(acts))


func _refresh_prompt_soft() -> void:
	var acts := player.focus.actions(player)
	if _sig(acts) != String(_prompt_panel.get_meta("sig", "")):
		_refresh_prompt()


static func _sig(acts: Array) -> String:
	var parts := []
	for a in acts:
		parts.append(String(a.get("action", "")) + ":" + String(a.get("text", "")))
	return "|".join(parts)


func _on_notified(text: String, item_id: String) -> void:
	var panel := PanelContainer.new()
	var sb := UITheme.panel_box(12)
	sb.set_content_margin_all(10)
	sb.content_margin_left = 12
	sb.content_margin_right = 16
	panel.add_theme_stylebox_override("panel", sb)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	if item_id != "":
		var icon := TextureRect.new()
		icon.texture = ItemDB.icon(item_id)
		icon.custom_minimum_size = Vector2(40, 40)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(icon)
	var l := UITheme.label(text, 21)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(minf(text.length() * 11.0, 420.0), 0)
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(l)
	panel.add_child(row)
	_feed.add_child(panel)
	while _feed.get_child_count() > 5:
		_feed.get_child(0).queue_free()
		_feed.remove_child(_feed.get_child(0))
	var tw := panel.create_tween()
	panel.modulate.a = 0.0
	tw.tween_property(panel, "modulate:a", 1.0, 0.2)
	tw.tween_interval(3.6)
	tw.tween_property(panel, "modulate:a", 0.0, 0.6)
	tw.tween_callback(panel.queue_free)


func _refresh_objective() -> void:
	var obj := Game.current_objective()
	if obj.is_empty():
		_objective_title.text = "FREE PLAY"
		_objective_text.text = "Explore the islands, fish, build and survive."
		_objective_count.text = ""
		return
	_objective_title.text = "OBJECTIVE %d / %d" % [Game.objective_index + 1, Game.OBJECTIVES.size()]
	_objective_text.text = obj["text"]
	var n := int(obj["count"])
	_objective_count.text = "%d / %d" % [mini(Game.objective_progress, n), n] if n > 1 else ""


func _on_busy(label: String, progress: float) -> void:
	_busy_panel.visible = label != ""
	_busy_label.text = label
	_busy_bar.value = progress


func _on_fishing_state(state: int) -> void:
	var S := FishingRod.S
	_fish_panel.visible = state == S.REEL
	_bite_label.visible = state == S.BITE
	if state == S.BITE:
		var tw := _bite_label.create_tween().set_loops(3)
		tw.tween_property(_bite_label, "scale", Vector2(1.3, 1.3), 0.12)
		tw.tween_property(_bite_label, "scale", Vector2.ONE, 0.12)
	var hint := ""
	match state:
		S.CHARGE:
			hint = "Release to cast"
		S.WAIT:
			hint = "Wait for a bite..."
		S.BITE:
			hint = "Bite! Press %s" % InputBindings.glyph("use_tool")
		S.REEL:
			hint = "Hold %s to reel. Let go when the tension runs high." % InputBindings.glyph("use_tool")
	_fish_hint.text = hint
	if state == S.CHARGE or state == S.WAIT:
		_on_busy("", 0.0)


func _on_reel(tension: float, progress: float) -> void:
	_fish_tension.value = tension
	_fish_progress.value = progress
	var fill := _fish_tension.get_theme_stylebox("fill") as StyleBoxFlat
	fill.bg_color = UITheme.CORAL if tension > 0.75 else UITheme.SAND


func _on_placement(active: bool, valid: bool, item_id: String) -> void:
	_place_panel.visible = active
	if active:
		_place_label.text = "%s: %s place   %s rotate   %s cancel" % [ItemDB.display_name(item_id),
				InputBindings.glyph("use_tool"), InputBindings.glyph("rotate_build"), InputBindings.glyph("cancel")]
		_place_label.add_theme_color_override("font_color", UITheme.GOOD if valid else UITheme.CORAL)


func set_visible_hud(v: bool) -> void:
	_root.visible = v


func set_objectives_visible(v: bool) -> void:
	_objective_text.get_parent().get_parent().visible = v
