# GlitchSystemInitializer.gd
# Helper script to initialize the glitch system with all events and room configs
# Run this during Main scene _ready() or attach to a dedicated init node

extends Node

@onready var event_manager: Node = null

func _ready() -> void:
	print("[GlitchSystemInitializer] Initializing glitch system...")
	
	# Find or create GlitchEventManager
	event_manager = get_node_or_null("/root/GlitchEventManager")
	if not event_manager:
		# Try to instance from scene
		var scene_path = "res://scenes/glitch/GlitchEventManager.tscn"
		var scene = load(scene_path)
		if scene:
			event_manager = scene.instantiate()
			get_tree().root.add_child(event_manager)
			print("[GlitchSystemInitializer] Instantiated GlitchEventManager from scene")
		else:
			push_error("[GlitchSystemInitializer] GlitchEventManager scene not found!")
			return
	
	# Register all startup sector events
	var events = GlitchEventRegistry.build_startup_sector_events()
	for event_id in events:
		event_manager.register_glitch_event(events[event_id])
	
	# Set room config
	var room_config = RoomGlitchConfig.create_startup_sector_config()
	event_manager.set_room_config(room_config)
	
	print("[GlitchSystemInitializer] Glitch system initialized with %d events" % events.size())
