import ape
import pytest

def test_tokenOfOwnerByIndex_accurate(minted, deployer, minted_token_id, bob):
    # check deployer owns the specified NFT as his first
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id

    # check bob doesn't own, transfer it to Bob, and check he owns as first
    # and deployer doesn't
    with ape.reverts():
        minted.tokenOfOwnerByIndex(bob, 0)
    minted.transferFrom(deployer, bob, minted_token_id, sender=deployer)
    assert minted.tokenOfOwnerByIndex(bob, 0) == minted_token_id
    with ape.reverts():
        minted.tokenOfOwnerByIndex(deployer, 0)

    # mint two more and now check deployer owns them as first two
    minted.mint(sender=deployer)
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id + 1
    minted.mint(sender=deployer)
    assert minted.tokenOfOwnerByIndex(deployer, 1) == minted_token_id + 2
    # transfer first owned to bob
    minted.transferFrom(deployer, bob, minted_token_id + 1, sender=deployer)
    assert minted.ownerOf(minted_token_id + 1) == bob
    assert minted.ownerOf(minted_token_id + 2) == deployer
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id + 2

    minted.mint(sender=deployer)
    minted.mint(sender=deployer)
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id + 2
    assert minted.tokenOfOwnerByIndex(deployer, 1) == minted_token_id + 3
    assert minted.tokenOfOwnerByIndex(deployer, 2) == minted_token_id + 4

    minted.transferFrom(deployer, bob, minted_token_id + 3, sender=deployer)
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id + 2
    assert minted.tokenOfOwnerByIndex(deployer, 1) == minted_token_id + 4
    with ape.reverts():
        assert minted.tokenOfOwnerByIndex(deployer, 2)


def test_tokensForOwner(minted, deployer, minted_token_id, bob):
    assert minted.tokensForOwner(deployer) == [minted_token_id]
    minted.mint(sender=deployer)
    assert minted.tokensForOwner(deployer) == [minted_token_id, minted_token_id + 1]

    minted.transferFrom(deployer, bob, minted_token_id, sender=deployer)
    assert minted.tokensForOwner(deployer) == [minted_token_id + 1]
    assert minted.tokensForOwner(bob) == [minted_token_id]
