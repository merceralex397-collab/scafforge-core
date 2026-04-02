extends Node

# GameState - Autoload singleton for global game state
# Signal contract:
#   - level_started(level_id: String)
#   - level_completed(level_id: String)
#   - game_saved
#   - game_loaded

signal level_started(level_id: String)
signal level_completed(level_id: String)
signal game_saved
signal game_loaded

var current_level_id: String = ""
var score: int = 0
var session_flags: Dictionary = {}

func _ready() -> void:
	print("[GameState] Initialized - Current level: %s" % current_level_id)

func start_level(level_id: String) -> void:
	current_level_id = level_id
	emit_signal("level_started", level_id)
	print("[GameState] Level started: %s" % level_id)

func complete_level(level_id: String) -> void:
	emit_signal("level_completed", level_id)
	print("[GameState] Level completed: %s" % level_id)

func add_score(points: int) -> void:
	score += points
	print("[GameState] Score: %d" % score)

func save_game() -> void:
	emit_signal("game_saved")
	print("[GameState] Game saved")

func load_game() -> void:
	emit_signal("game_loaded")
	print("[GameState] Game loaded")
