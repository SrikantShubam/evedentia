from evidentia.cli import _is_narrower_cohort


def test_is_narrower_cohort_true_when_child_adds_constraints():
    assert _is_narrower_cohort("small agencies", "small agencies with compliance-heavy finance workflows") is True


def test_is_narrower_cohort_false_when_not_subset_or_equal():
    assert _is_narrower_cohort("small agencies", "enterprise teams") is False
    assert _is_narrower_cohort("small agencies", "small agencies") is False
