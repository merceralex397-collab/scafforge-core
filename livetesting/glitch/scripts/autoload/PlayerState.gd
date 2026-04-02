extends Node

# PlayerState - Autoload singleton for player health, abilities, and checkpoint data
# Signal contract:
#   - player_died
#   - player_respawned
#   - checkpoint_activated(position: Vector2)

signal player_died
signal player_respawned
signal checkpoint_activated(position: Vector2)

var health: int = 3
var max_health: int = 3
var abilities: Array = []
var current_checkpoint: Vector2 = Vector2.ZERO
var is_alive: bool = true

func _ready() -> void:
	print("[PlayerState] Initialized - Health: %d" % health)

func take_damage(amount: int = 1) -> void:
	health -= amount
	if health <= 0:
		health = 0
		is_alive = false
		emit_signal("player_died")
	else:
		print("[PlayerState] Took %d damage, health: %d" % [amount, health])

func respawn() -> void:
	health = max_health
	is_alive = true
	emit_signal("player_respawned")
	print("[PlayerState] Respawned at %s" % str(current_checkpoint))

func set_checkpoint(pos: Vector2) -> void:
	current_checkpoint = pos
	emit_signal("checkpoint_activated", pos)
	print("[PlayerState] Checkpoint set at %s" % str(pos))
