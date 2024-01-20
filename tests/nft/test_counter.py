import ape


def test_initialCount(token, premint):
    count = token.totalSupply()
    assert premint == count


def test_increment(minted, premint):
    assert minted.totalSupply() == 1 + premint


def test_nonzero_owner_index(token):
    with ape.reverts():
        token.tokenOfOwnerByIndex("0x0000000000000000000000000000000000000000", 0)
