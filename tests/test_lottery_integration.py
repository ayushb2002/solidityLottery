import time
import pytest
from brownie import network
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENT, fund_with_link, get_account


def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENT:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    time.sleep(300)
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
