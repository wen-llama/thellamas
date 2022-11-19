import brownie


def test_tokenOfOwnerByIndex_accurate(minted, alice, minted_token_id, bob):
    assert minted.tokenOfOwnerByIndex(alice, 0) == minted_token_id
    with brownie.reverts():
        minted.tokenOfOwnerByIndex(bob, 0)
    minted.transferFrom(alice, bob, minted_token_id, {"from": alice})
    assert minted.tokenOfOwnerByIndex(bob, 0) == minted_token_id
    with brownie.reverts():
        minted.tokenOfOwnerByIndex(alice, 0)
