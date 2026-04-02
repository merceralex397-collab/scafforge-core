# GlitchRoomModifier.gd
# Room logic overlay modifier
# Applies temporary modifications to room-level rules
# Does NOT trap player permanently - preserves checkpoint access

extends Node
class_name GlitchRoomModifier

# ---- Modifier State ----
var checkpoint_displacement: Vector2 = Vector2.ZERO
var platform_speed_multiplier: float = 1.0
var wall_softness_modifier: float = 0.0
var portal_swap_active: bool = false

# ---- Active Glitch Tracking ----
var active_glitch_id: String = ""
var active_property: String = ""

# ---- Checkpoint Preservation ----
const FORCED_CHECKPOINT_PRESERVE: bool = true
var _original_checkpoint_position: Vector2 = Vector2.ZERO

func _ready() -> void:
	print("[GlitchRoomModifier] Initialized")

# ---- Apply Modifiers ----
func apply_checkpoint_displacement(glitch_id: String, displacement: Vector2, original_pos: Vector2) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchRoomModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "checkpoint"
	checkpoint_displacement = displacement
	_original_checkpoint_position = original_pos
	print("[GlitchRoomModifier] Applied checkpoint displacement: %s for %s" % [displacement, glitch_id])

func apply_platform_speed(glitch_id: String, mult: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchRoomModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "platform_speed"
	platform_speed_multiplier = mult
	print("[GlitchRoomModifier] Applied platform speed modifier: %.2f for %s" % [mult, glitch_id])

func apply_wall_softness(glitch_id: String, softness: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchRoomModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "wall_softness"
	wall_softness_modifier = softness
	print("[GlitchRoomModifier] Applied wall softness modifier: %.2f for %s" % [softness, glitch_id])

func apply_portal_swap(glitch_id: String, active: bool) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchRoomModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "portal_swap"
	portal_swap_active = active
	print("[GlitchRoomModifier] Applied portal swap: %s for %s" % [active, glitch_id])

# ---- Clear Modifier ----
func clear_modifier(glitch_id: String) -> void:
	if glitch_id != active_glitch_id:
		return
	
	match active_property:
		"checkpoint":
			checkpoint_displacement = Vector2.ZERO
		"platform_speed":
			platform_speed_multiplier = 1.0
		"wall_softness":
			wall_softness_modifier = 0.0
		"portal_swap":
			portal_swap_active = false
	
	print("[GlitchRoomModifier] Cleared modifier for %s" % glitch_id)
	active_glitch_id = ""
	active_property = ""

# ---- Query Methods ----
func has_active_modifier() -> bool:
	return active_glitch_id != ""

func get_current_glitch_id() -> String:
	return active_glitch_id

func get_checkpoint_displacement() -> Vector2:
	return checkpoint_displacement

func get_platform_speed_multiplier() -> float:
	return platform_speed_multiplier

func preserves_checkpoint() -> bool:
	return FORCED_CHECKPOINT_PRESERVE
