# RoomGlitchConfig.gd
# Per-room curated glitch pool configuration
# Defines which glitch events can fire in a given room

extends Resource
class_name RoomGlitchConfig

# ---- Constants ----
const DEFAULT_MAX_CONCURRENT: int = 2
const DEFAULT_MIN_INTERVAL: float = 8.0

# ---- Enums ----
enum GlitchCategory {
	PHYSICS,
	HAZARD,
	ROOM_LOGIC
}

# ---- Exported Properties ----
@export var room_id: String = ""
@export var room_display_name: String = ""
@export var allowed_categories: Array[GlitchCategory] = []
@export var physics_glitch_pool: Array[String] = []
@export var hazard_glitch_pool: Array[String] = []
@export var room_logic_glitch_pool: Array[String] = []
@export var max_simultaneous_glitches: int = DEFAULT_MAX_CONCURRENT
@export var min_glitch_interval: float = DEFAULT_MIN_INTERVAL

# ---- Computed Properties ----
func get_all_event_ids() -> Array[String]:
	var all_ids: Array[String] = []
	all_ids.append_array(physics_glitch_pool)
	all_ids.append_array(hazard_glitch_pool)
	all_ids.append_array(room_logic_glitch_pool)
	return all_ids

func is_category_allowed(cat: GlitchCategory) -> bool:
	return cat in allowed_categories

func get_pool_for_category(cat: GlitchCategory) -> Array[String]:
	match cat:
		GlitchCategory.PHYSICS:
			return physics_glitch_pool.duplicate()
		GlitchCategory.HAZARD:
			return hazard_glitch_pool.duplicate()
		GlitchCategory.ROOM_LOGIC:
			return room_logic_glitch_pool.duplicate()
	return []

# ---- Factory Methods ----
static func create_startup_sector_config() -> RoomGlitchConfig:
	var config := RoomGlitchConfig.new()
	config.room_id = "startup_sector_1"
	config.room_display_name = "Startup Sector"
	config.allowed_categories = [
		GlitchCategory.PHYSICS,
		GlitchCategory.HAZARD,
		GlitchCategory.ROOM_LOGIC
	]
	config.physics_glitch_pool = ["speed_down", "gravity_flip"]
	config.hazard_glitch_pool = ["spike_shift"]
	config.room_logic_glitch_pool = ["checkpoint_drift"]
	config.max_simultaneous_glitches = 2
	config.min_glitch_interval = 8.0
	return config
