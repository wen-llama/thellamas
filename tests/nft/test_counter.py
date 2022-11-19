import brownie
import pytest
from brownie import ZERO_ADDRESS, accounts, exceptions


#
# Inquire initial count
#
def test_initialCount(token, premint):
    count = token.totalSupply()
    assert premint == count


#
# Test increment
#

def test_increment(minted, premint):
    assert minted.totalSupply() == 1 + premint


def test_nonzero_owner_index(token):
    with brownie.reverts():
        token.tokenOfOwnerByIndex(ZERO_ADDRESS, 0)
