from evidentia.cli import approve_spec


def test_build_is_blocked_without_approval():
    assert approve_spec({"approved": False}) is False


def test_build_is_blocked_for_string_approval_values():
    assert approve_spec({"approved": "false"}) is False
