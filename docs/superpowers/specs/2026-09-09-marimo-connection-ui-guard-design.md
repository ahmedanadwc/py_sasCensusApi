# Marimo Connection UI Guard Design

## Goal

Prevent users from accessing or navigating to Steps 2–5 of the Marimo
notebook until an active SAS connection exists.

## Behavior

- Step 1 remains visible and usable while disconnected.
- Step 1's existing Session Environment Parameters guard remains based on
  `sas_backend.is_connected`.
- Navigation controls for Steps 2–5 are disabled while disconnected.
- The orchestrator renders only Step 1 while disconnected and shows a clear
  prompt to connect to SAS before continuing.
- Once `sas_backend.is_connected` is true, Steps 2–5 render normally.
- Forward navigation callbacks defensively verify the connection before
  changing steps, preventing stale button events from bypassing the guard.
- Existing backward navigation and step-specific business logic remain
  unchanged.

## Implementation

Use `sas_backend.is_connected` as the single authoritative predicate. Pass the
connection state into the navigation-bar and orchestrator cells so those cells
recompute their UI on Marimo reactive updates. Keep the guard at the
orchestrator boundary rather than duplicating UI guards throughout every later
step card.

Navigation buttons should remain present for a consistent layout, but Steps 2–5
must use `disabled=True` while disconnected. The Step 1 Next callback should
only call `set_step(1)` when connected.

## Validation

Add focused source-level tests for the connection predicate, disabled
navigation, conditional orchestrator rendering, and guarded Step 1 forward
navigation. Compile `src\py_sascensusapi\app.py` and confirm the existing
Marimo session artifact remains consistent with the source after regeneration
or the repository's notebook validation command.
