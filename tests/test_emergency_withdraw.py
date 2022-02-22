import brownie

def test_emergency_withdraw(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    amount,
    strategist
):
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # simulate 1 day of earnings
    chain.sleep(86400)
    chain.mine(1)
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    balance_before = token.balanceOf(strategy)

    strategy.emergencyWithdraw({"from": strategist})

    balance_after = token.balanceOf(strategy)

    assert balance_after > balance_before