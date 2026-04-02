# GlitchPhysicsModifier.gd
# Physics overlay modifier for player movement glitches
# Applies temporary multipliers to player physics properties
# Does NOT modify PlayerDefaults - applies overlays at runtime

extends Node
class_name GlitchPhysicsModifier

# ---- Modifier State ----
var speed_multiplier: float = 1.0
var gravity_multiplier: float = 1.0
var jump_force_multiplier: float = 1.0
var friction_multiplier: float = 1.0
var wall_slide_speed_multiplier: float = 1.0

# ---- Active Glitch Tracking ----
var active_glitch_id: String = ""
var active_property: String = ""

# ---- Reference to PlayerController ----
var player_controller: Node = null

func _ready() -> void:
	print("[GlitchPhysicsModifier] Initialized")

# ---- Apply Modifiers ----
func apply_speed_modifier(glitch_id: String, mult: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchPhysicsModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "speed"
	speed_multiplier = mult
	print("[GlitchPhysicsModifier] Applied speed modifier: %.2f for %s" % [mult, glitch_id])

func apply_gravity_modifier(glitch_id: String, mult: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchPhysicsModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "gravity"
	gravity_multiplier = mult
	print("[GlitchPhysicsModifier] Applied gravity modifier: %.2f for %s" % [mult, glitch_id])

func apply_jump_force_modifier(glitch_id: String, mult: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchPhysicsModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "jump_force"
	jump_force_multiplier = mult
	print("[GlitchPhysicsModifier] Applied jump force modifier: %.2f for %s" % [mult, glitch_id])

func apply_friction_modifier(glitch_id: String, mult: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchPhysicsModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "friction"
	friction_multiplier = mult
	print("[GlitchPhysicsModifier] Applied friction modifier: %.2f for %s" % [mult, glitch_id])

func apply_wall_slide_modifier(glitch_id: String, mult: float) -> void:
	if active_glitch_id != "" and active_glitch_id != glitch_id:
		print("[GlitchPhysicsModifier] Rejecting %s - %s already active" % [glitch_id, active_glitch_id])
		return
	
	active_glitch_id = glitch_id
	active_property = "wall_slide_speed"
	wall_slide_speed_multiplier = mult
	print("[GlitchPhysicsModifier] Applied wall slide modifier: %.2f for %s" % [mult, glitch_id])

# ---- Clear Modifier ----
func clear_modifier(glitch_id: String) -> void:
	if glitch_id != active_glitch_id:
		return
	
	match active_property:
		"speed":
			speed_multiplier = 1.0
		"gravity":
			gravity_multiplier = 1.0
		"jump_force":
			jump_force_multiplier = 1.0
		"friction":
			friction_multiplier = 1.0
		"wall_slide_speed":
			wall_slide_speed_multiplier = 1.0
	
	print("[GlitchPhysicsModifier] Cleared modifier for %s" % glitch_id)
	active_glitch_id = ""
	active_property = ""

# ---- Get Effective Values ----
func get_effective_speed(base_speed: float) -> float:
	return base_speed * speed_multiplier

func get_effective_gravity(base_gravity: float) -> float:
	return base_gravity * gravity_multiplier

func get_effective_jump_force(base_jump_force: float) -> float:
	return base_jump_force * jump_force_multiplier

func get_effective_friction(base_friction: float) -> float:
	return base_friction * friction_multiplier

func get_effective_wall_slide_speed(base_wall_slide_speed: float) -> float:
	return base_wall_slide_speed * wall_slide_speed_multiplier

# ---- Query Methods ----
func has_active_modifier() -> bool:
	return active_glitch_id != ""

func get_current_glitch_id() -> String:
	return active_glitch_id
