import pytest
from brownie import config
from brownie import Contract
from brownie import chain, interface


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture(scope="module")
def gov(accounts):
    yield accounts.at("0xb6bc033D34733329971B938fEf32faD7e98E56aD", force=True)


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture(scope="module")
def rewards(accounts):
    yield accounts.at("0xD20Eb2390e675b000ADb8511F62B28404115A1a4", force=True)


@pytest.fixture(scope="module")
def guardian(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts.at("0xD20Eb2390e675b000ADb8511F62B28404115A1a4", force=True)


@pytest.fixture(scope="module")
def whale(accounts):
    yield accounts.at("0x839De324a1ab773F76a53900D70Ac1B913d2B387", force=True)


@pytest.fixture(scope="module")
def amount():
    amount = 10_000e18
    yield amount


@pytest.fixture(scope="module")
def sorbettiere():
    yield Contract("0x839De324a1ab773F76a53900D70Ac1B913d2B387")


@pytest.fixture(scope="module")
def sorbettiere_owner(accounts):
    yield accounts.at("0xA71A021EF66B03E45E0d85590432DFCfa1b7174C", force=True)


@pytest.fixture(scope="module")
def keeper(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def curve_lp():
    yield Contract("0x30dF229cefa463e991e29D42DB0bae2e122B2AC7")


@pytest.fixture
def token():
    token_address = "0x30dF229cefa463e991e29D42DB0bae2e122B2AC7"  # Mim-2Pool
    yield Contract(token_address)


@pytest.fixture
def farmed():
    yield interface.ERC20("0x3E6648C5a70A150A88bCE65F4aD4d506Fe15d2AF")  # spell

@pytest.fixture
def farmed_whale(accounts):
    yield accounts.at("0x8f93Eaae544e8f5EB077A1e09C1554067d9e2CA8", force=True)

@pytest.fixture
def rando(accounts):
    yield accounts.at("0xB62432fC113d55228c364b567C499146ED6ca83A", force=True)

@pytest.fixture
def weth():
    token_address = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
    yield Contract(token_address)


@pytest.fixture
def weth_amout(user, weth):
    weth_amout = 10 ** weth.decimals()
    user.transfer(weth, weth_amout)
    yield weth_amout


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    chain.sleep(1)
    yield vault


@pytest.fixture(scope="module")
def strategy_name():
    strategy_name = "StrategyCurveSpell"
    yield strategy_name


@pytest.fixture(scope="module")
def pool_id():
    yield 0


@pytest.fixture(scope="module")
def healthCheck():
    yield Contract("0x32059ccE723b4DD15dD5cb2a5187f814e6c470bC")


@pytest.fixture
def strategy(
    strategist,
    keeper,
    vault,
    StrategyCurveSpell,
    gov,
    strategy_name,
    pool_id,
    healthCheck,
):
    strategy = strategist.deploy(StrategyCurveSpell, vault, pool_id, strategy_name)
    strategy.setKeeper(keeper, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    strategy.setHealthCheck(healthCheck, {"from": gov})
    strategy.setDoHealthCheck(True, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    yield strategy


@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    yield 1e-5
