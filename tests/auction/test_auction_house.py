import brownie
from brownie import ZERO_ADDRESS, chain, web3
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct

from tests.conftest import ID_AFTER_PREMINT

# Helper methods


def create_pending_returns(auction_house, bidder_1, bidder_2):
    auction_house.disable_wl()
    auction_house.create_bid(ID_AFTER_PREMINT, 100, {"from": bidder_1, "value": "100 wei"})
    auction_house.create_bid(ID_AFTER_PREMINT, 200, {"from": bidder_2, "value": "200 wei"})


# Initialization vars


def test_owner(auction_house, deployer):
    assert auction_house.owner() == deployer


def test_llamas(auction_house, token):
    assert auction_house.llamas() == token


def test_time_buffer(auction_house):
    assert auction_house.time_buffer() == 100


def test_bid_after(auction_house):
    assert auction_house.reserve_price() == 100


def test_min_bid_increment_percentage(auction_house):
    assert auction_house.min_bid_increment_percentage() == 5


def test_duration(auction_house):
    assert auction_house.duration() == 100


def test_paused(auction_house):
    assert auction_house.paused()


def test_wl_enabled(auction_house):
    assert auction_house.wl_enabled()


def test_wl_signer(auction_house, deployer):
    assert auction_house.wl_signer() == deployer


# Owner control


def test_set_owner(auction_house, alice):
    auction_house.set_owner(alice)
    assert auction_house.owner() == alice


def test_set_owner_zero_address(auction_house, deployer):
    with brownie.reverts("Cannot set owner to zero address"):
        auction_house.set_owner(ZERO_ADDRESS)
    assert auction_house.owner() == deployer


def test_set_time_buffer(auction_house):
    auction_house.set_time_buffer(200)
    assert auction_house.time_buffer() == 200


def test_set_reserve_price(auction_house):
    auction_house.set_reserve_price(200)
    assert auction_house.reserve_price() == 200


def test_set_min_bid_increment_percentage(auction_house):
    auction_house.set_min_bid_increment_percentage(15)
    assert auction_house.min_bid_increment_percentage() == 15


def test_set_min_bid_increment_percentage_above_range(auction_house):
    with brownie.reverts("_min_bid_increment_percentage out of range"):
        auction_house.set_min_bid_increment_percentage(16)
    assert auction_house.min_bid_increment_percentage() == 5


def test_set_min_bid_increment_percentage_below_range(auction_house):
    with brownie.reverts("_min_bid_increment_percentage out of range"):
        auction_house.set_min_bid_increment_percentage(1)
    assert auction_house.min_bid_increment_percentage() == 5


def test_set_duration(auction_house):
    auction_house.set_duration(3600)
    assert auction_house.duration() == 3600


def test_set_duration_above_range(auction_house):
    with brownie.reverts("_duration out of range"):
        auction_house.set_duration(260000)
    assert auction_house.duration() == 100


def test_set_duration_below_range(auction_house):
    with brownie.reverts("_duration out of range"):
        auction_house.set_duration(3599)
    assert auction_house.duration() == 100


def test_set_wl_signer(auction_house, alice):
    auction_house.set_wl_signer(alice)
    assert auction_house.wl_signer() == alice


def test_enable_disable_wl(auction_house):
    assert auction_house.wl_enabled()
    auction_house.disable_wl()
    assert not auction_house.wl_enabled()
    auction_house.enable_wl()
    assert auction_house.wl_enabled()


def test_pause_unpause(auction_house_unpaused, minted_token_id):
    assert not auction_house_unpaused.paused()
    assert auction_house_unpaused.auction()["llama_id"] == minted_token_id
    assert not auction_house_unpaused.auction()["settled"]
    auction_house_unpaused.pause()
    assert auction_house_unpaused.paused()


def test_set_owner_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.set_owner(alice, {"from": alice})


def test_set_time_buffer_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.set_time_buffer(200, {"from": alice})


def test_set_reserve_price_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.set_reserve_price(200, {"from": alice})


def test_set_min_bid_increment_percentage_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.set_min_bid_increment_percentage(200, {"from": alice})


def test_set_duration_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.set_duration(1000, {"from": alice})


def test_set_wl_signer_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.set_wl_signer(alice, {"from": alice})


def test_pause_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.pause({"from": alice})


def test_unpause_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.unpause({"from": alice})


def test_withdraw_stale_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.withdraw_stale([alice, alice], {"from": alice})


# WL Bidding


def test_create_friend_bid(auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["friend:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    auction_house_unpaused.create_friend_bid(
        ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
    )
    current_auction = auction_house_unpaused.auction()
    assert current_auction["bidder"] == alice
    assert current_auction["amount"] == 100


def test_create_friend_bid_wl_disabled(auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["friend:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    auction_house_unpaused.disable_wl()
    with brownie.reverts("WL auction is not enabled"):
        auction_house_unpaused.create_friend_bid(
            ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
        )


def test_create_friend_bid_after_already_winning_one_auction(
    token, auction_house_unpaused, alice, deployer
):
    alice_encoded = encode(["string", "address"], ["friend:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    auction_house_unpaused.create_friend_bid(
        ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
    )
    current_auction = auction_house_unpaused.auction()
    assert current_auction["bidder"] == alice
    assert current_auction["amount"] == 100

    chain.sleep(1000)

    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(ID_AFTER_PREMINT) == alice

    with brownie.reverts("Already won 1 WL auction"):
        auction_house_unpaused.create_friend_bid(
            ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
        )


def test_wl_signature_cannot_be_used_for_friend_bid(token, auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    with brownie.reverts("Signature is invalid"):
        auction_house_unpaused.create_friend_bid(
            ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
        )


def test_create_wl_bid(auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
    )
    current_auction = auction_house_unpaused.auction()
    assert current_auction["bidder"] == alice
    assert current_auction["amount"] == 100


def test_create_bid_wl_enabled(auction_house_unpaused, alice):
    with brownie.reverts("Public auction is not enabled"):
        auction_house_unpaused.create_bid(
            ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"}
        )


def test_create_wl_bid_invalid_signature(auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["blah:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    with brownie.reverts("Signature is invalid"):
        auction_house_unpaused.create_wl_bid(
            ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
        )


def test_create_wl_bid_wl_not_enabled(auction_house_unpaused, alice, deployer):
    auction_house_unpaused.disable_wl()
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    with brownie.reverts("WL auction is not enabled"):
        auction_house_unpaused.create_wl_bid(
            ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
        )


def test_create_wl_bid_wrong_llama_id(auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    with brownie.reverts("Llama not up for auction"):
        auction_house_unpaused.create_wl_bid(
            ID_AFTER_PREMINT + 1, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
        )


def test_create_wl_bid_auction_expired(auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    chain.sleep(1000)
    with brownie.reverts("Auction expired"):
        auction_house_unpaused.create_wl_bid(
            ID_AFTER_PREMINT, 100, signed_message.signature, {"from": alice, "value": "100 wei"}
        )


def test_create_wl_bid_less_than_reserve_price(auction_house_unpaused, alice, deployer):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    with brownie.reverts("Must send at least reservePrice"):
        auction_house_unpaused.create_wl_bid(
            ID_AFTER_PREMINT, 99, signed_message.signature, {"from": alice, "value": "99 wei"}
        )


def test_create_wl_bid_not_over_prev_bid(auction_house_unpaused, alice, bob, deployer):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    alice_signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT, 100, alice_signed_message.signature, {"from": alice, "value": "100 wei"}
    )
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    bob_encoded = encode(["string", "address"], ["whitelist:", bob.address])
    bob_hashed = web3.keccak(bob_encoded)
    bob_signable_message = encode_defunct(bob_hashed)
    bob_signed_message = Account.sign_message(bob_signable_message, deployer.private_key)

    with brownie.reverts("Must send more than last bid by min_bid_increment_percentage amount"):
        auction_house_unpaused.create_wl_bid(
            ID_AFTER_PREMINT, 101, bob_signed_message.signature, {"from": bob, "value": "101 wei"}
        )

    bid_after = auction_house_unpaused.auction()
    assert bid_after["bidder"] == alice
    assert bid_after["amount"] == 100


def test_create_wl_bid_can_only_win_two_wl_auctions(
    token, auction_house_unpaused, alice, bob, deployer
):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    alice_signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT, 100, alice_signed_message.signature, {"from": alice, "value": "100 wei"}
    )
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(ID_AFTER_PREMINT) == alice
    assert auction_house_unpaused.wl_auctions_won(alice) == 1
    assert auction_house_unpaused.auction()["llama_id"] == ID_AFTER_PREMINT + 1

    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT + 1,
        100,
        alice_signed_message.signature,
        {"from": alice, "value": "100 wei"},
    )
    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(ID_AFTER_PREMINT + 1) == alice
    assert auction_house_unpaused.wl_auctions_won(alice) == 2
    assert auction_house_unpaused.auction()["llama_id"] == ID_AFTER_PREMINT + 2

    # Alice can't win any more wl auctions.
    with brownie.reverts("Already won 2 WL auctions"):
        auction_house_unpaused.create_wl_bid(
            ID_AFTER_PREMINT + 2,
            100,
            alice_signed_message.signature,
            {"from": alice, "value": "100 wei"},
        )

    # Bob can still win a wl auction.
    bob_encoded = encode(["string", "address"], ["whitelist:", bob.address])
    bob_hashed = web3.keccak(bob_encoded)
    bob_signable_message = encode_defunct(bob_hashed)
    bob_signed_message = Account.sign_message(bob_signable_message, deployer.private_key)

    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT + 2, 100, bob_signed_message.signature, {"from": bob, "value": "100 wei"}
    )
    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(ID_AFTER_PREMINT + 2) == bob
    assert auction_house_unpaused.wl_auctions_won(bob) == 1
    assert auction_house_unpaused.auction()["llama_id"] == ID_AFTER_PREMINT + 3


def test_create_wl_bid_using_pending_returns(token, auction_house_unpaused, alice, bob, deployer):
    alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
    alice_hashed = web3.keccak(alice_encoded)
    alice_signable_message = encode_defunct(alice_hashed)
    alice_signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT, 100, alice_signed_message.signature, {"from": alice, "value": "100 wei"}
    )
    auction_1 = auction_house_unpaused.auction()
    assert auction_1["bidder"] == alice
    assert auction_1["amount"] == 100

    bob_encoded = encode(["string", "address"], ["whitelist:", bob.address])
    bob_hashed = web3.keccak(bob_encoded)
    bob_signable_message = encode_defunct(bob_hashed)
    bob_signed_message = Account.sign_message(bob_signable_message, deployer.private_key)

    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT, 200, bob_signed_message.signature, {"from": bob, "value": "200 wei"}
    )

    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 200

    assert auction_house_unpaused.pending_returns(alice) == 100

    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT, 300, alice_signed_message.signature, {"from": alice, "value": "200 wei"}
    )

    auction_3 = auction_house_unpaused.auction()
    assert auction_3["bidder"] == alice
    assert auction_3["amount"] == 300
    assert auction_house_unpaused.pending_returns(alice) == 0

    auction_house_unpaused.create_wl_bid(
        ID_AFTER_PREMINT, 1000, bob_signed_message.signature, {"from": bob, "value": "1000 wei"}
    )

    auction_4 = auction_house_unpaused.auction()
    assert auction_4["bidder"] == bob
    assert auction_4["amount"] == 1000
    assert auction_house_unpaused.pending_returns(alice) == 300


# Public Bidding


def test_create_bid(auction_house_unpaused, alice):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    current_auction = auction_house_unpaused.auction()
    assert current_auction["bidder"] == alice
    assert current_auction["amount"] == 100


def test_create_bid_send_more_than_last_bid(auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    firt_bid = auction_house_unpaused.auction()
    assert firt_bid["bidder"] == alice
    assert firt_bid["amount"] == 100

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 1000, {"from": bob, "value": "1000 wei"})
    second_bid = auction_house_unpaused.auction()
    assert second_bid["bidder"] == bob
    assert second_bid["amount"] == 1000


def test_create_bid_wrong_llama_id(auction_house_unpaused, alice):
    auction_house_unpaused.disable_wl()
    with brownie.reverts("Llama not up for auction"):
        auction_house_unpaused.create_bid(19, 100, {"from": alice, "value": "100 wei"})


def test_create_bid_auction_expired(auction_house_unpaused, alice):
    auction_house_unpaused.disable_wl()
    # Expire the auction
    chain.sleep(1000)
    with brownie.reverts("Auction expired"):
        auction_house_unpaused.create_bid(
            ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"}
        )


def test_create_bid_value_too_low(auction_house_unpaused, alice):
    auction_house_unpaused.disable_wl()
    with brownie.reverts("Must send at least reservePrice"):
        auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 1, {"from": alice, "value": "1 wei"})


def test_create_bid_not_over_prev_bid(auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    with brownie.reverts("Must send more than last bid by min_bid_increment_percentage amount"):
        auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 101, {"from": bob, "value": "101 wei"})

    bid_after = auction_house_unpaused.auction()
    assert bid_after["bidder"] == alice
    assert bid_after["amount"] == 100


def test_create_bid_using_pending_returns(token, auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 106, {"from": bob, "value": "106 wei"})
    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 106

    assert auction_house_unpaused.pending_returns(alice) == 100

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 125, {"from": alice, "value": "25 wei"})

    auction_3 = auction_house_unpaused.auction()
    assert auction_3["bidder"] == alice
    assert auction_3["amount"] == 125
    assert auction_house_unpaused.pending_returns(alice) == 0

    chain.sleep(101)

    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(ID_AFTER_PREMINT) == alice


def test_create_bid_using_pending_returns_from_previous_auction(
    token, auction_house_unpaused, alice, bob
):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 106, {"from": bob, "value": "106 wei"})
    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 106

    assert auction_house_unpaused.pending_returns(alice) == 100

    chain.sleep(101)

    auction_house_unpaused.settle_current_and_create_new_auction()

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT + 1, 100, {"from": alice})

    new_auction = auction_house_unpaused.auction()
    new_auction["bidder"] == alice
    new_auction["amount"] == 100

    assert auction_house_unpaused.pending_returns(alice) == 0

    chain.sleep(101)
    auction_house_unpaused.settle_current_and_create_new_auction()
    assert token.ownerOf(ID_AFTER_PREMINT + 1) == alice


def test_create_bid_using_pending_returns_outbid(token, auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 106, {"from": bob, "value": "106 wei"})
    auction_1 = auction_house_unpaused.auction()
    assert auction_1["bidder"] == bob
    assert auction_1["amount"] == 106

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 125, {"from": alice, "value": "25 wei"})

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 200, {"from": bob, "value": "200 wei"})

    assert auction_house_unpaused.pending_returns(alice) == 125

    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 200


def test_create_bid_using_pending_returns_not_enough(auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 106, {"from": bob, "value": "106 wei"})
    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 106

    with brownie.reverts("Does not have enough pending returns to cover remainder"):
        auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 126, {"from": alice, "value": "25 wei"})

    auction_3 = auction_house_unpaused.auction()
    assert auction_3["bidder"] == bob
    assert auction_3["amount"] == 106

    assert auction_house_unpaused.pending_returns(alice) == 100


# WITHDRAW


def test_create_second_bid_and_withdraw(auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100
    alice_balance_before = alice.balance()

    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 1000, {"from": bob, "value": "1000 wei"})

    bid_after = auction_house_unpaused.auction()
    assert bid_after["bidder"] == bob
    assert bid_after["amount"] == 1000

    auction_house_unpaused.withdraw({"from": alice})

    alice_balance_after = alice.balance()

    assert alice_balance_after == alice_balance_before + 100


def test_withdraw_zero_pending(auction_house, alice):
    balance_before = alice.balance()
    auction_house.withdraw({"from": alice})
    balance_after = alice.balance()
    assert balance_before == balance_after


def test_withdraw_stale(token, auction_house_unpaused, deployer, alice, bob):
    balance_of_alice_before = alice.balance()
    balance_of_deployer_before = deployer.balance()

    create_pending_returns(auction_house_unpaused, alice, bob)
    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(ID_AFTER_PREMINT) == bob
    assert deployer.balance() == balance_of_deployer_before + 200
    assert alice.balance() == balance_of_alice_before - 100
    assert auction_house_unpaused.pending_returns(alice) == 100
    auction_house_unpaused.withdraw_stale([alice])
    assert auction_house_unpaused.pending_returns(alice) == 0
    assert alice.balance() == balance_of_alice_before - 5  # Alice gets a 5% penalty
    assert (
        deployer.balance() == balance_of_deployer_before + 205
    )  # The owner takes 5% of alices pending returns


def test_withdraw_stale_user_has_no_pending_withdraws(auction_house_unpaused, alice, bob, charlie):
    balance_of_alice_before = alice.balance()
    balance_of_bob_before = bob.balance()
    balance_of_charlie_before = charlie.balance()
    wei_charlie_spent_to_win_auction = 200
    wei_fee_bob_payed_for_admin_stale_withdraw = 5

    create_pending_returns(auction_house_unpaused, bob, charlie)
    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()

    assert auction_house_unpaused.pending_returns(alice) == 0
    assert auction_house_unpaused.pending_returns(bob) == 100
    assert auction_house_unpaused.pending_returns(charlie) == 0
    auction_house_unpaused.withdraw_stale([alice, bob, charlie])
    assert (
        alice.balance() == balance_of_alice_before
    )  # Alice didn't have anything to withdraw because she never placed a bid.
    assert (
        bob.balance() == balance_of_bob_before - wei_fee_bob_payed_for_admin_stale_withdraw
    )  # Bob had 100 wei to withdraw but payed a 5% admin withdrawal fee.
    assert (
        charlie.balance() == balance_of_charlie_before - wei_charlie_spent_to_win_auction
    )  # Charlie didn't have anything to withdraw because he won the auction.


def test_settle_auction_no_bid(token, deployer, auction_house_unpaused):
    assert not auction_house_unpaused.auction()["settled"]
    chain.sleep(1000)
    auction_house_unpaused.pause()
    auction_house_unpaused.settle_auction()
    assert auction_house_unpaused.auction()["settled"]
    # Token was transferred to owner when no one bid
    assert token.ownerOf(ID_AFTER_PREMINT) == deployer


def test_settle_auction_when_not_paused(auction_house_unpaused):
    with brownie.reverts("Auction house is not paused"):
        auction_house_unpaused.settle_auction()


def test_settle_current_and_create_new_auction_no_bid(token, deployer, auction_house_unpaused):
    auction_house_unpaused.disable_wl()
    assert not auction_house_unpaused.auction()["settled"]
    old_auction_id = auction_house_unpaused.auction()["llama_id"]
    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()
    new_auction_id = auction_house_unpaused.auction()["llama_id"]
    assert not auction_house_unpaused.auction()["settled"]
    assert old_auction_id < new_auction_id
    # Token was transferred to owner when no one bid
    assert token.ownerOf(ID_AFTER_PREMINT) == deployer


def test_settle_auction_with_bid(token, deployer, auction_house_unpaused, alice):
    auction_house_unpaused.disable_wl()
    assert not auction_house_unpaused.auction()["settled"]
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    chain.sleep(1000)
    auction_house_unpaused.pause()
    deployer_balance_before = deployer.balance()
    auction_house_unpaused.settle_auction()
    deployer_balance_after = deployer.balance()
    assert auction_house_unpaused.auction()["settled"]
    assert token.ownerOf(ID_AFTER_PREMINT) == alice
    assert deployer_balance_after == deployer_balance_before + 100


def test_settle_current_and_create_new_auction_with_bid(deployer, auction_house_unpaused, alice):
    auction_house_unpaused.disable_wl()
    assert not auction_house_unpaused.auction()["settled"]
    old_auction_id = auction_house_unpaused.auction()["llama_id"]
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    chain.sleep(1000)
    deployer_balance_before = deployer.balance()
    auction_house_unpaused.settle_current_and_create_new_auction()
    deployer_balance_after = deployer.balance()
    new_auction_id = auction_house_unpaused.auction()["llama_id"]
    assert not auction_house_unpaused.auction()["settled"]
    assert old_auction_id < new_auction_id
    assert deployer_balance_after == deployer_balance_before + 100


def test_settle_current_and_create_new_auction_when_paused(token, auction_house):
    token.set_minter(auction_house)
    with brownie.reverts("Auction house is paused"):
        auction_house.settle_current_and_create_new_auction()


def test_settle_auction_multiple_bids(token, deployer, auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    assert not auction_house_unpaused.auction()["settled"]
    alice_balance_start = alice.balance()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 1000, {"from": bob, "value": "1000 wei"})
    chain.sleep(1000)
    auction_house_unpaused.pause()
    deployer_balance_before = deployer.balance()
    auction_house_unpaused.settle_auction()
    deployer_balance_after = deployer.balance()
    alice_balance_before_withdraw = alice.balance()
    assert alice_balance_before_withdraw == alice_balance_start - 100
    auction_house_unpaused.withdraw({"from": alice})
    alice_balance_after_withdraw = alice.balance()
    assert alice_balance_after_withdraw == alice_balance_start
    assert auction_house_unpaused.auction()["settled"]
    assert token.ownerOf(ID_AFTER_PREMINT) == bob
    assert deployer_balance_after == deployer_balance_before + 1000


def test_bidder_outbids_prev_bidder(token, auction_house_unpaused, deployer, alice, bob):
    auction_house_unpaused.disable_wl()
    assert not auction_house_unpaused.auction()["settled"]
    alice_balance_start = alice.balance()
    bob_balance_start = bob.balance()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 1000, {"from": bob, "value": "1000 wei"})
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 2000, {"from": alice, "value": "2000 wei"})
    chain.sleep(1000)
    deployer_balance_before = deployer.balance()
    auction_house_unpaused.settle_current_and_create_new_auction()
    deployer_balance_after = deployer.balance()
    alice_balance_before_withdraw = alice.balance()
    bob_balance_before_withdraw = bob.balance()
    assert alice_balance_before_withdraw == alice_balance_start - 2100
    assert bob_balance_before_withdraw == bob_balance_start - 1000
    auction_house_unpaused.withdraw({"from": alice})
    auction_house_unpaused.withdraw({"from": bob})
    alice_balance_after_withdraw = alice.balance()
    bob_balance_after_withdraw = bob.balance()
    assert alice_balance_after_withdraw == alice_balance_start - 2000
    assert bob_balance_after_withdraw == bob_balance_start
    assert not auction_house_unpaused.auction()["settled"]
    assert token.ownerOf(ID_AFTER_PREMINT) == alice
    assert deployer_balance_after == deployer_balance_before + 2000


# AUCTION EXTENSION


def test_create_bid_auction_extended(auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    starting_block_timestamp = chain.time()
    chain.sleep(90)
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 1000, {"from": bob, "value": "1000 wei"})
    assert auction_house_unpaused.auction()["end_time"] == starting_block_timestamp + 190
    assert not auction_house_unpaused.auction()["settled"]


def test_create_bid_auction_not_extended(auction_house_unpaused, alice, bob):
    auction_house_unpaused.disable_wl()
    auction_house_unpaused.create_bid(ID_AFTER_PREMINT, 100, {"from": alice, "value": "100 wei"})
    chain.sleep(101)
    with brownie.reverts("Auction expired"):
        auction_house_unpaused.create_bid(
            ID_AFTER_PREMINT, 1000, {"from": bob, "value": "1000 wei"}
        )
