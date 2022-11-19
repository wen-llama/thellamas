#!/usr/bin/python3

import pytest
from brownie import (
    Llama,
    ERC721TokenReceiverImplementation,
    accounts
)


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def token(Llama, deployer):
    token = Llama.deploy({"from": deployer})
    return token


@pytest.fixture(scope="module")
def token_minted(token, deployer):
    token.mint(deployer)
    return token


@pytest.fixture(scope="module")
def deployer():
    return accounts[0]


@pytest.fixture(scope="module")
def alice():
    return accounts[1]


@pytest.fixture(scope="module")
def bob():
    return accounts[2]


@pytest.fixture(scope="module")
def charlie():
    return accounts[3]


@pytest.fixture(scope="module")
def minted(token, alice):
    token.mint(alice)
    return token


@pytest.fixture(scope="module")
def minted_token_id():
    return 0



# If there is a minter contract separate from the NFT, deploy here
@pytest.fixture(scope="module")
def minter(token):
    return token

# If there is a premint, hardcode the number of tokens preminted here for tests
@pytest.fixture(scope="module")
def premint():
    return 0


@pytest.fixture(scope="module")
def token_metadata():
    return {"name": "The Llamas", "symbol": "LLAMA"}


@pytest.fixture(scope="module")
def tokenReceiver(deployer):
    return ERC721TokenReceiverImplementation.deploy({"from": deployer})
