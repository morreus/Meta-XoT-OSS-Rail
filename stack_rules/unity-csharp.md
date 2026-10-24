# Stack rules: Unity / C#

(A starting reference: keep what fits your project.)

## Detection markers
`*.csproj`, `*.sln`, `Assets/`, `ProjectSettings/`, `Packages/manifest.json`, `*.unity` scenes, `*.asmdef`.

## Commands
- **Run/build:** in the Unity Editor (no standard CLI run). Batch builds: `Unity -batchmode -quit -projectPath . -executeMethod <BuildClass.Method>` only if the project defines one.
- **Test:** Unity Test Framework — **EditMode** (fast, no scene) and **PlayMode** (runtime) tests, NUnit. Run via the Test Runner window or `-runTests -testPlatform EditMode|PlayMode`.
- **Format:** project's `.editorconfig` if present; Rider/VS formatting.
- **Packages:** UPM via `Packages/manifest.json`.

## Conventions
- `[SerializeField] private` over public fields; respect existing prefab/scene wiring.
- Cache references in `Awake`/`Start`; never `GameObject.Find` / `GetComponent` in `Update`.
- Object pooling for frequently spawned objects; avoid `Instantiate`/`Destroy` churn.
- ScriptableObjects for shared/config data; assembly definitions (`.asmdef`) to keep compile times down.
- Use `CompareTag` not `== tag`; prefer events over per-frame polling.

## Instrumentation style
- `Debug.Log` gated by `#if UNITY_EDITOR || DEVELOPMENT_BUILD`; event-based, never per-frame in shipping code.
- Consider `[System.Diagnostics.Conditional("DEVELOPMENT_BUILD")]` helpers or a wrapper logger so it's trivially stripped. Remove/gate before commit.

## Risk checklist (surface any this change touches)
- **Serialization** — renamed/removed `[SerializeField]` fields lose data; scene/prefab reference breakage; ScriptableObject schema changes; `[FormerlySerializedAs]` when renaming; dictionaries don't serialize by default.
- **Performance (esp. mobile)** — per-frame GC allocations (LINQ, boxing, string concat, repeated `transform.position`), `Update` cost, draw calls/batching, overdraw, texture/atlas memory, physics in `FixedUpdate`. Use non-allocating API variants (`Physics.*NonAlloc`, `GetComponents(list)`), `StringBuilder` for runtime strings (avoid JSON/XML parsing in hot paths; prefer MessagePack/Protobuf when perf-critical), and cache `WaitForSeconds`/component lookups. Mobile frame budget ≈ 22 ms at 30 fps (leave ~35% idle for thermals); mobile GPUs are tile-based (TBDR) — watch overdraw and full-screen post-processing.
- **UI** — Canvas render mode, CanvasScaler reference resolution + match mode, anchors/pivots, nested canvases (rebuild cost), multiple resolutions/aspect ratios, notch/safe areas, layout-group cost.
- **Lifecycle/order** — `Awake` vs `OnEnable` vs `Start`; script execution order; coroutine cancellation on disable/destroy; `OnDestroy` cleanup; domain-reload settings.
- **Null/destroy semantics** — Unity's overloaded `== null` (destroyed objects compare equal to null); don't cache destroyed refs.
- **Async/threading** — Unity API is main-thread only; `async`/`Task` and threads must marshal back; `Time.deltaTime` only on main thread.
- **Asset loading** — Resources vs Addressables; async load handles; memory unload.
- **Platform** — `#if UNITY_ANDROID / UNITY_IOS` defines; Input System vs legacy; per-platform player settings.
- **Floats** — never `==` compare; use a tolerance.

## Editor traps that silently invalidate verification
Each of these produces confident, wrong results.

- **Play mode freezes when the Editor is backgrounded** if `Application.runInBackground` is false at
  runtime — even when the *player setting* is true. The Editor still reports `isPlaying=True`,
  `isPaused=False`, `timeScale=1` while advancing **zero frames**. Any automated Play-mode check will
  happily measure a frozen game. Set `Application.runInBackground = true` at runtime, keep the Editor
  focused, and assert the frame count actually advanced before trusting a Play-mode measurement.
- **Opening a scene mutates it.** `[ExecuteInEditMode]` components rewrite their own transforms on
  load and Unity re-serialises the file to the current format — while reporting the scene as *not
  dirty*. An opportunistic save then bakes in changes nobody made. Never save a scene you only opened
  to look at; if a scene diff appears that you didn't author, suspect re-serialisation before
  assuming someone's work.
- **A scene that bounces to another on Play** (e.g. a bootstrap scene that loads another scene at start) cannot be
  Play-tested in isolation — anything attached to it dies before it runs. Prefer Edit-mode
  verification for components that support it.

## Verification style
- Enter Play mode and exercise the actual flow.
- Test at **≥ 2 aspect ratios** (e.g. 16:9 landscape and 9:16 portrait) for any UI change; check safe areas on a notched profile.
- Build to a target device for platform-specific or perf-sensitive changes.
- Use the Profiler for allocation/FPS-sensitive changes (aim for 0 per-frame GC alloc in hot paths).
- Console clean (no new errors/warnings).

## Common gotchas
- `MissingReferenceException` from using a destroyed object; coroutines silently stop when the GameObject is disabled; `[SerializeReference]` needed for polymorphic serialization; scene changes are async (`LoadSceneAsync`); `Time.timeScale` affects `WaitForSeconds`.
