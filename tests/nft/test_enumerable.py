import brownie


def test_tokenOfOwnerByIndex_accurate(minted, deployer, minted_token_id, bob):
    # check deployer owns the specified NFT as his first
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id

    # check bob doesn't own, transfer it to Bob, and check he owns as first
    # and deployer doesn't
    with brownie.reverts():
        minted.tokenOfOwnerByIndex(bob, 0)
    minted.transferFrom(deployer, bob, minted_token_id, {"from": deployer})
    assert minted.tokenOfOwnerByIndex(bob, 0) == minted_token_id
    with brownie.reverts():
        minted.tokenOfOwnerByIndex(deployer, 0)

    # mint two more and now check deployer owns them as first two
    minted.mint()
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id + 1
    minted.mint()
    assert minted.tokenOfOwnerByIndex(deployer, 1) == minted_token_id + 2
    # transfer first owned to bob
    minted.transferFrom(deployer, bob, minted_token_id + 1, {"from": deployer})
    assert minted.ownerOf(minted_token_id + 1) == bob
    assert minted.ownerOf(minted_token_id + 2) == deployer
    # whoops!  deployer still showing as owning transferred NFT
    # assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id + 1  # passes, should fail
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id + 2  # should pass
