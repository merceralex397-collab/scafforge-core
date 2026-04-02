extends Node

# LevelManager - Autoload singleton for level loading and scene transitions
# Signal contract:
#   - level_loaded(scene_path: String)
#   - transition_started
#   - transition_completed

signal level_loaded(scene_path: String)
signal transition_started
signal transition_completed

var current_level_path: String = ""
var level_container_path: NodePath = NodePath("/root/Main/LevelContainer")

func _ready() -> void:
	print("[LevelManager] Initialized")

func load_level(level_path: String) -> void:
	emit_signal("transition_started")
	print("[LevelManager] Loading level: %s" % level_path)
	
	# Unload current level if exists
	var container = get_node(level_container_path) if has_node(level_container_path) else null
	if container:
		for child in container.get_children():
			child.queue_free()
	
	current_level_path = level_path
	emit_signal("level_loaded", level_path)
	emit_signal("transition_completed")
	print("[LevelManager] Level loaded: %s" % level_path)

func get_current_level() -> String:
	return current_level_path
