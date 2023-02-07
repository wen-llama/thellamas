import brownie


def test_tokenOfOwnerByIndex_accurate(minted, deployer, minted_token_id, bob):
    assert minted.tokenOfOwnerByIndex(deployer, 0) == minted_token_id
    with brownie.reverts():
        minted.tokenOfOwnerByIndex(bob, 0)
    minted.transferFrom(deployer, bob, minted_token_id, {"from": deployer})
    assert minted.tokenOfOwnerByIndex(bob, 0) == minted_token_id
    with brownie.reverts():
        minted.tokenOfOwnerByIndex(deployer, 0)
