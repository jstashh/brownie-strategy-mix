import pytest


def test_base_strategy(
    gov,
    strategy,
    chain
):
    # we've harvested immediately after the strategy was deployed so the trigger should be false
    assert strategy.harvestTrigger(0, {"from": gov}) == False

    # fast forward so our min delay is passed
    chain.sleep(86400 * 4)
    chain.mine(1)

    # we're past the min delay now so should be able to harvest
    assert strategy.harvestTrigger(0, {"from": gov}) == True

    strategy.harvest({"from": gov})

    # we've just harvested so we shouldn't be able to do so again until the min delay is passed
    assert strategy.harvestTrigger(0, {"from": gov}) == False

    # test all of our random shit
    strategy.doHealthCheck()
    strategy.healthCheck()
    strategy.apiVersion()
    strategy.name()
    strategy.delegatedAssets()
    strategy.vault()
    strategy.strategist()
    strategy.rewards()
    strategy.keeper()
    strategy.want()
    strategy.minReportDelay()
    strategy.maxReportDelay()
    strategy.profitFactor()
    strategy.debtThreshold()
    strategy.emergencyExit()
