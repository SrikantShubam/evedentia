from evidentia.deployer import can_deploy


def test_deploy_requires_approval():
    assert can_deploy({"approved": False}) is False


def test_deploy_requires_boolean_approval():
    assert can_deploy({"approved": "false"}) is False
