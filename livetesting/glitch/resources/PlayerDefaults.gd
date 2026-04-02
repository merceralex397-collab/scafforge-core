# PlayerDefaults.gd
# Centralized movement constants for Glitch player controller
# Tune these values in the Inspector after adding to a scene or as a standalone resource

extends Resource
class_name PlayerDefaults

# Movement
@export var SPEED: float = 300.0           # Horizontal run speed (px/s)
@export var JUMP_FORCE: float = -450.0     # Initial jump velocity (negative Y = up)
@export var GRAVITY: float = 980.0         # Gravity acceleration (px/s²)
@export var MAX_FALL_SPEED: float = 800.0  # Terminal velocity

# Wall Interaction
@export var WALL_SLIDE_SPEED: float = 120.0   # Max fall speed when wall sliding
@export var WALL_JUMP_LERP: float = 0.8      # Horizontal push factor on wall jump (0-1)

# Dash
@export var DASH_SPEED: float = 600.0      # Dash velocity magnitude (px/s)
@export var DASH_DURATION: float = 0.15    # Dash duration (seconds)
@export var DASH_COOLDOWN: float = 0.8     # Cooldown between dashes (seconds)

# Coyote Time & Jump Buffering
@export var COYOTE_TIME: float = 0.1       # Seconds after leaving ground where jump still works
@export var JUMP_BUFFER_TIME: float = 0.12 # Seconds before landing where jump input is remembered
