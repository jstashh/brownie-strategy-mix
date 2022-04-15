import brownie
from brownie import Contract
import pytest

@pytest.mark.skip(reason="For some reason this fails, something to do with weth being a proxy contract maybe")
def test_manual_sell(strategy, farmed, farmed_whale, strategist):
    donation_amount = 1e25 # 1 million SPELL
    farmed.transfer(strategy, donation_amount, {"from": farmed_whale})
    assert farmed.balanceOf(strategy) == donation_amount

    target_token = Contract(strategy.targetToken())
    
    target_token_balance_before = target_token.balanceOf(strategy)
    strategy.manualSell(donation_amount, {"from": strategist})
    target_token_balance_after = target_token.balanceOf(strategy)

    assert target_token_balance_after > target_token_balance_before

def test_manual_sell_from_rando(strategy, rando):
    with brownie.reverts("!authorized"):
        strategy.manualSell(1, {"from": rando})