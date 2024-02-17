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
    premint_addresses = [preminter] * 20
    token = deployer.deploy(
        project.Larp,
        bytes.fromhex("280de2361f686a08d02f92298994a01c99ab3a8c2cbf73527bac21f0e65a85b4"),
        bytes.fromhex("bb1eaedfd924a774eb5a2bd4a01b496ccf8d77cca63af85cdc50ae2a54e4acb3"),
        premint_addresses
    )
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
    token.allowlistMint(
        [
            bytes.fromhex("4de6f61ec539f1dbbe42f2f8f0fabac58ac41b3e72f040a7f0fdb47a72896bd8"),
            bytes.fromhex("e0c0488cf2ec5e3f095200be58101d8a14cb8dd50487d7707dbd6c3756c35675"),
            bytes.fromhex("3ca892a7fc01fdf94e036ea38339a6811167ab843d780c8dc9bf7860379da568")
        ],
        sender=alice,
        value="0.1 ether",
        gas_limit=int(1e8)
    )

    return token


@pytest.fixture(scope="function")
def wl_minted(token, alice, deployer):
    token.start_wl_mint(sender=deployer)
    token.whitelistMint(
        [
            bytes.fromhex("01d406d4747bd12193a48c0e49c2d4f64e82b88d62e90f5ffbcec6c3cd853951"),
            bytes.fromhex("dde94d9c8f562df87d019849933c6f4c5588f278e731af5dda4a3fe0208f74d6"),
            bytes.fromhex("40cf18ab9bd51f9d58054254246f31fd04090cac179cd40780c17de8706572be"),
            bytes.fromhex("02c541d566951c2470a31dcfd33617d8048956b9241fe2202ac2df867bd69f33"),
            bytes.fromhex("038657d4f4bcc47bbd18ba0d36183cc5b533b5d459a9043eacc9edd542f2dff0"),
            bytes.fromhex("329572f27f6cb8520d730695735833ece47bf0d0d6e759b778ef8c05b34f70de"),
            bytes.fromhex("c58cb8c5f0fa318ebc4e0e145102da447d654314514927170c3a85d7e16ed58b"),
            bytes.fromhex("5ebdddf044b8fa76cada5612e61d1eef0003c4060040d5423b504f6d511d141b")
        ],
        sender=alice,
        value="0.3 ether",
        gas_limit=int(1e8)
    )

    return token


# If there is a minter contract separate from the NFT, deploy here
@pytest.fixture(scope="function")
def minter(token):
    return token


# CONSTANTS


@pytest.fixture(scope="function")
def minted_token_id():
    return 0


# If there is a premint, hardcode the number of tokens preminted here for tests
@pytest.fixture(scope="function")
def premint():
    return 20


@pytest.fixture(scope="function")
def token_metadata():
    return {"name": "LARP Collective", "symbol": "LARP"}
