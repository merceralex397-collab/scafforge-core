womanvshorseVA

*** When opening Godot ***

--- Debug adapter server started on port 6006 ---
Could not find version of build tools that matches Target SDK, using 36.1.0
--- GDScript language server started on port 6005 ---
  ERROR: res://scripts/wave_spawner.gd:77 - Parse Error: Could not parse global class "EnemyBase" from "res://scripts/enemy_base.gd".
  ERROR: res://scripts/wave_spawner.gd:95 - Parse Error: Could not parse global class "EnemyBase" from "res://scripts/enemy_base.gd".
  ERROR: res://scripts/wave_spawner.gd:79 - Parse Error: Could not resolve class "EnemyBrown", because of a parser error.
  ERROR: res://scripts/wave_spawner.gd:80 - Parse Error: Could not resolve class "EnemyBlack", because of a parser error.
  ERROR: res://scripts/wave_spawner.gd:81 - Parse Error: Could not resolve class "EnemyWar", because of a parser error.
  ERROR: res://scripts/wave_spawner.gd:82 - Parse Error: Could not resolve class "EnemyBoss", because of a parser error.
  ERROR: res://scripts/wave_spawner.gd:83 - Parse Error: Could not resolve class "EnemyBrown", because of a parser error.
  ERROR: modules/gdscript/gdscript.cpp:2907 - Failed to load script "res://scripts/wave_spawner.gd" with error "Parse error".



*** When running/testing in Godot ***


Line 77:Could not parse global class "EnemyBase" from "res://scripts/enemy_base.gd".
Line 95:Could not parse global class "EnemyBase" from "res://scripts/enemy_base.gd".
Line 79:Could not resolve class "EnemyBrown", because of a parser error.
Line 80:Could not resolve class "EnemyBlack", because of a parser error.
Line 81:Could not resolve class "EnemyWar", because of a parser error.
Line 82:Could not resolve class "EnemyBoss", because of a parser error.
Line 83:Could not resolve class "EnemyBrown", because of a parser error.


Other errors:

W 0:00:00:896   GDScript::reload: The local variable "border_rect" is declared but never used in the block. If this is intended, prefix it with an underscore: "_border_rect".
  <GDScript Error>UNUSED_VARIABLE
  <GDScript Source>main.gd:181 @ GDScript::reload()


W 0:00:00:901   GDScript::reload: The signal "score_changed" is declared but never explicitly used in the class.
  <GDScript Error>UNUSED_SIGNAL
  <GDScript Source>hud.gd:3 @ GDScript::reload()
