from brownie import network, exceptions
from web3 import Web3
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENT, get_account, fund_with_link, get_contract
import pytest

# def test_get_entrance_fee():
#     account = accounts[0]
#     lottery = Lottery.deploy(
#         config["networks"][network.show_active()]["eth_usd_price_feed"], {"from": account})
#     assert lottery.getEntranceFee() > Web3.toWei(0.046, "ether")
#     assert lottery.getEntranceFee() < Web3.toWei(0.05, "ether")
#     # 50USD ~ 0.047ETH


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENT:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # Price - 1050 ETH -> 1 USD
    # usdEntryFee -> $50 -> 50/1050 ~ 0.047ETH
    expected_entrance_fee = Web3.toWei(0.047, "ether")
    entrance_fee = lottery.getEntranceFee()
    # Assert
    assert expected_entrance_fee <= entrance_fee


def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENT:
        pytest.skip()

    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter(
            {"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENT:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # Act
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENT:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Act
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # Assert
    assert lottery.lottery_state() == 2


def test_can_pick_winner_properly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENT:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1),
                  "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2),
                  "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account})
    # Result will be - 777 % 3 = 0 ->account[0]
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
