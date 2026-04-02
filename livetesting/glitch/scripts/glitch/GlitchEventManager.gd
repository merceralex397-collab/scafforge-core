# GlitchEventManager.gd
# Orchestrates the glitch event lifecycle
# Manages telegraph phase, applies modifiers, and coordinates with GlitchState

extends Node

# ---- Signals ----
signal glitch_telegraph_started(glitch_event: GlitchEvent)
signal glitch_telegraph_ended(glitch_event: GlitchEvent)
signal glitch_event_started(glitch_event: GlitchEvent)
signal glitch_event_ended(glitch_event: GlitchEvent)

# ---- Node References ----
@onready var physics_modifier: GlitchPhysicsModifier = $PhysicsModifier
@onready var hazard_modifier: GlitchHazardModifier = $HazardModifier
@onready var room_modifier: GlitchRoomModifier = $RoomModifier

# ---- State ----
var active_telegraph_timers: Dictionary = {}
var active_glitch_timers: Dictionary = {}
var current_room_config: RoomGlitchConfig = null
var glitch_registry: Dictionary = {}

# ---- Constants ----
const WARNING_PULSE_RATE: float = 4.0
const WARNING_INTENSITY_FULL: float = 1.0
const WARNING_INTENSITY_REDUCED: float = 0.4

func _ready() -> void:
	# Initialize modifiers
	print("[GlitchEventManager] Initialized")
	
	# Connect to GlitchState signals
	var glitch_state = get_node_or_null("/root/GlitchState")
	if glitch_state:
		glitch_state.connect("glitch_started", _on_glitch_started_from_state)
		glitch_state.connect("glitch_ended", _on_glitch_ended_from_state)
		print("[GlitchEventManager] Connected to GlitchState signals")
	else:
		push_warning("[GlitchEventManager] GlitchState not found - running standalone")

func _process(delta: float) -> void:
	pass

# ---- Public API ----

func set_room_config(config: RoomGlitchConfig) -> void:
	current_room_config = config
	print("[GlitchEventManager] Room config set: %s" % config.room_id)

func register_glitch_event(event: GlitchEvent) -> void:
	glitch_registry[event.event_id] = event
	print("[GlitchEventManager] Registered glitch event: %s" % event.event_id)

func trigger_glitch(event_id: String) -> bool:
	if not glitch_registry.has(event_id):
		push_warning("[GlitchEventManager] Unknown glitch event: %s" % event_id)
		return false
	
	var glitch_event: GlitchEvent = glitch_registry[event_id]
	
	# Check if already active via GlitchState
	var glitch_state = get_node_or_null("/root/GlitchState")
	if glitch_state and glitch_state.is_glitch_active(event_id):
		print("[GlitchEventManager] Glitch %s already active, skipping" % event_id)
		return false
	
	# Start telegraph phase
	_start_telegraph(glitch_event)
	return true

func trigger_random_glitch() -> bool:
	if not current_room_config:
		push_warning("[GlitchEventManager] No room config set")
		return false
	
	# Get all available event IDs
	var all_events = current_room_config.get_all_event_ids()
	if all_events.is_empty():
		return false
	
	# Pick random event
	var random_id = all_events[randi() % all_events.size()]
	return trigger_glitch(random_id)

# ---- Telegraph Phase ----
func _start_telegraph(event: GlitchEvent) -> void:
	print("[GlitchEventManager] Starting telegraph for: %s (%.1fs)" % [event.event_id, event.get_telegraph_time()])
	
	# Emit telegraph started signal
	emit_signal("glitch_telegraph_started", event)
	
	# Emit GlitchState warning signal so warning UI can display
	var glitch_state = get_node_or_null("/root/GlitchState")
	if glitch_state:
		glitch_state.emit_warning(event.event_id)
	
	# Create timer for telegraph duration
	var timer = get_tree().create_timer(event.get_telegraph_time())
	active_telegraph_timers[event.event_id] = timer
	timer.timeout.connect(_on_telegraph_complete.bind(event))

func _on_telegraph_complete(event: GlitchEvent) -> void:
	active_telegraph_timers.erase(event.event_id)
	
	print("[GlitchEventManager] Telegraph complete for: %s" % event.event_id)
	emit_signal("glitch_telegraph_ended", event)
	
	# Apply the glitch via GlitchState
	var glitch_state = get_node_or_null("/root/GlitchState")
	if glitch_state:
		glitch_state.apply_glitch(event.event_id)
	
	# Apply modifier based on category
	_apply_modifier(event)
	
	# Start glitch duration timer
	_start_glitch_duration(event)

# ---- Glitch Duration ----
func _start_glitch_duration(event: GlitchEvent) -> void:
	var timer = get_tree().create_timer(event.get_effective_duration())
	active_glitch_timers[event.event_id] = timer
	timer.timeout.connect(_on_glitch_duration_complete.bind(event))

func _on_glitch_duration_complete(event: GlitchEvent) -> void:
	active_glitch_timers.erase(event.event_id)
	
	print("[GlitchEventManager] Glitch duration complete for: %s" % event.event_id)
	
	# End glitch via GlitchState
	var glitch_state = get_node_or_null("/root/GlitchState")
	if glitch_state:
		glitch_state.end_glitch(event.event_id)
	
	# Clear modifier
	_clear_modifier(event)
	
	emit_signal("glitch_event_ended", event)

# ---- Modifier Application ----
func _apply_modifier(event: GlitchEvent) -> void:
	match event.category:
		GlitchEvent.Category.PHYSICS:
			_apply_physics_modifier(event)
		GlitchEvent.Category.HAZARD:
			_apply_hazard_modifier(event)
		GlitchEvent.Category.ROOM_LOGIC:
			_apply_room_logic_modifier(event)
	
	emit_signal("glitch_event_started", event)

func _apply_physics_modifier(event: GlitchEvent) -> void:
	var config = event.modifier_config
	
	match event.event_id:
		"speed_down":
			var mult = config.get("multiplier", 0.5)
			physics_modifier.apply_speed_modifier(event.event_id, mult)
		"speed_up":
			var mult = config.get("multiplier", 1.5)
			physics_modifier.apply_speed_modifier(event.event_id, mult)
		"gravity_flip":
			var mult = config.get("multiplier", -1.0)
			physics_modifier.apply_gravity_modifier(event.event_id, mult)
		"gravity_boost":
			var mult = config.get("multiplier", 1.5)
			physics_modifier.apply_gravity_modifier(event.event_id, mult)
		"jump_force_down":
			var mult = config.get("multiplier", 0.5)
			physics_modifier.apply_jump_force_modifier(event.event_id, mult)
		"jump_force_up":
			var mult = config.get("multiplier", 1.5)
			physics_modifier.apply_jump_force_modifier(event.event_id, mult)
		_:
			print("[GlitchEventManager] Unknown physics glitch: %s" % event.event_id)

func _apply_hazard_modifier(event: GlitchEvent) -> void:
	var config = event.modifier_config
	
	match event.event_id:
		"spike_shift":
			var shift = config.get("shift", Vector2(16, 0))
			hazard_modifier.apply_position_shift(event.event_id, shift)
		"platform_reverse":
			var mult = config.get("multiplier", -1.0)
			hazard_modifier.apply_movement_speed(event.event_id, mult)
		"timing_shift":
			var offset = config.get("offset", 0.5)
			hazard_modifier.apply_timing_offset(event.event_id, offset)
		_:
			print("[GlitchEventManager] Unknown hazard glitch: %s" % event.event_id)

func _apply_room_logic_modifier(event: GlitchEvent) -> void:
	var config = event.modifier_config
	
	match event.event_id:
		"checkpoint_drift":
			var displacement = config.get("displacement", Vector2(64, 0))
			var original_pos = config.get("original_position", Vector2.ZERO)
			room_modifier.apply_checkpoint_displacement(event.event_id, displacement, original_pos)
		"platform_speed_change":
			var mult = config.get("multiplier", 2.0)
			room_modifier.apply_platform_speed(event.event_id, mult)
		"wall_soft":
			var softness = config.get("softness", 0.5)
			room_modifier.apply_wall_softness(event.event_id, softness)
		"portal_swap":
			room_modifier.apply_portal_swap(event.event_id, true)
		_:
			print("[GlitchEventManager] Unknown room logic glitch: %s" % event.event_id)

func _clear_modifier(event: GlitchEvent) -> void:
	match event.category:
		GlitchEvent.Category.PHYSICS:
			physics_modifier.clear_modifier(event.event_id)
		GlitchEvent.Category.HAZARD:
			hazard_modifier.clear_modifier(event.event_id)
		GlitchEvent.Category.ROOM_LOGIC:
			room_modifier.clear_modifier(event.event_id)

# ---- GlitchState Signal Callbacks ----
func _on_glitch_started_from_state(event_id: String) -> void:
	print("[GlitchEventManager] GlitchState reported started: %s" % event_id)

func _on_glitch_ended_from_state(event_id: String) -> void:
	print("[GlitchEventManager] GlitchState reported ended: %s" % event_id)

# ---- Query Methods ----
func get_physics_modifier() -> GlitchPhysicsModifier:
	return physics_modifier

func get_hazard_modifier() -> GlitchHazardModifier:
	return hazard_modifier

func get_room_modifier() -> GlitchRoomModifier:
	return room_modifier

func is_telegraphing(event_id: String) -> bool:
	return active_telegraph_timers.has(event_id)

func is_glitch_active(event_id: String) -> bool:
	return active_glitch_timers.has(event_id)

func get_active_glitch_count() -> int:
	return active_glitch_timers.size()
