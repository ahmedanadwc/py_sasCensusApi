import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import saspy
    from py_sascensusapi.config import DEFAULT_SAS_CFGFILE

    return DEFAULT_SAS_CFGFILE, mo, saspy


@app.cell
def _(DEFAULT_SAS_CFGFILE, saspy):
    kwargs = {"cfgname": "oda"}
    if DEFAULT_SAS_CFGFILE:
        kwargs["cfgfile"] = DEFAULT_SAS_CFGFILE
    sas = saspy.SASsession(**kwargs)
    return (sas,)


@app.cell
def _(sas):
    sas.endsas()
    return


if __name__ == "__main__":
    app.run()
