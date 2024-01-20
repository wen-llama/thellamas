#!/usr/bin/python3

import pytest
from ape import Contract, accounts, project
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak


# ACCOUNTS


@pytest.fixture(scope="function")
def smart_contract_owner(deployer, project):
    return deployer.deploy(project.BasicSafe)


@pytest.fixture(scope="function")
def deployer(accounts):
    return accounts[0]


@pytest.fixture(scope="function")
def alice(accounts):
    return accounts[1]


@pytest.fixture(scope="function")
def bob(accounts):
    return accounts[2]


@pytest.fixture(scope="function")
def charlie(accounts):
    return accounts[3]


@pytest.fixture(scope="function")
def preminter(accounts):
    return accounts[4]


@pytest.fixture(scope="function")
def split_recipient(accounts):
    return accounts.generate_test_account()


# CONTRACTS


@pytest.fixture(scope="function")
def token(deployer, project, preminter):
    premint_addresses = [preminter] * 40
    token = deployer.deploy(project.Larp, premint_addresses)
    return token


@pytest.fixture(scope="function")
def tokenReceiver(deployer, project):
    return deployer.deploy(project.ERC721TokenReceiverImplementation)


@pytest.fixture(scope="function")
def auction_house(deployer, project, token, split_recipient):
    auction_house = deployer.deploy(
        project.LlamaAuctionHouse, token, 100, 100, 5, 100, split_recipient.address, 95
    )
    return auction_house


@pytest.fixture(scope="function")
def auction_house_unpaused(deployer, project, token, split_recipient):
    auction_house = deployer.deploy(
        project.LlamaAuctionHouse, token, 100, 100, 5, 100, split_recipient.address, 95, sender=deployer
    )
    token.set_minter(auction_house, sender=deployer)
    auction_house.unpause(sender=deployer)
    return auction_house


@pytest.fixture(scope="function")
def auction_house_sc_owner(
    deployer, project, token, smart_contract_owner, split_recipient
):
    auction_house = deployer.deploy(
        project.LlamaAuctionHouse, token, 100, 100, 5, 100, split_recipient.address, 95, sender=deployer
    )
    token.set_minter(auction_house, sender=deployer)
    auction_house.unpause(sender=deployer)
    auction_house.set_owner(smart_contract_owner, sender=deployer)
    return auction_house


# NFTs

@pytest.fixture(scope="function")
def token_minted(token, deployer):
    token.mint(deployer)
    return token


@pytest.fixture(scope="function")
def minted(token, deployer):
    token.mint(sender=deployer)
    return token


@pytest.fixture(scope="function")
def al_minted(token, alice, deployer):
    token.start_al_mint(sender=deployer)
    # Sign a message from the wl_signer for alice
    alice_encoded = encode(["string", "address", "uint256"], ["allowlist:", alice.address, 1])
    alice_hashed = keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    token.allowlistMint(
        1, 1, signed_message.signature, sender=alice, value="0.1 ether"
    )

    return token


@pytest.fixture(scope="function")
def wl_minted(token, alice, deployer):
    token.start_wl_mint(sender=deployer)
    # Sign a message from the wl_signer for alice
    alice_encoded = encode(["string", "address", "uint256"], ["whitelist:", alice.address, 1])
    alice_hashed = keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    token.whitelistMint(
        1, 1, signed_message.signature, sender=alice, value="0.3 ether"
    )

    return token


# If there is a minter contract separate from the NFT, deploy here
@pytest.fixture(scope="function")
def minter(token):
    return token


# CONSTANTS


@pytest.fixture(scope="function")
def minted_token_id():
    return 40


# If there is a premint, hardcode the number of tokens preminted here for tests
@pytest.fixture(scope="function")
def premint():
    return 40


@pytest.fixture(scope="function")
def token_metadata():
    return {"name": "LARP Collective", "symbol": "LARP"}
