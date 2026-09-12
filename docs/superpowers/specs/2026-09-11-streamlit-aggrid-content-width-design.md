# Streamlit AgGrid Content-Width Column Sizing

## Goal

Make the dataset preview grid size every column wide enough to display its
longest header or cell value, while preserving row selection and allowing
horizontal scrolling when the combined column width exceeds the page.

## Design

The existing `AgGrid` configuration in `streamlit_app.py` will use a
JavaScript grid lifecycle callback that runs after the data has rendered. The
callback will collect all column IDs and call AgGrid's `autoSizeColumns`
method. Running after data rendering ensures sizing includes the actual row
values, not only the grid structure.

The grid will keep `fit_columns_on_grid_load=False`, because fitting columns
to the viewport would conflict with content-width sizing. Unsafe JavaScript
support will remain enabled because `st_aggrid` requires it for the callback.
Selection behavior and the existing grid height will remain unchanged unless
the current working-tree changes already specify otherwise.

## Compatibility and error handling

The callback will use JavaScript syntax and boolean values. No data or
selection behavior will be changed. If the grid is wider than the available
viewport, AgGrid's normal horizontal scrolling will provide access to all
columns.

## Validation

Validate the edited code with the repository's available Python checks and
inspect the final diff. Confirm that the callback is attached to the
post-render event, all columns are passed to `autoSizeColumns`, and the
working-tree changes that predate this task are not overwritten.
