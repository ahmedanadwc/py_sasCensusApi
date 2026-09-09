# Sequential Wizard Navigation Design

## Goal

Prevent users from navigating ahead of the wizard's completed prerequisites
while keeping completed steps available for review.

## Unlock rules

The wizard exposes five steps with these access conditions:

- Step 1 is always unlocked.
- Step 2 unlocks when `sas_backend.is_connected` is true.
- Step 3 unlocks after `step2_result` is populated by a successful Step 2
  operation.
- Step 4 unlocks after `step3_result` is populated by a successful Step 3
  operation.
- Step 5 unlocks after the user applies a valid endpoint to
  `st.session_state.picked_endpoint`.

The highest unlocked step is recalculated on every Streamlit rerun. Disconnecting
SAS therefore immediately locks Step 2 and later steps again. Existing result
state is retained, but it cannot bypass the current connection prerequisite.

## UI behavior

Sidebar navigation buttons for locked steps use Streamlit's `disabled=True`
option. The current step and all unlocked prior steps remain clickable.

Each in-step Next button uses the same unlock predicate as the sidebar. A locked
transition is never sent to `set_step()`. Back buttons remain available for
previous unlocked steps.

## Implementation structure

Add a small pure helper near `set_step()` that returns the highest unlocked
step from the current backend/session state. Use that helper for sidebar button
disabled state and for each Next button. Keep step-specific business operations
unchanged; they continue to populate the existing result fields.

## Validation

Add focused tests for the unlock sequence, including initial state, successful
connection, completed Step 2 and Step 3 results, endpoint application, and
re-locking after disconnect. Compile both Streamlit entry points and run the
focused test suite.
