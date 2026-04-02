# GlitchEvent.gd
# Data-driven glitch event definition
# Defines categories, telegraph timing, duration, severity, and modifier configuration

extends Resource
class_name GlitchEvent

# ---- Enums ----
enum Category {
	PHYSICS,
	HAZARD,
	ROOM_LOGIC
}

enum ImpactLevel {
	LOW,
	HIGH
}

# ---- Constants ----
const TELEGRAPH_DURATION_DEFAULT: float = 1.5
const GLITCH_DURATION_DEFAULT: float = 4.0
const MAX_GLITCH_DURATION: float = 6.0
const HIGH_IMPACT_TELEGRAPH: float = 2.0
const LOW_IMPACT_TELEGRAPH: float = 1.0

# ---- Exported Properties ----
@export var event_id: String = ""
@export var display_name: String = ""
@export var description: String = ""
@export var category: Category = Category.PHYSICS
@export var impact_level: ImpactLevel = ImpactLevel.LOW
@export var telegraph_duration: float = TELEGRAPH_DURATION_DEFAULT
@export var duration: float = GLITCH_DURATION_DEFAULT
@export var modifier_config: Dictionary = {}

# ---- Computed Properties ----
func get_telegraph_time() -> float:
	# High impact events get longer telegraph
	if impact_level == ImpactLevel.HIGH:
		return max(telegraph_duration, HIGH_IMPACT_TELEGRAPH)
	return max(telegraph_duration, LOW_IMPACT_TELEGRAPH)

func get_effective_duration() -> float:
	return min(duration, MAX_GLITCH_DURATION)

func get_category_name() -> String:
	match category:
		Category.PHYSICS:
			return "PHYSICS"
		Category.HAZARD:
			return "HAZARD"
		Category.ROOM_LOGIC:
			return "ROOM_LOGIC"
	return "UNKNOWN"

func get_impact_name() -> String:
	match impact_level:
		ImpactLevel.LOW:
			return "LOW"
		ImpactLevel.HIGH:
			return "HIGH"
	return "UNKNOWN"

# ---- Validation ----
func is_valid() -> bool:
	return (
		event_id != "" and
		display_name != "" and
		category in Category.values() and
		impact_level in ImpactLevel.values() and
		telegraph_duration > 0 and
		duration > 0
	)
