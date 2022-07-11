// SPDX-License-Identifier: MIT

pragma solidity >=0.6.0 <0.8.0;

import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";
import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    uint256 public usdEntryFee;
    uint256 public randomness;
    address payable public recentWinner;
    AggregatorV3Interface internal ethUsdPriceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    uint256 public fee;
    bytes32 public keyHash;
    LOTTERY_STATE public lottery_state;

    event RequestedRandomness(bytes32 requestId);

    constructor(
        address _priceFeed,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeed);
        lottery_state = LOTTERY_STATE.CLOSED; // or we could have said lottery_state = 1 (as 0->OPEN, 1->CLOSED, 2->CALCULATING_WINNER)
        fee = _fee;
        keyHash = _keyHash;
    }

    function enter() public payable {
        // $50 - Minimum
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();

        uint256 adjustedPrice = uint256(price) * 10**10; // 18 Decimals (uint256 already considers for 8 decimals)
        // Today, 1ETH - 1050USD (this value will be received in price variable)
        // 50USD -> 50/1050 ETH
        // Will also need to convert ETH to WEI (adding 18 decimal points)
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery yet!"
        );

        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestId = requestRandomness(keyHash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You are not there yet!"
        );
        require(_randomness > 0, "Random not found!");
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);
        // Reset the lottery!
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
