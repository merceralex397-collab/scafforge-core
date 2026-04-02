extends Node

# GlitchState - Autoload singleton for glitch event state and corruption level
# Signal contract:
#   - glitch_warning(event_id: String)       # Emitted during telegraph phase
#   - glitch_started(event_id: String)        # Emitted when glitch effect begins
#   - glitch_ended(event_id: String)         # Emitted when glitch effect ends
#   - corruption_level_changed(level: int)    # Emitted when corruption changes

signal glitch_warning(event_id: String)
signal glitch_started(event_id: String)
signal glitch_ended(event_id: String)
signal corruption_level_changed(level: int)

var corruption_level: int = 0
var active_glitches: Array = []
var glitch_cooldowns: Dictionary = {}

func _ready() -> void:
	print("[GlitchState] Initialized - Corruption level: %d" % corruption_level)

func apply_glitch(event_id: String) -> void:
	if event_id in active_glitches:
		return
	active_glitches.append(event_id)
	emit_signal("glitch_started", event_id)
	print("[GlitchState] Glitch started: %s" % event_id)

func end_glitch(event_id: String) -> void:
	if event_id in active_glitches:
		active_glitches.erase(event_id)
		emit_signal("glitch_ended", event_id)
		print("[GlitchState] Glitch ended: %s" % event_id)

func emit_warning(event_id: String) -> void:
	emit_signal("glitch_warning", event_id)
	print("[GlitchState] Glitch warning: %s" % event_id)

func set_corruption(level: int) -> void:
	corruption_level = clamp(level, 0, 100)
	emit_signal("corruption_level_changed", corruption_level)
	print("[GlitchState] Corruption level changed to: %d" % corruption_level)

func is_glitch_active(event_id: String) -> bool:
	return event_id in active_glitches
