# Streamlit Session Environment Visibility Design

## Goal

Show the Step 1 “Session Environment Parameters” section only while the
application has an active SAS connection.

## Design

Use `sas_backend.is_connected` as the authoritative connection state for
rendering. The existing `st.session_state["sas_connected"]` flag remains
available for status compatibility, but the Connect handler must assign it
from the actual `success` result instead of unconditionally setting it to
`True`.

The environment parameter inputs, initialization button, and SAS log remain
inside the backend-state guard. The disconnected state continues to show the
connection controls and offline guidance, but no environment parameter
inputs.

## Behavior

- Failed connection: environment parameters remain hidden and the session
  status reports the connection error.
- Successful connection: environment parameters become visible.
- Disconnect: environment parameters become hidden on rerun.
- Backend state is authoritative even if session state becomes stale.

## Validation

Validate the source structure and run the repository's available Python
checks. Confirm that the guard uses `sas_backend.is_connected`, that failed
connections do not set the session flag to `True`, and that the forwarding
Streamlit module continues to target the root implementation.
