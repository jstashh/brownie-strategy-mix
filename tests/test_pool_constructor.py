import brownie


def test_constructing_with_wrong_pool_reverts(StrategyCurveSpell, vault, strategy_name, strategist):
    invalid_pool_id = 1
    with brownie.reverts():     
        strategist.deploy(StrategyCurveSpell, vault, invalid_pool_id, strategy_name)