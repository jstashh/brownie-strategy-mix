import pytest
from brownie import chain

def test_deposit(vault, token, strategy, whale, amount, gov, keeper, curve_lp, sorbettiere, sorbettiere_owner):
    sorbettiere.changeEndTime(8640000, {"from": sorbettiere_owner})
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 -1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    old_assets = vault.totalAssets()

    chain.sleep(86400 * 5)
    chain.mine(1)

    chain.sleep(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    
    harvest_event = tx.events["Harvested"]
    assert harvest_event["profit"] > 0
    assert harvest_event["loss"] == 0
    assert harvest_event["debtPayment"] == 0
    assert harvest_event["debtOutstanding"] == 0

    assert strategy.pendingRewards() == 0
    new_assets = vault.totalAssets()
    assert new_assets >= old_assets
    # print(new_assets - old_assets)

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    vault.withdraw({"from": whale})
    end_whale = token.balanceOf(whale)
    assert end_whale > starting_whale
    # print(end_whale - starting_whale)
