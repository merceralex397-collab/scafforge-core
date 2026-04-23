# Example Inventory Records

These examples are illustrative scaffolding for plan `15`. They are supporting material, not the canonical contract.

## `RepoRecord`

```json
{
  "repo_id": "repo_durable_arcade01",
  "human_name": "Arcade Starter",
  "git_remote": "https://github.com/example/arcade-starter.git",
  "repo_class": "durable",
  "product_family": "game",
  "lifecycle_state": "active",
  "current_assigned_host": "wsl-main",
  "inventory_origin": "adopted",
  "autonomy_level": "partial"
}
```

## `HostRecord`

```json
{
  "host_id": "wsl-main",
  "host_kind": "wsl",
  "display_name": "Local WSL Ubuntu",
  "connectivity_state": "healthy",
  "worker_capabilities": ["node", "python", "git", "godot"]
}
```

## `PathBinding`

```json
{
  "repo_id": "repo_durable_arcade01",
  "host_id": "wsl-main",
  "absolute_path": "/home/pc/code/ScafforgeProjects/arcade-starter",
  "path_role": "primary",
  "binding_state": "present"
}
```
