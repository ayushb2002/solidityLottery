from brownie import accounts, network, config, MockV3Aggregator, Contract, VRFCoordinatorMock, LinkToken, interface

LOCAL_BLOCKCHAIN_ENVIRONMENT = ["development", "ganache-local"]
FORKED_LOCAL_ENVIRONMENT = ["mainnet-fork", "mainnet-fork-dev"]
DECIMALS = 8
INITIAL_VALUE = 1050 * (10**8)


def get_account(index=None, id=None):

    if index:
        return accounts[index]

    if id:
        return accounts.load(id)

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENT or network.show_active() in FORKED_LOCAL_ENVIRONMENT:
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken
}


def get_contract(contract_name):
    """
    This function will grab the contract addresses from the brownie config
    if defined, otherwise, it will deploy a mock version of that contract, and
    return that mock contract.
        Args:
            contract_name (string)
        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            version of this contract.
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENT:
        if len(contract_type) <= 0:
            # MockV3Aggregator.length
            deploy_mocks()
        contract = contract_type[-1]
        # MockV3Aggregator[-1]
    else:
        contract_address = config["networks"][network.show_active(
        )][contract_name]
        # address
        # ABI
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        # MockV3Aggregator.abi
    return contract


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Deployed!")


def fund_with_link(contract_address, account=None, link_token=None, amount=0.25*(10**18)):  # 0.25 Link
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(
    #     contract_address, amount, {"from": account})
    tx.wait(1)
    print("Funded Contract!")
    return tx
