import brownie
import hexbytes
import pytest
from brownie import ZERO_ADDRESS, accounts, history

#
# These tests are meant to be executed with brownie. To run them:
# * create a brownie project using brownie init
# * in the contract directory, place NFT.sol and ERC721TokenReceiver.sol
# * in the tests directory, place this script
# * run brownie test
#

# Some helper functions


def _ensureToken(token, token_id, owner):
    # XXX Make sure that token does not yet exist
    stop_mint = False
    i = 0
    while stop_mint is False:
        _mint(token, owner, token_id)
        try:
            if token.ownerOf(token_id) == owner:
                stop_mint = True
        except:
            stop_mint = False
        if i > 10:
            assert False
            break
        i += 1


def _mint(token, owner, token_id=1):
    token.mint(owner, {"from": token.owner()})


def _ensureNotToken(token, tokenID):
    with brownie.reverts():
        token.ownerOf(tokenID)


#
# Verify that a Transfer event has been logged
#
def _verifyTransferEvent(txn_receipt, _from, to, tokenID):
    event = txn_receipt.events["Transfer"]
    assert event["_tokenId"] == tokenID
    assert event["_from"] == _from
    assert event["_to"] == to


#
# Verify that an Approval event has been logged
#
def _verifyApprovalEvent(txn_receipt, owner, spender, tokenID):
    event = txn_receipt.events["Approval"]
    assert event["_tokenId"] == tokenID
    assert event["_owner"] == owner
    assert event["_approved"] == spender


#
# Verify that an ApprovalForAll event has been logged
#
def _verifyApprovalForAllEvent(txn_receipt, owner, operator, approved):
    event = txn_receipt.events["ApprovalForAll"]
    assert event["_owner"] == owner
    assert event["_operator"] == operator
    assert event["_approved"] == approved


#
# Inquire the balance for the zero address - this should raise an exception
#
def test_balanceOf_zero_address(token):
    # This should raise an error. Note that we need to provide an address with
    # 40 hex digits, as otherwise the web3 ABI encoder treats the argument as a string
    # and is not able to find the matching ABI entry
    with brownie.reverts():  # "ERC721: balance query for the zero address"):
        balance = token.balanceOf(ZERO_ADDRESS)


#
# Inquire the balance for a non-zero address
#
def test_balanceOf_nonzero_address(token):
    balance = token.balanceOf("0x1" + "0" * 39)
    assert 0 == balance


#
# Mint a token - this also tests balanceOf and
# ownerOf
#
def test_mint(minted, alice, minted_token_id):
    # Remember old balance and mint
    assert minted.balanceOf(alice) == 1
    assert alice == minted.ownerOf(minted_token_id)

    # Verify that minting has created an event
    txn_receipt = history[-1]
    _verifyTransferEvent(txn_receipt, ZERO_ADDRESS, alice, minted_token_id)


#
# Only the contract owner can mint
#
# def test_mint_notOwner(token):
#    me = accounts[0];
#    bob = accounts[1]
#    tokenID = 1;
#
#    # Try to mint
#    with brownie.reverts(): #"Sender not contract owner"):
#        token._mint(tokenID, {"from": bob});

#
# Cannot mint an existing token
#
# def test_mint_tokenExists(token):
#    me = accounts[0];
#    bob = accounts[1]
#    tokenID = 1;
#    _ensureToken(token, tokenID, me);
#    # Try to mint
#    with brownie.reverts(): #"Token already exists"):
#        token._mint(tokenID, {"from": me});


#
# Burn a token
#
# def test_burn(token):
#    me = accounts[0];
#    tokenID = 1;
#    # Make sure that token does not yet exist
#    token._burn(tokenID, {"from": me});
#    # Mint
#    token._mint(tokenID, {"from": me});
#    # Now burn it
#    txn_receipt = token._burn(tokenID, {"from": me});
#    # Verify that burning has created an event
#    _verifyTransferEvent(txn_receipt, me, "0x"+40*"0", tokenID);
#
##
## Only the contract owner can burn
##
# def test_burn_notOwner(token):
#    me = accounts[0];
#    bob = accounts[1]
#    tokenID = 1;
#    _ensureToken(token, tokenID, me);
#    # Try to burn
#    with brownie.reverts(): #"Sender not contract owner"):
#        token._burn(tokenID, {"from": bob});

#
# Get owner of non-existing token
#
def test_owner_of_invalid_token_id(token):
    token_id = 1
    _ensureNotToken(token, token_id)
    with brownie.reverts():  # "ERC721: owner query for nonexistent token"):
        token.ownerOf(token_id)


#
# Test a valid transfer, initiated by the current owner of the token
#
def test_transferFrom(token, alice, bob):
    token_id = 1
    _ensureToken(token, token_id, alice)

    # Remember balances
    old_balance_alice = token.balanceOf(alice)
    old_balance_bob = token.balanceOf(bob)

    # Now do the transfer
    txn_receipt = token.transferFrom(alice, bob, token_id, {"from": alice})

    # check owner of NFT
    assert bob == token.ownerOf(token_id)

    # Check balances
    new_balance_alice = token.balanceOf(alice)
    new_balance_bob = token.balanceOf(bob)

    assert new_balance_alice + 1 == old_balance_alice
    assert old_balance_bob + 1 == new_balance_bob

    # Verify that an Transfer event has been logged
    _verifyTransferEvent(txn_receipt, alice, bob, token_id)


#
# Test an invalid transfer - from is not current owner
#
def test_transferFrom_not_owner(token, alice, bob, charlie):
    token_id = 1
    _ensureToken(token, token_id, alice)
    with brownie.reverts():  # "ERC721: transfer caller is not owner nor approved"):
        token.transferFrom(charlie, bob, token_id, {"from": charlie})


#
# Test an invalid transfer - to is the zero address
#
def test_transferFrom_to_zero_zddress(token, alice):
    token_id = 1
    _ensureToken(token, token_id, alice)
    with brownie.reverts():  # "ERC721: transfer to the zero address"):
        token.transferFrom(alice, ZERO_ADDRESS, token_id, {"from": alice})


#
# Test an invalid transfer - invalid token ID
#
def test_transfer_from_invalid_token_id(token, alice, bob):
    token_id = token.totalSupply() + 2
    with brownie.reverts():
        token.transferFrom(alice, bob, token_id, {"from": alice})


#
# Test an invalid transfer - not authorized
#
def test_transfer_from_not_authorized(token, alice, bob, charlie):
    token_id = 1
    _ensureToken(token, token_id, alice)
    with brownie.reverts():  # "ERC721: transfer caller is not owner nor approved"):
        token.transferFrom(alice, bob, token_id, {"from": charlie})


#
# Test a valid safe transfer, initiated by the current owner of the token
#
def test_safe_transfer_from_current_owner(token, alice, bob):
    token_id = 1
    _ensureToken(token, token_id, alice)

    # Remember balances
    old_balance_alice = token.balanceOf(alice)
    old_balance_bob = token.balanceOf(bob)

    # Now do the transfer
    txn_receipt = token.safeTransferFrom(
        alice, bob, token_id, hexbytes.HexBytes(""), {"from": alice}
    )

    # check owner of NFT
    assert bob == token.ownerOf(token_id)

    # Check balances
    assert token.balanceOf(alice) + 1 == old_balance_alice
    assert old_balance_bob + 1 == token.balanceOf(bob)

    # Verify that an Transfer event has been logged
    _verifyTransferEvent(txn_receipt, alice, bob, token_id)


#
# Test an invalid safe transfer - from is not current owner
#
def test_safe_transfer_from_not_owner(token, alice, bob, charlie):
    token_id = 1
    _ensureToken(token, token_id, alice)
    with brownie.reverts():  # "ERC721: transfer caller is not owner nor approved"):
        token.safeTransferFrom(
            charlie, bob, token_id, hexbytes.HexBytes(""), {"from": charlie}
        )


#
# Test an safe invalid transfer - to is the zero address
#
def test_safe_transfer_from_to_zero_address(token, alice):
    token_id = 1
    _ensureToken(token, token_id, alice)
    with brownie.reverts():  # "ERC721: transfer to the zero address"):
        token.safeTransferFrom(
            alice, ZERO_ADDRESS, token_id, hexbytes.HexBytes(""), {"from": alice}
        )


#
# Test an invalid safe transfer - invalid token ID
#
def test_safe_transfer_tid_from_to_zero_address(token, alice, bob):
    token_id = 1

    # Make sure that token does not exist
    _ensureNotToken(token, token_id)

    # Now do the transfer
    with brownie.reverts():
        token.safeTransferFrom(
            alice, bob, token_id, hexbytes.HexBytes(""), {"from": alice}
        )


#
# Test an invalid safe transfer - not authorized
#
def test_safe_transfer_from_not_authorized(token, alice, bob, charlie):
    token_id = 1
    _ensureToken(token, token_id, alice)
    with brownie.reverts():  # "ERC721: transfer caller is not owner nor approved"):
        token.safeTransferFrom(
            alice, bob, token_id, hexbytes.HexBytes(""), {"from": bob}
        )


#
# Test a valid safe transfer to a contract returning the proper magic value
#
def test_safe_transfer_from(token, tokenReceiver):
    token_receiver = tokenReceiver
    data = "0x1234"
    me = accounts[0]
    token_id = 1
    _ensureToken(token, token_id, me)

    # get current invocation count of test contract
    oldInvocationCount = token_receiver.getInvocationCount()
    # Remember balances
    oldBalanceMe = token.balanceOf(me)
    oldBalanceToken = token.balanceOf(token_receiver.address)
    # Make sure that the contract returns the correct magic value
    token_receiver.setReturnCorrectValue(True)
    # Now do the transfer
    txn_receipt = token.safeTransferFrom(
        me, token_receiver.address, token_id, hexbytes.HexBytes(data), {"from": me}
    )
    # check owner of NFT
    assert token_receiver.address == token.ownerOf(token_id)
    # Check balances
    newBalanceMe = token.balanceOf(me)
    newBalanceToken = token.balanceOf(token_receiver.address)
    assert newBalanceMe + 1 == oldBalanceMe
    assert oldBalanceToken + 1 == newBalanceToken
    # get current invocation count of test contract
    newInvocationCount = token_receiver.getInvocationCount()
    assert oldInvocationCount + 1 == newInvocationCount
    # Check that data has been stored
    assert token_receiver.getData() == data
    # Verify that an Transfer event has been logged
    _verifyTransferEvent(txn_receipt, me, token_receiver.address, token_id)


#
# Test a valid safe transfer to a contract returning the wrong proper magic value
#
def test_safeTransferFrom_wrongMagicValue(token, tokenReceiver):
    me = accounts[0]
    tokenID = 1
    _ensureToken(token, tokenID, me)
    # Make sure that the contract returns the wrong magic value
    tokenReceiver.setReturnCorrectValue(False)
    # Now do the transfer
    with brownie.reverts():  # "Did not return magic value"):
        token.safeTransferFrom(
            me, tokenReceiver.address, tokenID, hexbytes.HexBytes(""), {"from": me}
        )
    # Reset behaviour of test contract
    tokenReceiver.setReturnCorrectValue(True)


#
# Test a valid safe transfer to a contract returning the proper magic value - no data
#
def test_safeTransferFrom_noData(token, tokenReceiver):
    me = accounts[0]
    tokenID = 1
    _ensureToken(token, tokenID, me)
    # get current invocation count of test contract
    oldInvocationCount = tokenReceiver.getInvocationCount()
    # Remember balances
    oldBalanceMe = token.balanceOf(me)
    oldBalanceToken = token.balanceOf(tokenReceiver.address)
    # Make sure that the contract returns the correct magic value
    tokenReceiver.setReturnCorrectValue(True)
    # Now do the transfer
    txn_receipt = token.safeTransferFrom(
        me, tokenReceiver.address, tokenID, {"from": me}
    )
    # check owner of NFT
    assert tokenReceiver.address == token.ownerOf(tokenID)
    # Check balances
    newBalanceMe = token.balanceOf(me)
    newBalanceToken = token.balanceOf(tokenReceiver.address)
    assert newBalanceMe + 1 == oldBalanceMe
    assert oldBalanceToken + 1 == newBalanceToken
    # get current invocation count of test contract
    newInvocationCount = tokenReceiver.getInvocationCount()
    assert oldInvocationCount + 1 == newInvocationCount
    # Verify that an Transfer event has been logged
    _verifyTransferEvent(txn_receipt, me, tokenReceiver.address, tokenID)


#
# Test an approval which is not authorized
#
def test_approval_not_authorized(token, alice, bob):
    token_id = 1
    _ensureToken(token, token_id, bob)
    with brownie.reverts():  # "ERC721: approve caller is not owner nor approved for all"):
        token.approve(alice, token_id, {"from": alice})


#
# Test a valid transfer, initiated by an approved sender
#
def test_transfer_from_approved(token, alice, bob, charlie):
    token_id = 1
    _ensureToken(token, token_id, alice)

    # Approve
    token.approve(charlie, token_id, {"from": alice})
    old_balance_alice = token.balanceOf(alice)
    old_balance_bob = token.balanceOf(bob)

    # Now do the transfer
    txn_receipt = token.transferFrom(alice, bob, token_id, {"from": charlie})
    assert bob == token.ownerOf(token_id)

    # Check balances
    new_balance_alice = token.balanceOf(alice)
    new_balance_bob = token.balanceOf(bob)
    assert new_balance_alice + 1 == old_balance_alice
    assert old_balance_bob + 1 == new_balance_bob

    # Verify that an Transfer event has been logged
    _verifyTransferEvent(txn_receipt, alice, bob, token_id)


#
# Test setting and getting approval
#
def test_approval(token, alice, bob, charlie):
    token_id = 1

    # Make sure that token does not yet exist
    _ensureNotToken(token, token_id)

    # Get approval - should raise
    with brownie.reverts():  # "ERC721: approved query for nonexistent token"):
        token.getApproved(token_id)

    # Approve - should raise
    with brownie.reverts():  # "ERC721: owner query for nonexistent token"):
        token.approve(charlie, token_id, {"from": alice})

    # Mint
    _mint(token, alice)

    # Approve for charlie
    txn_receipt = token.approve(charlie, token_id, {"from": alice})

    # Check
    assert charlie == token.getApproved(token_id)

    # Verify events
    _verifyApprovalEvent(txn_receipt, alice, charlie, token_id)


#
# Test that approval is reset to zero address if token is transferred
#
def test_approval_resetUponTransfer(token):
    me = accounts[0]
    alice = accounts[1]
    bob = accounts[2]
    tokenID = 1
    _ensureToken(token, tokenID, me)
    # Approve for bob
    token.approve(bob, tokenID, {"from": me})
    # Check
    assert bob == token.getApproved(tokenID)
    # Do transfer
    token.transferFrom(me, alice, tokenID, {"from": bob})
    # Check that approval has been reset
    assert ("0x" + 40 * "0") == token.getApproved(tokenID)


#
# Test setting and clearing the operator flag
#
def test_setGetOperator(token):
    me = accounts[0]
    alice = accounts[1]
    bob = accounts[2]
    assert False == token.isApprovedForAll(me, bob)
    assert False == token.isApprovedForAll(me, alice)
    # Declare bob as operator for me
    txn_receipt = token.setApprovalForAll(bob, True, {"from": me})
    # Check
    assert True == token.isApprovedForAll(me, bob)
    assert False == token.isApprovedForAll(me, alice)
    # Check events
    _verifyApprovalForAllEvent(txn_receipt, me, bob, True)
    # Do the same for alice
    txn_receipt = token.setApprovalForAll(alice, True, {"from": me})
    # Check
    assert True == token.isApprovedForAll(me, bob)
    assert True == token.isApprovedForAll(me, alice)
    # Check events
    _verifyApprovalForAllEvent(txn_receipt, me, alice, True)
    # Reset both
    txn_receipt = token.setApprovalForAll(bob, False, {"from": me})
    # Check events
    _verifyApprovalForAllEvent(txn_receipt, me, bob, False)
    txn_receipt = token.setApprovalForAll(alice, False, {"from": me})
    # Check events
    _verifyApprovalForAllEvent(txn_receipt, me, alice, False)
    # Check
    assert False == token.isApprovedForAll(me, bob)
    assert False == token.isApprovedForAll(me, alice)


def test_only_approval_not_on_my_tokens(token, alice):
    with brownie.reverts():
        token.setApprovalForAll(alice, True, {"from": alice})


#
# Test authorization logic for setting and getting approval
#
def test_approval_authorization(token, alice, bob, charlie):
    token_id = 1
    _ensureToken(token, token_id, alice)
    # Try to approve for charlie while not being owner or operator - this should raise an exception
    with brownie.reverts():  # "ERC721: approve caller is not owner nor approved for all"):
        token.approve(charlie, token_id, {"from": bob})

    # Now make bob an operator for alice
    token.setApprovalForAll(bob, True, {"from": alice})

    # Approve for charlie again - this should now work
    txn_receipt = token.approve(charlie, token_id, {"from": bob})

    # Check
    assert charlie == token.getApproved(token_id)
    _verifyApprovalEvent(txn_receipt, alice, charlie, token_id)

    # Reset
    token.setApprovalForAll(bob, False, {"from": alice})


#
# Test a valid transfer, initiated by an operator for the current owner of the token
#
def test_transferFrom_operator(token):
    me = accounts[0]
    alice = accounts[1]
    bob = accounts[2]
    tokenID = 1
    _ensureToken(token, tokenID, me)
    # Now make bob an operator for me
    token.setApprovalForAll(bob, True, {"from": me})
    # Remember balances
    oldBalanceMe = token.balanceOf(me)
    oldBalanceAlice = token.balanceOf(alice)
    # Now do the transfer
    txn_receipt = token.transferFrom(me, alice, tokenID, {"from": bob})
    # Reset
    token.setApprovalForAll(bob, False, {"from": me})
    # check owner of NFT
    assert alice == token.ownerOf(tokenID)
    # Check balances
    newBalanceMe = token.balanceOf(me)
    newBalanceAlice = token.balanceOf(alice)
    assert newBalanceMe + 1 == oldBalanceMe
    assert oldBalanceAlice + 1 == newBalanceAlice
    # Verify that an Transfer event has been logged
    _verifyTransferEvent(txn_receipt, me, alice, tokenID)


#
# Test ERC165 functions
#
def test_ERC615(token):
    # ERC721
    assert True == token.supportsInterface("0x80ac58cd")
    # ERC165 itself
    assert True == token.supportsInterface("0x01ffc9a7")
    # ERC721 Metadata
    assert True == token.supportsInterface("0x5b5e139f")


#
# Test name and symbol
#
def test_name_symbol(token):
    name = token.name()
    symbol = token.symbol()
    assert len(name) > 0
    assert len(symbol) > 0


#
# Test tokenURI
#
def test_token_uri(token, alice):
    token_id = 1

    # Make sure that token does not yet exist
    _ensureNotToken(token, token_id)

    # Try to get tokenURI of invalid token - should raise exception
    with brownie.reverts():  # "ERC721URIStorage: URI query for nonexistent token"):
        token.tokenURI(token_id)

    # Mint
    _ensureToken(token, token_id, alice)

    token.set_revealed(True, {"from": token.owner()})

    # Get base URI
    base_uri = token.base_uri()

    # Get token URI
    token_uri = token.tokenURI(token_id)

    assert f"{base_uri}{token_id}" == token_uri


#
# Test tokenURI - token ID 0
#
def test_token_uri_id_zero(token, alice):
    token_id = 1
    # Make sure that token does not yet exist
    _ensureNotToken(token, token_id)
    # Try to get tokenURI of invalid token - should raise exception
    with brownie.reverts():  # "ERC721URIStorage: URI query for nonexistent token"):
        token.tokenURI(token_id)

    # Mint
    _ensureToken(token, token_id, alice)
    token.set_revealed(True, {"from": token.owner()})

    # Get base URI
    base_uri = token.base_uri()
    default_uri = token_id

    # Get token URI
    token_uri = token.tokenURI(token_id)
    assert f"{base_uri}{default_uri}" == token_uri
