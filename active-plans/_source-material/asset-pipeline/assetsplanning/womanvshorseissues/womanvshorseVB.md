womanvshorseVB


*** When opening Godot: ***

Godot Engine v4.6.1.stable.official (c) 2007-present Juan Linietsky, Ariel Manzur & Godot Contributors.
--- Debug adapter server started on port 6006 ---
Could not find version of build tools that matches Target SDK, using 36.1.0
res://assets/fonts/PressStart2P-Regular.ttf: Pixel font detected, disabling subpixel positioning.
  ERROR: res://scenes/ui/game_over.gd:14 - Parse Error: Used space character for indentation instead of tab as used before in the file.
  ERROR: modules/gdscript/gdscript.cpp:2907 - Failed to load script "res://scenes/ui/game_over.gd" with error "Parse error".
  ERROR: scene/resources/resource_format_text.cpp:40 - res://scenes/enemies/horse_base.tscn:15 - Parse Error: Can't load cached ext-resource id: res://assets/sprites/lpc-horses-rework/PNG/64x64/horse-brown.png.
  ERROR: Failed loading resource: res://scenes/enemies/horse_base.tscn.
  ERROR: res://scripts/wave_spawner.gd:7 - Parse Error: Could not preload resource file "res://scenes/enemies/horse_base.tscn".
  ERROR: modules/gdscript/gdscript.cpp:2907 - Failed to load script "res://scripts/wave_spawner.gd" with error "Parse error".
--- GDScript language server started on port 6005 ---




*** When trying to run in Godot *** 

E 0:00:02:892   title_screen.gd:9 @ _on_start_pressed(): res://scenes/player/player.tscn:18 - Parse Error: Can't load cached ext-resource id: res://assets/sprites/kenney-topdown-shooter/PNG/Woman Green/womanGreen_gun.png.
  <C++ Source>  scene/resources/resource_format_text.cpp:40 @ _printerr()
  <Stack Trace> title_screen.gd:9 @ _on_start_pressed()


E 0:00:02:892   title_screen.gd:9 @ _on_start_pressed(): Failed loading resource: res://scenes/player/player.tscn.
  <C++ Error>   Condition "found" is true. Returning: Ref<Resource>()
  <C++ Source>  core/io/resource_loader.cpp:343 @ _load()
  <Stack Trace> title_screen.gd:9 @ _on_start_pressed()


W 0:00:02:905   GDScript::reload: The class variable "_hurtbox_area" is declared but never used in the class.
  <GDScript Error>UNUSED_PRIVATE_CLASS_VARIABLE
  <GDScript Source>horse_base.gd:10 @ GDScript::reload()

W 0:00:02:905   GDScript::reload: The parameter "delta" is never used in the function "_physics_process()". If this is intended, prefix it with an underscore: "_delta".
  <GDScript Error>UNUSED_PARAMETER
  <GDScript Source>horse_base.gd:30 @ GDScript::reload()


E 0:00:02:907   title_screen.gd:9 @ _on_start_pressed(): res://scenes/enemies/horse_base.tscn:15 - Parse Error: Can't load cached ext-resource id: res://assets/sprites/lpc-horses-rework/PNG/64x64/horse-brown.png.
  <C++ Source>  scene/resources/resource_format_text.cpp:40 @ _printerr()
  <Stack Trace> title_screen.gd:9 @ _on_start_pressed()


E 0:00:02:907   title_screen.gd:9 @ _on_start_pressed(): Failed loading resource: res://scenes/enemies/horse_base.tscn.
  <C++ Error>   Condition "found" is true. Returning: Ref<Resource>()
  <C++ Source>  core/io/resource_loader.cpp:343 @ _load()
  <Stack Trace> title_screen.gd:9 @ _on_start_pressed()
