import pytest
from brownie import config
from brownie import Contract
from brownie import chain

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

@pytest.fixture(scope="module")
def gov(accounts):
    yield accounts.at("0x72a34AbafAB09b15E7191822A679f28E067C4a16", force=True)


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture(scope="module")
def rewards(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def guardian(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def whale(accounts):
    yield accounts.at("0x73c18D7CA84afc41863b32085ecEFaE4bAC9DF3d", force=True)


@pytest.fixture(scope="module")
def amount():
    amount = 10_000e18
    yield amount

@pytest.fixture(scope="module")
def sorbettiere():
    yield Contract("0x37Cf490255082ee50845EA4Ff783Eb9b6D1622ce")

@pytest.fixture(scope="module")
def sorbettiere_owner(accounts):
    yield accounts.at("0x65960B6744Ec1873a38189C98A2802E21BE45e0A", force=True)


@pytest.fixture(scope="module")
def keeper(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def curve_lp(accounts):
    yield Contract("0x2dd7C9371965472E5A5fD28fbE165007c61439E1")


@pytest.fixture
def token():
    token_address = "0x2dd7C9371965472E5A5fD28fbE165007c61439E1" # Mim-2Pool
    yield Contract(token_address)

@pytest.fixture
def farmed():
    yield Contract("0x468003B688943977e6130F4F68F23aad939a1040") # spell


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
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
    yield Contract("0xf13Cd6887C62B5beC145e30c38c4938c5E627fe0")

@pytest.fixture
def strategy(strategist, keeper, vault, StrategyCurveSpell, gov, strategy_name, pool_id, healthCheck):
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
