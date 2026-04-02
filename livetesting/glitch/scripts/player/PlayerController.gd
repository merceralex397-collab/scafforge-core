# PlayerController.gd
# Baseline player movement controller for Glitch
# CharacterBody2D with state machine, coyote time, jump buffering, wall slide, wall jump, and dash

extends CharacterBody2D
class_name PlayerController

# State machine - renamed to avoid conflict with PlayerState autoload
enum MoveState {
	IDLE,
	RUN,
	JUMP,
	FALL,
	WALL_SLIDE,
	DASH
}

# Movement constants (loaded from PlayerDefaults)
var defaults: PlayerDefaults

# Current state
var state: MoveState = MoveState.IDLE

# Input tracking
var move_input: float = 0.0
var facing_right: bool = true

# Coyote time
var time_since_grounded: float = 0.0
var is_grounded_previous: bool = false

# Jump buffering
var jump_buffer_time: float = 0.0

# Wall interaction
var wall_direction: int = 0  # -1 = left wall, 1 = right wall
var wall_jump_lockout: float = 0.0  # Time before can grab same wall again

# Dash state
var dash_timer: float = 0.0
var dash_cooldown_timer: float = 0.0
var dash_direction: Vector2 = Vector2.RIGHT

# Node references
@onready var sprite: Sprite2D = $Sprite
@onready var collision_shape: CollisionShape2D = $CollisionShape2D

# Glitch physics modifier reference (via autoload)
var physics_modifier: GlitchPhysicsModifier = null

func _ready() -> void:
	# Create or load PlayerDefaults
	defaults = PlayerDefaults.new()
	
	# Get GlitchPhysicsModifier from autoload
	physics_modifier = get_node_or_null("/root/GlitchPhysicsModifier")
	if not physics_modifier:
		# Fallback: try via GlitchEventManager if in scene tree
		var event_manager = get_node_or_null("/root/GlitchEventManager")
		if event_manager:
			physics_modifier = event_manager.get_physics_modifier()
	
	if physics_modifier:
		print("[PlayerController] Connected to GlitchPhysicsModifier")
	else:
		push_warning("[PlayerController] GlitchPhysicsModifier not found - physics glitches will have no effect")
	
	# Connect to level/checkpoint systems if needed
	# For now, standalone controller is sufficient for CORE-001

func _physics_process(delta: float) -> void:
	_process_input()
	_process_coyote_time(delta)
	_process_jump_buffer(delta)
	_process_wall_lockout(delta)
	_process_dash_cooldown(delta)
	_process_dash_input()
	
	match state:
		MoveState.IDLE:
			_idle_state(delta)
		MoveState.RUN:
			_run_state(delta)
		MoveState.JUMP:
			_jump_state(delta)
		MoveState.FALL:
			_fall_state(delta)
		MoveState.WALL_SLIDE:
			_wall_slide_state(delta)
		MoveState.DASH:
			_dash_state(delta)
	
	# Apply movement
	move_and_slide()
	
	# Track previous grounded state for coyote time
	is_grounded_previous = is_on_floor()

func _process_input() -> void:
	# Horizontal movement
	move_input = 0.0
	if Input.is_action_pressed("move_left"):
		move_input -= 1.0
	if Input.is_action_pressed("move_right"):
		move_input += 1.0
	
	# Update facing direction
	if move_input > 0:
		facing_right = true
		sprite.flip_h = false
	elif move_input < 0:
		facing_right = false
		sprite.flip_h = true

func _process_coyote_time(delta: float) -> void:
	if is_on_floor():
		time_since_grounded = 0.0
	else:
		time_since_grounded += delta

func _process_jump_buffer(delta: float) -> void:
	if Input.is_action_just_pressed("jump"):
		jump_buffer_time = defaults.JUMP_BUFFER_TIME
	if jump_buffer_time > 0:
		jump_buffer_time -= delta

func _process_wall_lockout(delta: float) -> void:
	if wall_jump_lockout > 0:
		wall_jump_lockout -= delta

func _process_dash_cooldown(delta: float) -> void:
	if dash_cooldown_timer > 0:
		dash_cooldown_timer -= delta

func _process_dash_input() -> void:
	if _should_dash():
		_do_dash()

# ---- IDLE State ----
func _idle_state(delta: float) -> void:
	velocity.x = 0.0
	var effective_gravity = defaults.GRAVITY
	if physics_modifier:
		effective_gravity *= physics_modifier.gravity_multiplier
	velocity.y += effective_gravity * delta
	if velocity.y > defaults.MAX_FALL_SPEED:
		velocity.y = defaults.MAX_FALL_SPEED
	
	# Transitions
	if move_input != 0:
		state = MoveState.RUN
	elif _should_jump():
		_do_jump()
		state = MoveState.JUMP
	elif not is_on_floor():
		state = MoveState.FALL

# ---- RUN State ----
func _run_state(delta: float) -> void:
	var effective_speed = defaults.SPEED
	var effective_gravity = defaults.GRAVITY
	if physics_modifier:
		effective_speed *= physics_modifier.speed_multiplier
		effective_gravity *= physics_modifier.gravity_multiplier
	velocity.x = move_input * effective_speed
	velocity.y += effective_gravity * delta
	if velocity.y > defaults.MAX_FALL_SPEED:
		velocity.y = defaults.MAX_FALL_SPEED
	
	# Transitions
	if move_input == 0 and is_on_floor():
		state = MoveState.IDLE
	elif _should_jump():
		_do_jump()
		state = MoveState.JUMP
	elif not is_on_floor():
		state = MoveState.FALL
	elif _should_wall_slide():
		state = MoveState.WALL_SLIDE

# ---- JUMP State ----
func _jump_state(delta: float) -> void:
	# Apply gravity
	var effective_gravity = defaults.GRAVITY
	var effective_speed = defaults.SPEED
	if physics_modifier:
		effective_gravity *= physics_modifier.gravity_multiplier
		effective_speed *= physics_modifier.speed_multiplier
	velocity.y += effective_gravity * delta
	if velocity.y > defaults.MAX_FALL_SPEED:
		velocity.y = defaults.MAX_FALL_SPEED
	
	# Horizontal control (reduced in air)
	velocity.x = move_input * effective_speed * 0.8
	
	# Transitions
	if velocity.y >= 0 or not is_on_floor():
		state = MoveState.FALL
	elif _should_wall_slide():
		state = MoveState.WALL_SLIDE

# ---- FALL State ----
func _fall_state(delta: float) -> void:
	var effective_gravity = defaults.GRAVITY
	var effective_speed = defaults.SPEED
	if physics_modifier:
		effective_gravity *= physics_modifier.gravity_multiplier
		effective_speed *= physics_modifier.speed_multiplier
	velocity.y += effective_gravity * delta
	if velocity.y > defaults.MAX_FALL_SPEED:
		velocity.y = defaults.MAX_FALL_SPEED
	
	# Horizontal control
	velocity.x = move_input * effective_speed * 0.8
	
	# Transitions
	if is_on_floor():
		if move_input == 0:
			state = MoveState.IDLE
		else:
			state = MoveState.RUN
	elif _should_wall_slide():
		state = MoveState.WALL_SLIDE
	elif _should_jump():
		_do_jump()
		state = MoveState.JUMP

# ---- WALL_SLIDE State ----
func _wall_slide_state(delta: float) -> void:
	# Wall slide: reduced fall speed
	var effective_gravity = defaults.GRAVITY
	var effective_speed = defaults.SPEED
	var effective_wall_slide_speed = defaults.WALL_SLIDE_SPEED
	if physics_modifier:
		effective_gravity *= physics_modifier.gravity_multiplier
		effective_speed *= physics_modifier.speed_multiplier
		effective_wall_slide_speed *= physics_modifier.wall_slide_speed_multiplier
	velocity.y += effective_gravity * delta * 0.5  # Half gravity when wall sliding
	if velocity.y > effective_wall_slide_speed:
		velocity.y = effective_wall_slide_speed
	
	# Slide down wall
	velocity.x = wall_direction * effective_speed * 0.5
	
	# Transitions
	if _should_jump():
		_do_wall_jump()
		state = MoveState.JUMP
	elif not _should_wall_slide():
		state = MoveState.FALL
	elif is_on_floor():
		state = MoveState.IDLE

# ---- DASH State ----
func _dash_state(delta: float) -> void:
	dash_timer -= delta
	
	# Lock to dash direction, disable gravity
	velocity = dash_direction * defaults.DASH_SPEED
	
	# Transitions
	if dash_timer <= 0:
		dash_cooldown_timer = defaults.DASH_COOLDOWN
		if is_on_floor():
			if move_input == 0:
				state = MoveState.IDLE
			else:
				state = MoveState.RUN
		else:
			state = MoveState.FALL

# ---- Helper Methods ----
func _should_jump() -> bool:
	# Jump if: buffer has time AND (grounded OR coyote time valid)
	return jump_buffer_time > 0 and (is_on_floor() or time_since_grounded <= defaults.COYOTE_TIME)

func _do_jump() -> void:
	var effective_jump_force = defaults.JUMP_FORCE
	if physics_modifier:
		effective_jump_force *= physics_modifier.jump_force_multiplier
	velocity.y = effective_jump_force
	jump_buffer_time = 0.0
	time_since_grounded = defaults.COYOTE_TIME  # Prevent double jump via coyote

func _should_wall_slide() -> bool:
	if wall_jump_lockout > 0:
		return false
	if not is_on_wall():
		return false
	if is_on_floor():
		return false
	
	# Check if moving toward wall
	var wall_normal = get_last_slide_collision().get_collider_normal()
	wall_direction = int(sign(wall_normal.x))
	
	if wall_direction == -1 and move_input < 0:  # Left wall, moving left
		return true
	if wall_direction == 1 and move_input > 0:  # Right wall, moving right
		return true
	
	return false

func _do_wall_jump() -> void:
	# Push away from wall
	var effective_jump_force = defaults.JUMP_FORCE
	var effective_speed = defaults.SPEED
	if physics_modifier:
		effective_jump_force *= physics_modifier.jump_force_multiplier
		effective_speed *= physics_modifier.speed_multiplier
	velocity.y = effective_jump_force * 0.9
	velocity.x = -wall_direction * effective_speed * defaults.WALL_JUMP_LERP
	
	# Lockout to prevent immediate re-grab
	wall_jump_lockout = 0.1  # 100ms
	
	# Update facing direction
	facing_right = (wall_direction < 0)
	sprite.flip_h = not facing_right
	
	jump_buffer_time = 0.0
	time_since_grounded = defaults.COYOTE_TIME

func _should_dash() -> bool:
	if dash_cooldown_timer > 0:
		return false
	if not Input.is_action_just_pressed("dash"):
		return false
	return true

func _do_dash() -> void:
	# Determine dash direction
	if move_input != 0:
		dash_direction = Vector2(sign(move_input), 0)
	else:
		dash_direction = Vector2(1 if facing_right else -1, 0)
	
	dash_timer = defaults.DASH_DURATION
	state = MoveState.DASH

# ---- Public Methods for UX-001 Touch Integration ----
func get_move_input() -> float:
	return move_input

func is_facing_right() -> bool:
	return facing_right

func get_current_state() -> MoveState:
	return state
