# Stack rules: Flutter / Dart

(A starting reference: keep what fits your project.)

## Detection markers
`pubspec.yaml`, `lib/*.dart`, sibling `android/` + `ios/` (and/or `web/`, `macos/`), `.dart_tool/`, `analysis_options.yaml`.

## Commands
- **Run:** `flutter run` (note `--flavor` and `-d <device>`).
- **Test:** `flutter test` (unit + widget), golden tests if present, `integration_test/` via `flutter test integration_test`.
- **Analyze/format:** `flutter analyze`, `dart format .`.
- **Deps:** `flutter pub get`; codegen via `dart run build_runner build` if used.
- **Build:** `flutter build apk|ipa|web` (+ flavor).

## Conventions
- Sound null-safety; `const` constructors wherever possible; small, composable widgets.
- Keep `setState` scope tight; lift state only as needed; follow the app's state-management choice (Provider / Riverpod / Bloc) — don't mix paradigms.
- Immutable models; `copyWith`; `==`/`hashCode` (or freezed/equatable) for value types.
- Use `Key`s where widget identity matters in lists/animations.
- Honour `analysis_options.yaml` lints; existing feature/folder structure.

## Instrumentation style
- `debugPrint` / `dart:developer log` gated by `kDebugMode`; `assert(...)` for invariants (stripped in release). Never log in `build()`. Remove or gate before commit.

## Risk checklist (surface any this change touches)
- **Rebuild performance** — unnecessary rebuilds, expensive work in `build()`, missing `const`, rebuilding large subtrees on small state changes; use `const`, `Selector`/`select`, `RepaintBoundary`.
- **Async** — unhandled `Future` errors; using `BuildContext` across an `await` gap (guard with `if (!mounted) return;`); cancellation; `FutureBuilder`/`StreamBuilder` rebuild semantics.
- **Lifecycle / leaks** — dispose controllers, `AnimationController`, `StreamSubscription`, `TextEditingController`, focus nodes in `dispose()`; `setState` after dispose.
- **Layout & lists** — overflow errors; responsiveness across screen sizes/orientations; text scale factor; `SafeArea`; intrinsic sizing cost; `MediaQuery` rebuilds. Long lists must use `ListView.builder`/`GridView.builder` (lazy); wrap frequently-repainting subtrees in `RepaintBoundary`.
- **Images** — unoptimized/oversized images blow memory; use appropriately sized assets, `cacheWidth`/`cacheHeight`, and caching.
- **Platform** — platform channels; iOS vs Android behaviour/permissions; plugin platform support; web/desktop differences if targeted.
- **Concurrency** — heavy work off the UI isolate (`compute`/isolates); jank from synchronous work on the main isolate.
- **State** — provider scope/lifetime; rebuild storms; global vs scoped state.
- **Golden tests** — font/render fragility across environments/CI.

## Verification style
- `flutter analyze` clean + `flutter test` (incl. widget/golden) green; paste real output.
- Run on at least one device/emulator for UI changes; check **≥ 2 screen sizes/orientations** and large text scale.
- If both platforms are targeted, sanity-check iOS and Android for platform-channel/permission changes.

## Common gotchas
- `setState() called after dispose()`; `BuildContext` used after `await` without `mounted` check; `RenderFlex overflowed`; hot-reload preserving stale state (use hot-restart to verify); missing `const` causing avoidable rebuilds; `ListView` without `itemExtent`/keys causing scroll jank.
