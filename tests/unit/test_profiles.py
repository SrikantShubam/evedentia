from evidentia.tournament.profiles import PROFILES, STRUCTURAL_GATES, required_gates


def test_required_gates_known_profile():
    gates = required_gates("consumer_app")
    assert gates[0] == "parent_market_exists"
    assert "willingness_to_pay" in gates


def test_structural_gate_registry_has_player_fit():
    assert "player_fit" in STRUCTURAL_GATES["consumer_app"]
    assert "player_fit" in STRUCTURAL_GATES["agency_service"]


def test_profiles_present():
    assert set(PROFILES.keys()) == {
        "consumer_app",
        "b2b_workflow",
        "browser_extension",
        "agency_service",
    }
