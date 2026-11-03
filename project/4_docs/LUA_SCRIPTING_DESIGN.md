# Lua scripting for MKDSrust mods: design (draft for review)

Status: proposal, 2026-11-03. Nothing implemented yet.

## Goal
Let modders change gameplay with small, safe scripts, without Rust, compiling or rebuilding the game. Examples:
- custom item odds;
- a "shells only" mode;
- a lap-time HUD;
- low-gravity karts;
- a new battle rule;
- debug tools for the Toolbox Test Bench.

Rust source patches stay the path for deep changes; Lua covers the large middle ground.

## Choices
| Question | Choice | Why |
|---|---|---|
| Language | **Luau** (Roblox's Lua dialect) through the `mlua` crate | Built for sandboxing untrusted scripts. Has optional type annotations, which help the Toolbox editor. Lua 5.1-compatible, so existing Lua tutorials apply. Has an interrupt hook for CPU limits |
| Where scripts run | In the PC game process, between game frames and at hooked calls | No emulation cost; scripts see and change the live game state |
| Packaging | `scripts/*.luau` inside a mod package, listed in `manifest.json` | Same install, enable and load-order flow as other mods |
| Exact/acceptance builds | Scripts never run (like other mods today) | The byte-identical race proof stays valid |

## What scripts can do (API v1)
Scripts get a curated API, **not** raw dictionary names. Research names still change, and mods must not break when
a field is renamed. The API maps stable names to the dictionary underneath and is versioned (`api = 1` in the
manifest).

```lua
-- per-frame callback
game.on("frame", function(f)
  for _, r in ipairs(race.racers()) do
    if r.is_player then hud.text(4, 4, string.format("%.1f km/h", r.speed_kmh)) end
  end
end)

-- an event with a result the script may change
game.on("item_roll", function(e)          -- e.racer, e.place, e.result
  if e.place == 1 then e.result = items.BANANA end
end)

-- state read and write, through named, typed properties
race.racer(0).speed_cap = race.racer(0).speed_cap * 1.2
```

v1 surface:
- **`game`:** events (`frame`, `race_start`, `race_end`, `lap`, `item_roll`, `item_use`, `hit`, `scene`), the
  frame number, the scene id.
- **`race`:**
  - course id and name, lap count, timer;
  - racers: position, speed, place, lap, item held, character, kart, `is_player`, `is_cpu`.
  - Writable where safe: speed cap, item held, lap, position (teleport).
- **`items`:** item ids, plus odds tables (read and write).
- **`input`:** the buttons this frame (read), and overriding them (for bots and replays in the Test Bench).
- **`hud`:** simple text and rectangles drawn by the PC host over the game. It doesn't touch DS VRAM.
- **`store`:** a small per-mod key/value table saved next to the mod's settings.
- **`log`:** lines in the game log, which the Toolbox shows.
- **`mem`** (advanced, flagged in the manifest): raw reads and writes of guest RAM by address, for experiments. Mods
  that use it get a "uses raw memory" badge on the site.

Events are implemented as **native hooks** on the game functions behind them. The same mechanism already replaces
functions (`Machine::hook`, `native::NATIVE`). A hook runs the Lua handlers, applies changed results, and continues
the original function, or skips it when the event says so.

## Safety
- **Sandbox:** no `io`, `os`, `require` of files, `load` of bytecode, FFI or network. Each mod gets its own Luau VM
  with a read-only global environment (Luau `sandbox` mode).
- **Limits:** a CPU budget per frame per mod, via the interrupt callback (default 2 ms); a memory limit per VM (default
  16 MB). A mod over its limits is paused with a message in the log and an overlay notice. The game keeps running.
- **Errors:** a script error disables that handler and logs the stack trace. It never crashes the game.
- **Site screening:** `.luau` files become an allowed type in `PLUGIN_FORMAT.md`. Today scripts are blocked, so the
  contract and the site checks need a version bump. The site screens them with a static scan (size limit; no binary
  chunks, no obfuscation patterns) and flags `mem` usage. Moderators review them like any upload.
- **No Nintendo material:** scripts are text written by modders, and the same "no game content" rules apply.

## Toolbox integration (stage 7)
- **Code workspace:** Monaco with Luau syntax highlighting, autocomplete from a generated API definition file
  (`mkdsrust.d.luau`), type checking with `luau-analyze`, and inline errors.
- **Test Bench:** Play runs the scripts with `--race`. **Hot reload works for scripts**: a changed `.luau` file
  reloads its VM between frames, without restarting the game.
- **Recipes:** "Custom item odds", "HUD speedometer", "Low gravity", "Time-trial ghost tools".

## Load order and conflicts
Scripts run in mod load order (`enabled.txt`). For events with results (`item_roll`), later mods see earlier mods'
changes and can override them. The manifest can declare `conflicts` as today.

## Work plan
1. `mlua` + Luau in the native host; a VM per mod; the `frame` event; `log`; `race.racers()` (read-only); a
   sandbox and limits test suite.
2. Writable properties, the `hud` overlay, `input`, `store`.
3. Native hooks for events (`item_roll` first: it's the most requested). An exact-mode guard: the hooks are absent
   in `--timing exact`.
4. Bump the package format to v2 (`scripts`, `api`), update launcher, site screening and docs together.
5. Hand the Toolbox Code workspace to Codex.

## Open questions for the owner
1. Luau (recommended) or plain Lua 5.4? Lua 5.4 is more familiar but harder to sandbox and has no types.
2. Should raw `mem` be allowed in published mods (badged), or only locally?
3. Are online/multiplayer-affecting scripts out of scope for now (assumed yes)?
