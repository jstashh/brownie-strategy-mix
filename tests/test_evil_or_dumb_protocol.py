import brownie
from brownie import Contract
from brownie import config
import math


def test_protocol_drains_balance(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    amount,
    sorbettiere,
    farmed,
):
    ## deposit to the vault after approving.
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # send away all funds from the sorbettiere itself
    to_send = farmed.balanceOf(sorbettiere)
    print("Balance of Vault", to_send)
    farmed.transfer(gov, to_send, {"from": sorbettiere})
    assert farmed.balanceOf(sorbettiere) == 0
    assert vault.strategies(strategy)[2] == 10000

    # turn off health check since we're doing weird shit
    strategy.setDoHealthCheck(False, {"from": gov})

    # revoke the strategy to get our funds back out
    vault.revokeStrategy(strategy, {"from": gov})
    chain.sleep(1)
    tx_1 = strategy.harvest({"from": gov})
    chain.sleep(1)
    print("\nThis was our vault report:", tx_1.events["Harvested"])

    # we can also withdraw from an empty vault as well
    tx = vault.withdraw(amount, whale, 10000, {"from": whale})
    endingWhale = token.balanceOf(whale)
    print(
        "This is how much our whale lost:",
        (startingWhale - endingWhale) / (10 ** token.decimals()),
    )


def test_protocol_half_rekt(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    amount,
    sorbettiere,
    farmed,
):
    ## deposit to the vault after approving.
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # send away all funds from the sorbettiere itself
    to_send = farmed.balanceOf(sorbettiere) / 2
    starting_chef = farmed.balanceOf(sorbettiere)
    print("Balance of Vault", to_send)
    farmed.transfer(gov, to_send, {"from": sorbettiere})
    assert farmed.balanceOf(sorbettiere) < starting_chef

    # turn off health check since we're doing weird shit
    strategy.setDoHealthCheck(False, {"from": gov})

    # revoke the strategy to get our funds back out
    vault.revokeStrategy(strategy, {"from": gov})
    chain.sleep(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    print("\nThis was our vault report:", tx.events["Harvested"])

    # we can also withdraw from an empty vault as well
    vault.withdraw(amount, whale, 10000, {"from": whale})
    endingWhale = token.balanceOf(whale)
    print(
        "This is how much our whale lost:",
        (startingWhale - endingWhale) / (10 ** token.decimals()),
    )


def test_withdraw_when_done_rewards_over(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    amount,
):
    ## deposit to the vault after approving.
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # turn off health check since we're doing weird shit
    strategy.setDoHealthCheck(False, {"from": gov})

    # normal operation
    chain.sleep(60 * 86400)
    chain.mine(1)
    tx_1 = strategy.harvest({"from": gov})
    chain.sleep(86400)
    chain.mine(1)

    # check if we can still withdraw normally if this happened, let's revoke
    vault.revokeStrategy(strategy, {"from": gov})
    chain.sleep(1)
    tx_2 = strategy.harvest({"from": gov})
    chain.sleep(1)
    print("\nThis was our vault report:", tx_2.events["Harvested"])

    # we can also withdraw from an empty vault as well
    vault.withdraw({"from": whale})