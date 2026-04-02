# GlitchHazardModifier.gd
# Hazard behavior overlay modifier
# Applies temporary modifications to existing hazard behavior
# Does NOT spawn new collision geometry - only modifies existing hazard behavior

extends Node
class_name GlitchHazardModifier

# ---- Modifier State ----
var position_shift: Vector2 = Vector2.ZERO
var movement_speed_modifier: float = 1.0
var timing_offset: float = 0.0
var type_swap_active: bool = false

# ---- Active Glitch Tracking ----
var active_glitch_id: String = ""
var active_property: String = ""

func _ready() -> void:
	print("[GlitchHazardModifier] Initialized")

# ---- Apply Modifiers ----
func apply_position_shift(glitch_id: String, shift: Vector2) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchHazardModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "position"
	position_shift = shift
	print("[GlitchHazardModifier] Applied position shift: %s for %s" % [shift, glitch_id])

func apply_movement_speed(glitch_id: String, mult: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchHazardModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "movement_speed"
	movement_speed_modifier = mult
	print("[GlitchHazardModifier] Applied movement speed modifier: %.2f for %s" % [mult, glitch_id])

func apply_timing_offset(glitch_id: String, offset: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchHazardModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "timing"
	timing_offset = offset
	print("[GlitchHazardModifier] Applied timing offset: %.2f for %s" % [offset, glitch_id])

func apply_type_swap(glitch_id: String, active: bool) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchHazardModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "type_swap"
	type_swap_active = active
	print("[GlitchHazardModifier] Applied type swap: %s for %s" % [active, glitch_id])

# ---- Clear Modifier ----
func clear_modifier(glitch_id: String) -> void:
	if glitch_id != active_glitch_id:
		return
	
	match active_property:
		"position":
			position_shift = Vector2.ZERO
		"movement_speed":
			movement_speed_modifier = 1.0
		"timing":
			timing_offset = 0.0
		"type_swap":
			type_swap_active = false
	
	print("[GlitchHazardModifier] Cleared modifier for %s" % glitch_id)
	active_glitch_id = ""
	active_property = ""

# ---- Query Methods ----
func has_active_modifier() -> bool:
	return active_glitch_id != ""

func get_current_glitch_id() -> String:
	return active_glitch_id

func get_position_shift() -> Vector2:
	return position_shift

func get_movement_speed_modifier() -> float:
	return movement_speed_modifier

func get_timing_offset() -> float:
	return timing_offset
