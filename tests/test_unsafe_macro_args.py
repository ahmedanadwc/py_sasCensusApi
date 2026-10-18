from py_sascensusapi.sas_backend import find_unsafe_macro_args

ZCTA_FOR = "for=zip code tabulation area (3 digit) (or part):*"


def test_parens_rejected_by_default():
    assert find_unsafe_macro_args({"p_apiForClause": ZCTA_FOR}) == ["p_apiForClause"]


def test_balanced_parens_allowed_for_paren_ok_fields():
    fields = {"p_apiForClause": ZCTA_FOR, "p_apiInClause": "in=state:09,23"}
    assert find_unsafe_macro_args(fields, paren_ok=("p_apiForClause", "p_apiInClause")) == []


def test_unbalanced_parens_rejected_even_when_paren_ok():
    fields = {"a": "for=x(", "b": "for=x)(", "c": "for=(x"}
    assert find_unsafe_macro_args(fields, paren_ok=("a", "b", "c")) == ["a", "b", "c"]


def test_other_unsafe_chars_rejected_even_when_paren_ok():
    fields = {"a": "x(1);", "b": "100%", "c": "it's", "d": "x\ny"}
    assert find_unsafe_macro_args(fields, paren_ok=tuple(fields)) == ["a", "b", "c", "d"]


def test_paren_ok_does_not_relax_other_fields():
    fields = {"p_apiForClause": ZCTA_FOR, "p_apiGetClause": "get=NAME(x)"}
    assert find_unsafe_macro_args(fields, paren_ok=("p_apiForClause",)) == ["p_apiGetClause"]
