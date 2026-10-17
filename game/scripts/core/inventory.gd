class_name Inventory
extends RefCounted
## A fixed number of slots. Each slot is null or {"id", "count", "dur"}.
## Tools never stack and carry durability ("dur"); everything else stacks
## up to ItemDB.max_stack().

signal changed

var slots: Array = []


func _init(size: int = 24) -> void:
	slots.resize(size)


func size() -> int:
	return slots.size()


func get_slot(i: int):
	return slots[i] if i >= 0 and i < slots.size() else null


## Adds items and returns how many did not fit.
func add(id: String, count: int = 1, dur: float = -1.0) -> int:
	if count <= 0 or not ItemDB.has(id):
		return count
	var stack := ItemDB.max_stack(id)
	var left := count
	if stack > 1:
		for s in slots:
			if left == 0:
				break
			if s != null and s["id"] == id and s["count"] < stack:
				var n := mini(stack - int(s["count"]), left)
				s["count"] += n
				left -= n
	for i in slots.size():
		if left == 0:
			break
		if slots[i] == null:
			var n := mini(stack, left)
			var entry := {"id": id, "count": n}
			if ItemDB.kind(id) == "tool":
				entry["dur"] = dur if dur >= 0.0 else ItemDB.max_durability(id)
			slots[i] = entry
			left -= n
	if left != count:
		changed.emit()
	return left


func count(id: String) -> int:
	var total := 0
	for s in slots:
		if s != null and s["id"] == id:
			total += int(s["count"])
	return total


func has_items(req: Dictionary) -> bool:
	for id in req:
		if count(id) < int(req[id]):
			return false
	return true


## Removes `count` of `id`, taking from the last stacks first. All or nothing.
func remove(id: String, n: int = 1) -> bool:
	if count(id) < n:
		return false
	var left := n
	for i in range(slots.size() - 1, -1, -1):
		var s = slots[i]
		if s == null or s["id"] != id:
			continue
		var take := mini(int(s["count"]), left)
		s["count"] -= take
		left -= take
		if s["count"] <= 0:
			slots[i] = null
		if left == 0:
			break
	changed.emit()
	return true


func remove_items(req: Dictionary) -> bool:
	if not has_items(req):
		return false
	for id in req:
		remove(id, int(req[id]))
	return true


## Removes `n` from a specific slot.
func take_from_slot(i: int, n: int = 1) -> void:
	var s = get_slot(i)
	if s == null:
		return
	s["count"] -= n
	if s["count"] <= 0:
		slots[i] = null
	changed.emit()


func swap(a: int, b: int) -> void:
	if a == b:
		return
	var sa = slots[a]
	var sb = slots[b]
	# Merge equal stackable items instead of swapping.
	if sa != null and sb != null and sa["id"] == sb["id"] and ItemDB.max_stack(sa["id"]) > 1:
		var room := ItemDB.max_stack(sb["id"]) - int(sb["count"])
		var n := mini(room, int(sa["count"]))
		sb["count"] += n
		sa["count"] -= n
		if sa["count"] <= 0:
			slots[a] = null
	else:
		slots[a] = sb
		slots[b] = sa
	changed.emit()


## Moves the whole stack in slot `i` into `other`; keeps what does not fit.
func transfer_slot(i: int, other: Inventory) -> void:
	var s = get_slot(i)
	if s == null:
		return
	var left := other.add(s["id"], int(s["count"]), float(s.get("dur", -1.0)))
	if left == 0:
		slots[i] = null
	else:
		s["count"] = left
	changed.emit()


## Wears a tool in slot `i`; returns true if it broke.
func wear(i: int, amount: float) -> bool:
	var s = get_slot(i)
	if s == null or not s.has("dur"):
		return false
	s["dur"] = float(s["dur"]) - amount
	if s["dur"] <= 0.0:
		slots[i] = null
		changed.emit()
		return true
	changed.emit()
	return false


func clear() -> void:
	for i in slots.size():
		slots[i] = null
	changed.emit()


func to_data() -> Array:
	var out := []
	for s in slots:
		out.append(s.duplicate() if s != null else null)
	return out


func from_data(data: Array) -> void:
	for i in slots.size():
		var s = data[i] if i < data.size() else null
		if s is Dictionary and ItemDB.has(String(s.get("id", ""))):
			var entry := {"id": String(s["id"]), "count": int(s.get("count", 1))}
			if s.has("dur"):
				entry["dur"] = float(s["dur"])
			slots[i] = entry
		else:
			slots[i] = null
	changed.emit()
