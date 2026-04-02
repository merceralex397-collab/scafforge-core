# GlitchEventRegistry.gd
# Central registry for all glitch events
# Provides factory methods for creating standard glitch events

extends Node
class_name GlitchEventRegistry

# ---- Singleton Access ----
static func get_instance() -> GlitchEventRegistry:
	var node = Node.new()
	node.set_script(load("res://scripts/glitch/GlitchEventRegistry.gd"))
	return node

# ---- PHYSICS Events ----

static func create_speed_down_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "speed_down"
	event.display_name = "Lag Spike"
	event.description = "Network latency simulated. Movement speed reduced by 50%."
	event.category = GlitchEvent.Category.PHYSICS
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "speed",
		"multiplier": 0.5,
		"affected_systems": ["player"]
	}
	return event

static func create_speed_up_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "speed_up"
	event.display_name = "Time Acceleration"
	event.description = "Time flows faster. Movement speed increased by 50%."
	event.category = GlitchEvent.Category.PHYSICS
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "speed",
		"multiplier": 1.5,
		"affected_systems": ["player"]
	}
	return event

static func create_gravity_flip_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "gravity_flip"
	event.display_name = "Gravity Inversion"
	event.description = "Gravity is temporarily inverted. Jump to fall upward."
	event.category = GlitchEvent.Category.PHYSICS
	event.impact_level = GlitchEvent.ImpactLevel.HIGH
	event.telegraph_duration = 2.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "gravity",
		"multiplier": -1.0,
		"affected_systems": ["player"]
	}
	return event

static func create_gravity_boost_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "gravity_boost"
	event.display_name = "Heavy Core"
	event.description = "Gravity intensifies. Fall speed increased by 50%."
	event.category = GlitchEvent.Category.PHYSICS
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "gravity",
		"multiplier": 1.5,
		"affected_systems": ["player"]
	}
	return event

static func create_jump_force_down_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "jump_force_down"
	event.display_name = "Weak Legs"
	event.description = "Jump force reduced by 50%. Harder to clear gaps."
	event.category = GlitchEvent.Category.PHYSICS
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "jump_force",
		"multiplier": 0.5,
		"affected_systems": ["player"]
	}
	return event

# ---- HAZARD Events ----

static func create_spike_shift_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "spike_shift"
	event.display_name = "Spike Drift"
	event.description = "Spike positions shift slightly. Stay on your feet."
	event.category = GlitchEvent.Category.HAZARD
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "position",
		"shift": Vector2(16, 0),
		"affected_systems": ["hazards"]
	}
	return event

static func create_platform_reverse_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "platform_reverse"
	event.display_name = "Platform Reversal"
	event.description = "Moving platforms reverse direction."
	event.category = GlitchEvent.Category.HAZARD
	event.impact_level = GlitchEvent.ImpactLevel.MEDIUM
	event.telegraph_duration = 1.5
	event.duration = 4.0
	event.modifier_config = {
		"property": "movement_speed",
		"multiplier": -1.0,
		"affected_systems": ["hazards"]
	}
	return event

static func create_timing_shift_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "timing_shift"
	event.display_name = "Timing Desync"
	event.description = "Hazard timing is offset. React faster."
	event.category = GlitchEvent.Category.HAZARD
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "timing",
		"offset": 0.5,
		"affected_systems": ["hazards"]
	}
	return event

# ---- ROOM_LOGIC Events ----

static func create_checkpoint_drift_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "checkpoint_drift"
	event.display_name = "Checkpoint Drift"
	event.description = "Checkpoint position shifts slightly. Progress is preserved."
	event.category = GlitchEvent.Category.ROOM_LOGIC
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "checkpoint",
		"displacement": Vector2(64, 0),
		"preserve_original": true,
		"affected_systems": ["checkpoints"]
	}
	return event

static func create_platform_speed_change_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "platform_speed_change"
	event.display_name = "Platform Surge"
	event.description = "Platform movement speed doubles."
	event.category = GlitchEvent.Category.ROOM_LOGIC
	event.impact_level = GlitchEvent.ImpactLevel.MEDIUM
	event.telegraph_duration = 1.5
	event.duration = 4.0
	event.modifier_config = {
		"property": "platform_speed",
		"multiplier": 2.0,
		"affected_systems": ["platforms"]
	}
	return event

static func create_wall_soft_event() -> GlitchEvent:
	var event := GlitchEvent.new()
	event.event_id = "wall_soft"
	event.display_name = "Wall Decay"
	event.description = "Walls become temporarily soft. Wall jumping is harder."
	event.category = GlitchEvent.Category.ROOM_LOGIC
	event.impact_level = GlitchEvent.ImpactLevel.LOW
	event.telegraph_duration = 1.0
	event.duration = 4.0
	event.modifier_config = {
		"property": "wall_softness",
		"softness": 0.5,
		"affected_systems": ["walls"]
	}
	return event

# ---- Registry Builder ----
static func build_startup_sector_events() -> Dictionary:
	var registry: Dictionary = {}
	
	# PHYSICS
	registry["speed_down"] = create_speed_down_event()
	registry["speed_up"] = create_speed_up_event()
	registry["gravity_flip"] = create_gravity_flip_event()
	registry["gravity_boost"] = create_gravity_boost_event()
	registry["jump_force_down"] = create_jump_force_down_event()
	
	# HAZARD
	registry["spike_shift"] = create_spike_shift_event()
	registry["platform_reverse"] = create_platform_reverse_event()
	registry["timing_shift"] = create_timing_shift_event()
	
	# ROOM_LOGIC
	registry["checkpoint_drift"] = create_checkpoint_drift_event()
	registry["platform_speed_change"] = create_platform_speed_change_event()
	registry["wall_soft"] = create_wall_soft_event()
	
	return registry
