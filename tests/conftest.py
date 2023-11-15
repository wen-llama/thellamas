#!/usr/bin/python3

import pytest
from brownie import ERC721TokenReceiverImplementation, accounts, web3
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="function")
def token(Llama, deployer, preminter):
    premint_addresses = [preminter] * 20
    token = Llama.deploy(premint_addresses, {"from": deployer})
    return token


@pytest.fixture(scope="function")
def token_minted(token, deployer):
    token.mint(deployer)
    return token


@pytest.fixture(scope="function")
def deployer():
    return accounts.add()


@pytest.fixture(scope="function")
def split_recipient():
    return accounts.add()


@pytest.fixture(scope="function")
def smart_contract_owner(BasicSafe, accounts):
    return BasicSafe.deploy({"from": accounts[0]})


@pytest.fixture(scope="function")
def alice():
    return accounts[1]


@pytest.fixture(scope="function")
def bob():
    return accounts[2]


@pytest.fixture(scope="function")
def charlie():
    return accounts[3]


@pytest.fixture(scope="function")
def preminter():
    return accounts[4]


@pytest.fixture(scope="function")
def minted(token):
    token.mint()
    return token


@pytest.fixture(scope="function")
def al_minted(token, alice, deployer):
    token.start_al_mint()
    # Sign a message from the wl_signer for alice
    alice_encoded = encode(["string", "address", "uint256"], ["allowlist:", alice.address, 1])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    token.allowlistMint(
        1, 1, signed_message.signature, {"from": alice, "value": web3.toWei(0.1, "ether")}
    )

    return token


@pytest.fixture(scope="function")
def minted_token_id():
    return 20


# If there is a minter contract separate from the NFT, deploy here
@pytest.fixture(scope="function")
def minter(token):
    return token


# If there is a premint, hardcode the number of tokens preminted here for tests
@pytest.fixture(scope="function")
def premint():
    return 20


@pytest.fixture(scope="function")
def token_metadata():
    return {"name": "The Llamas", "symbol": "LLAMA"}


@pytest.fixture(scope="function")
def tokenReceiver(deployer):
    return ERC721TokenReceiverImplementation.deploy({"from": deployer})


@pytest.fixture(scope="function")
def auction_house(LlamaAuctionHouse, token, deployer, split_recipient):
    auction_house = LlamaAuctionHouse.deploy(token, 100, 100, 5, 100, split_recipient.address, 5, {"from": deployer})
    auction_house.set_auction_order([20,21,22])
    return auction_house


@pytest.fixture(scope="function")
def auction_house_unpaused(LlamaAuctionHouse, token, deployer, split_recipient):
    auction_house = LlamaAuctionHouse.deploy(token, 100, 100, 5, 100, split_recipient.address, 5, {"from": deployer})
    auction_house.set_auction_order([20,21,22,23])
    token.set_minter(auction_house)
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    auction_house.unpause()
    return auction_house


@pytest.fixture(scope="function")
def auction_house_unpaused_all_split(LlamaAuctionHouse, token, deployer, split_recipient):
    auction_house = LlamaAuctionHouse.deploy(token, 100, 100, 5, 100, split_recipient.address, 100, {"from": deployer})
    auction_house.set_auction_order([20,21,22,23])
    token.set_minter(auction_house)
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    auction_house.unpause()
    return auction_house


@pytest.fixture(scope="function")
def auction_house_unpaused_no_split(LlamaAuctionHouse, token, deployer, split_recipient):
    auction_house = LlamaAuctionHouse.deploy(token, 100, 100, 5, 100, split_recipient.address, 0, {"from": deployer})
    auction_house.set_auction_order([20,21,22,23])
    token.set_minter(auction_house)
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    auction_house.unpause()
    return auction_house


@pytest.fixture(scope="function")
def auction_house_sc_owner(LlamaAuctionHouse, token, deployer, smart_contract_owner, split_recipient):
    auction_house = LlamaAuctionHouse.deploy(token, 100, 100, 5, 100, split_recipient.address, 5, {"from": deployer})
    auction_house.set_auction_order([20,21,22])
    token.set_minter(auction_house)
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    token.mint({"from": auction_house})
    auction_house.unpause()
    auction_house.disable_wl()
    auction_house.set_owner(smart_contract_owner, {"from": deployer})
    return auction_house
