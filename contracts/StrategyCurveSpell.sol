// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";

import "./interfaces/curve.sol";
import "./interfaces/yearn.sol";
import "./interfaces/sorbettiere.sol";
import {IUniswapV2Router02} from "./interfaces/uniswap.sol";
import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";

contract StrategyCurveSpell is BaseStrategy {
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */
    // these will likely change across different wants.

    // the rewards contract we deposit into and harvest SPELL from
    ISorbettiere internal constant sorbettiere =
        ISorbettiere(0x839De324a1ab773F76a53900D70Ac1B913d2B387);

    // used as the intermediary for selling spell into an underlying token of the curve pool
    IERC20 internal constant weth =
        IERC20(0x82aF49447D8a07e3bd95BD0d56f35241523fBab1);

    // we use these to deposit to our curve pool
    IERC20 internal constant mim =
        IERC20(0xFEa7a6a0B346362BF88A9e4A88416B77a57D6c2A);
    IERC20 internal constant usdt =
        IERC20(0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9);
    IERC20 internal constant usdc =
        IERC20(0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8);

    IERC20 internal constant spell =
        IERC20(0x3E6648C5a70A150A88bCE65F4aD4d506Fe15d2AF);
    IUniswapV2Router02 public router =
        IUniswapV2Router02(0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506); // sushi router
    ICurveZap public curveZapIn =
        ICurveZap(0x7544Fe3d184b6B55D6B36c3FCA1157eE0Ba30287);

    address public targetToken; // this is the token we sell into - MIM, USDC, or usdt
    bool public forceHarvestTriggerOnce; // only set this to true externally when we want to trigger our keepers to harvest for us
    bool public withdrawStakedOnMigration = true; // set to true to withdraw the deposited lp tokens before migration
    bool public shouldSellSpell = true; // set to true to sell any farmed spell

    uint256 internal poolId; // the pool we are depositing into in the rewards contract
    string internal stratName; // set our strategy name here

    /* ========== CONSTRUCTOR ========== */

    constructor(
        address _vault,
        uint256 _poolId,
        string memory _name
    ) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        maxReportDelay = 2 days; // 2 days in seconds
        healthCheck = 0x32059ccE723b4DD15dD5cb2a5187f814e6c470bC;

        // these are our standard approvals. want = Curve LP token
        want.approve(address(sorbettiere), type(uint256).max);

        spell.approve(address(router), type(uint256).max);

        // set our strategy's name
        stratName = _name;

        // set the pool id that we'll use in the rewards contract to deposit into
        address stakingToken = sorbettiere.poolInfo(_poolId).stakingToken;
        require(stakingToken == address(want), "wrong pool");
        poolId = _poolId;

        // these are our approvals and path specific to this contract
        mim.approve(address(curveZapIn), type(uint256).max);
        usdc.approve(address(curveZapIn), type(uint256).max);
        usdt.safeApprove(address(curveZapIn), type(uint256).max);

        // start off with mim
        targetToken = address(mim);
    }

    function name() external view override returns (string memory) {
        return stratName;
    }

    /* ========== MUTATIVE FUNCTIONS ========== */
    // these will likely change across different wants.

    ///@notice Only do this if absolutely necessary; as assets will be withdrawn but rewards won't be claimed.
    function emergencyWithdraw() external onlyEmergencyAuthorized {
        sorbettiere.emergencyWithdraw(poolId);
    }

    function prepareMigration(address _newStrategy) internal override {
        if (withdrawStakedOnMigration) {
            uint256 _stakedBal = stakedBalance();
            if (_stakedBal > 0) {
                sorbettiere.withdraw(poolId, _stakedBal);
            }
        }

        uint256 _spellBalance = spell.balanceOf(address(this));
        if (_spellBalance > 0) {
            spell.safeTransfer(_newStrategy, _spellBalance);
        }
    }

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}

    // This allows us to manually harvest with our keeper as needed
    function setWithdrawStakedOnMigration(bool _withdrawStakedOnMigration)
        external
        onlyEmergencyAuthorized
    {
        withdrawStakedOnMigration = _withdrawStakedOnMigration;
    }

    function setForceHarvestTriggerOnce(bool _forceHarvestTriggerOnce)
        external
        onlyEmergencyAuthorized
    {
        forceHarvestTriggerOnce = _forceHarvestTriggerOnce;
    }

    function setShouldSellSpell(bool _shouldSellSpell)
        external
        onlyEmergencyAuthorized
    {
        shouldSellSpell = _shouldSellSpell;
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        if (emergencyExit) {
            return;
        }

        // Send all of our LP tokens to deposit to the gauge if we have any
        uint256 _toInvest = balanceOfWant();
        if (_toInvest > 0) {
            sorbettiere.deposit(poolId, _toInvest);
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 _wantBal = balanceOfWant();
        if (_amountNeeded > _wantBal) {
            // check if we have enough free funds to cover the withdrawal
            uint256 _stakedBal = stakedBalance();
            if (_stakedBal > 0) {
                sorbettiere.withdraw(
                    poolId,
                    Math.min(_stakedBal, _amountNeeded.sub(_wantBal))
                );
            }

            uint256 _withdrawnBal = balanceOfWant();
            _liquidatedAmount = Math.min(_amountNeeded, _withdrawnBal);
            _loss = _amountNeeded.sub(_liquidatedAmount);
        } else {
            // we have enough balance to cover the liquidation available
            return (_amountNeeded, 0);
        }
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // harvest our rewards from the staking contract
        sorbettiere.withdraw(poolId, 0);

        if (shouldSellSpell) {
            uint256 spellBalance = spell.balanceOf(address(this));
            // sell SPELL if we have any
            if (spellBalance > 0) {
                _sellSpell(spellBalance);
            }
        }

        uint256 mimBalance = mim.balanceOf(address(this));
        uint256 usdtBalance = usdt.balanceOf(address(this));
        uint256 usdcBalance = usdc.balanceOf(address(this));

        // deposit our balance to Curve if we have any
        if (mimBalance > 0 || usdcBalance > 0 || usdtBalance > 0) {
            curveZapIn.add_liquidity(
                address(want),
                [mimBalance, usdcBalance, usdtBalance],
                0
            );
        }

        // debtOustanding will only be > 0 in the event of revoking or if we need to rebalance from a withdrawal or lowering the debtRatio
        uint256 stakedBal = stakedBalance();
        if (_debtOutstanding > 0) {
            // don't bother withdrawing if we don't have staked funds
            if (stakedBal > 0) {
                sorbettiere.withdraw(
                    poolId,
                    Math.min(stakedBal, _debtOutstanding)
                );
            }
            uint256 _withdrawnBal = balanceOfWant();
            _debtPayment = Math.min(_debtOutstanding, _withdrawnBal);
        }

        // serious loss should never happen, but if it does (for instance, if Curve is hacked), let's record it accurately
        uint256 assets = estimatedTotalAssets();
        uint256 debt = vault.strategies(address(this)).totalDebt;

        // if assets are greater than debt, things are working great!
        if (assets > debt) {
            _profit = assets.sub(debt);
            uint256 _wantBal = balanceOfWant();
            if (_profit.add(_debtPayment) > _wantBal) {
                // this should only be hit following donations to strategy
                uint256 _toLiquidate = _profit.add(_debtPayment);
                liquidatePosition(_toLiquidate);
            }
        }
        // if assets are less than debt, we are in trouble
        else {
            _loss = debt.sub(assets);
        }

        // we're done harvesting, so reset our trigger if we used it
        forceHarvestTriggerOnce = false;
    }

    function stakedBalance() public view returns (uint256) {
        return sorbettiere.userInfo(poolId, address(this)).amount;
    }

    function pendingRewards() public view returns (uint256) {
        return sorbettiere.pendingIce(poolId, address(this));
    }

    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return balanceOfWant().add(stakedBalance());
    }

    // fire sale, get rid of it all!
    function liquidateAllPositions() internal override returns (uint256) {
        uint256 _stakedBal = stakedBalance();
        // don't bother withdrawing zero
        if (_stakedBal > 0) {
            sorbettiere.withdraw(poolId, _stakedBal);
        }

        return balanceOfWant();
    }

    function manualSell(uint256 _amount) external onlyEmergencyAuthorized {
        _sellSpell(_amount);
    }

    // Sells our SPELL for our target token
    function _sellSpell(uint256 _amount) internal {
        address[] memory path = new address[](3);
        path[0] = address(spell);
        path[1] = address(weth);
        path[2] = address(targetToken);
        router.swapExactTokensForTokens(
            _amount,
            uint256(0),
            path,
            address(this),
            block.timestamp
        );
    }

    /* ========== KEEP3RS ========== */

    function harvestTrigger(uint256 callCostinEth)
        public
        view
        override
        returns (bool)
    {
        StrategyParams memory params = vault.strategies(address(this));

        // harvest no matter what once we reach our maxDelay
        if (block.timestamp.sub(params.lastReport) > maxReportDelay) {
            return true;
        }

        // trigger if we want to manually harvest
        if (forceHarvestTriggerOnce) {
            return true;
        }

        // otherwise, we don't harvest
        return false;
    }

    // convert our keeper's eth cost into want, we don't need this anymore since we don't use baseStrategy harvestTrigger
    function ethToWant(uint256 _ethAmount)
        public
        view
        override
        returns (uint256)
    {
        return _ethAmount;
    }

    /* ========== SETTERS ========== */

    // These functions are useful for setting parameters of the strategy that may need to be adjusted.
    // Set optimal token to sell harvested funds for depositing to Curve.
    // Default is MIM, but can be set to USDC or usdt as needed by strategist or governance.
    function setOptimal(uint256 _optimal) external onlyEmergencyAuthorized {
        if (_optimal == 0) {
            targetToken = address(mim);
        } else if (_optimal == 1) {
            targetToken = address(usdc);
        } else if (_optimal == 2) {
            targetToken = address(usdt);
        } else {
            revert("incorrect token");
        }
    }
}
