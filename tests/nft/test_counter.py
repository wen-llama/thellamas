import brownie
from brownie import ZERO_ADDRESS


def test_initialCount(token, premint):
    count = token.totalSupply()
    assert premint == count


def test_increment(minted, premint):
    assert minted.totalSupply() == 1 + premint


def test_nonzero_owner_index(token):
    with brownie.reverts():
        token.tokenOfOwnerByIndex(ZERO_ADDRESS, 0)
