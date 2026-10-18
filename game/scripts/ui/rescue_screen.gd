class_name RescueScreen
extends MenuBase
## The ending: a ship sees the signal fire. Shows a few stats and lets the
## player keep exploring or return to the title.

var _stats: Label


func _ready() -> void:
	super._ready()
	var col := _build_frame(Vector2(820, 0), 0.6)
	col.add_child(MenuBase.header("Rescued!", "A sail turns toward the smoke on Lookout Isle."))
	_stats = UITheme.label("", 21, UITheme.INK)
	_stats.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_stats.custom_minimum_size = Vector2(740, 0)
	col.add_child(_stats)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	row.add_child(MenuBase.button("Keep exploring", close))
	row.add_child(MenuBase.button("Save and return to title", func() -> void:
		SaveManager.save_game()
		close()
		Game.pending_start = ""
		Game.set_state("menu")
		get_tree().reload_current_scene()))
	col.add_child(row)
	Game.rescued.connect(_on_rescued)


func _on_rescued() -> void:
	var fish := int(Game.counters.get("catch", 0))
	var built := Game.structures.size()
	_stats.text = "You survived %d day%s on the islands, caught %d fish and built %d structure%s.\nThe ship will wait while you finish exploring." % [
		Game.day, "" if Game.day == 1 else "s", fish, built, "" if built == 1 else "s"]
	open()


func _on_open() -> void:
	(panel.get_child(0).get_child(-1).get_child(0) as Button).grab_focus.call_deferred()
