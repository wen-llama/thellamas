import ape


# Test the name method
def test_name(token, token_metadata):
    assert token.name() == token_metadata["name"]


# Test the symbol
def test_symbol(token, token_metadata):
    assert token.symbol() == token_metadata["symbol"]


# Test balanceOf
def test_balanceOf(minted, deployer, token, minted_token_id, premint):
    assert token.ownerOf(minted_token_id) == deployer
    assert token.balanceOf(deployer.address) == token.totalSupply() - premint


# Test a valid transfer
def test_transfer(minted, deployer, bob, token, minted_token_id):
    token = token
    init_bal_alice = token.balanceOf(deployer)
    init_bal_bob = token.balanceOf(bob)

    txn_receipt = token.transferFrom(deployer, bob, minted_token_id, sender=deployer)
    assert init_bal_alice - 1 == token.balanceOf(deployer)
    assert init_bal_bob + 1 == token.balanceOf(bob)

    # Verify that event has been emitted
    event = txn_receipt.events[0]
    assert event["_from"] == deployer
    assert event["_to"] == bob
    assert event["_tokenId"] == minted_token_id


# Test an unauthorized transferFrom
def test_transfer_nonowner(minted, alice, bob, token):
    token = token
    old_balance_alice = token.balanceOf(alice)
    old_balance_bob = token.balanceOf(bob)

    with ape.reverts():  # "ERC721: transfer caller is not owner nor approved"):
        token.transferFrom(alice, bob, 1, sender=bob)
    assert token.balanceOf(alice) == old_balance_alice
    assert token.balanceOf(bob) == old_balance_bob


# Test a transfer with no balance
def test_transfer_nobalance(token, alice, bob):
    with ape.reverts():
        token.transferFrom(alice, bob, 1, sender=bob)


# Test approval
def test_approve(minted, deployer, bob, token, minted_token_id):
    # Allow bob to spend 100 token on my behalf
    txn_receipt = token.approve(bob, minted_token_id, sender=deployer)

    # Verify that event has been emitted
    event = txn_receipt.events[0]
    assert event["_owner"] == deployer
    assert event["_approved"] == bob
    assert event["_tokenId"] == minted_token_id

    # Check
    assert token.getApproved(minted_token_id) == bob


# Test approval - overwrite old value
def test_approve_overwrite(minted, deployer, bob, charlie, token, minted_token_id):

    # Allow bob to spend 100 token on my behalf
    token.approve(bob, minted_token_id, sender=deployer)

    # Check
    assert token.getApproved(minted_token_id) == bob

    # Overwrite
    token.approve(charlie, minted_token_id, sender=deployer)
    assert token.getApproved(minted_token_id) == charlie


def test_cannot_approve_owner(minted, deployer, bob, token, minted_token_id):

    # Allow bob to spend 100 token on my behalf
    token.approve(bob, minted_token_id, sender=deployer)

    # Check
    assert token.getApproved(minted_token_id) == bob

    # Overwrite
    with ape.reverts():  # "ERC721: approval to current owner"):
        token.approve(deployer, minted_token_id, sender=deployer)


# Test a valid withdrawal
def test_transferFrom(minted, deployer, bob, token, minted_token_id):
    init_balance_deployer = token.balanceOf(deployer)
    init_balance_bob = token.balanceOf(bob)

    # Authorize bob
    token.approve(bob, minted_token_id, sender=deployer)
    txn_receipt = token.transferFrom(deployer, bob, minted_token_id, sender=bob)
    assert init_balance_deployer - 1 == token.balanceOf(deployer)
    assert init_balance_bob + 1 == token.balanceOf(bob)

    # Verify that event has been emitted
    event = txn_receipt.events[0]
    assert event["_from"] == deployer
    assert event["_to"] == bob
    assert event["_tokenId"] == minted_token_id

    # Verify that the approval has been set to ZERO_ADDRESS
    assert token.getApproved(minted_token_id) == "0x0000000000000000000000000000000000000000"
