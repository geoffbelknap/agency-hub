from scripts.review_connector import determine_ask_outcome


def test_connector_with_validation_error_is_ask_fail():
    assert determine_ask_outcome(errors=["bad"], flags=[]) == "ASK-Fail"


def test_high_risk_flag_without_error_is_ask_partial():
    assert determine_ask_outcome(errors=[], flags=["new connector"]) == "ASK-Partial"


def test_clean_change_is_ask_pass():
    assert determine_ask_outcome(errors=[], flags=[]) == "ASK-Pass"
