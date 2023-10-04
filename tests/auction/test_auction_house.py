import brownie
from brownie import chain, web3, ZERO_ADDRESS
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct


# Helper methods


def create_pending_returns(auction_house, bidder_1, bidder_2):
    auction_house.create_bid(40, 100, {"from": bidder_1, "value": "100 wei"})
    auction_house.create_bid(40, 200, {"from": bidder_2, "value": "200 wei"})


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



def test_pause_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.pause({"from": alice})


def test_unpause_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.unpause({"from": alice})


def test_withdraw_stale_not_owner(auction_house, alice):
    with brownie.reverts("Caller is not the owner"):
        auction_house.withdraw_stale([alice, alice], {"from": alice})


# Public Bidding


def test_create_bid(auction_house_unpaused, alice):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    current_auction = auction_house_unpaused.auction()
    assert current_auction["bidder"] == alice
    assert current_auction["amount"] == 100


def test_create_bid_send_more_than_last_bid(auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    firt_bid = auction_house_unpaused.auction()
    assert firt_bid["bidder"] == alice
    assert firt_bid["amount"] == 100

    auction_house_unpaused.create_bid(40, 1000, {"from": bob, "value": "1000 wei"})
    second_bid = auction_house_unpaused.auction()
    assert second_bid["bidder"] == bob
    assert second_bid["amount"] == 1000


def test_create_bid_wrong_llama_id(auction_house_unpaused, alice):
    with brownie.reverts("Llama not up for auction"):
        auction_house_unpaused.create_bid(39, 100, {"from": alice, "value": "100 wei"})


def test_create_bid_auction_expired(auction_house_unpaused, alice):
    # Expire the auction
    chain.sleep(1000)
    with brownie.reverts("Auction expired"):
        auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})


def test_create_bid_value_too_low(auction_house_unpaused, alice):
    with brownie.reverts("Must send at least reservePrice"):
        auction_house_unpaused.create_bid(40, 1, {"from": alice, "value": "1 wei"})


def test_create_bid_not_over_prev_bid(auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    with brownie.reverts("Must send more than last bid by min_bid_increment_percentage amount"):
        auction_house_unpaused.create_bid(40, 101, {"from": bob, "value": "101 wei"})

    bid_after = auction_house_unpaused.auction()
    assert bid_after["bidder"] == alice
    assert bid_after["amount"] == 100


def test_create_bid_using_pending_returns(token, auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(40, 106, {"from": bob, "value": "106 wei"})
    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 106

    assert auction_house_unpaused.pending_returns(alice) == 100

    auction_house_unpaused.create_bid(40, 125, {"from": alice, "value": "25 wei"})

    auction_3 = auction_house_unpaused.auction()
    assert auction_3["bidder"] == alice
    assert auction_3["amount"] == 125
    assert auction_house_unpaused.pending_returns(alice) == 0

    chain.sleep(101)

    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(40) == alice


def test_create_bid_using_pending_returns_from_previous_auction(
    token, auction_house_unpaused, alice, bob
):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(40, 106, {"from": bob, "value": "106 wei"})
    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 106

    assert auction_house_unpaused.pending_returns(alice) == 100

    chain.sleep(101)

    auction_house_unpaused.settle_current_and_create_new_auction()

    auction_house_unpaused.create_bid(41, 100, {"from": alice})

    new_auction = auction_house_unpaused.auction()
    new_auction["bidder"] == alice
    new_auction["amount"] == 100

    assert auction_house_unpaused.pending_returns(alice) == 0

    chain.sleep(101)
    auction_house_unpaused.settle_current_and_create_new_auction()
    assert token.ownerOf(41) == alice


def test_create_bid_using_pending_returns_outbid(token, auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(40, 106, {"from": bob, "value": "106 wei"})
    auction_1 = auction_house_unpaused.auction()
    assert auction_1["bidder"] == bob
    assert auction_1["amount"] == 106

    auction_house_unpaused.create_bid(40, 125, {"from": alice, "value": "25 wei"})

    auction_house_unpaused.create_bid(40, 200, {"from": bob, "value": "200 wei"})

    assert auction_house_unpaused.pending_returns(alice) == 125

    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 200


def test_create_bid_using_pending_returns_not_enough(auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100

    auction_house_unpaused.create_bid(40, 106, {"from": bob, "value": "106 wei"})
    auction_2 = auction_house_unpaused.auction()
    assert auction_2["bidder"] == bob
    assert auction_2["amount"] == 106

    with brownie.reverts("Does not have enough pending returns to cover remainder"):
        auction_house_unpaused.create_bid(40, 126, {"from": alice, "value": "25 wei"})

    auction_3 = auction_house_unpaused.auction()
    assert auction_3["bidder"] == bob
    assert auction_3["amount"] == 106

    assert auction_house_unpaused.pending_returns(alice) == 100


# WITHDRAW


def test_create_second_bid_and_withdraw(auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    bid_before = auction_house_unpaused.auction()
    assert bid_before["bidder"] == alice
    assert bid_before["amount"] == 100
    alice_balance_before = alice.balance()

    auction_house_unpaused.create_bid(40, 1000, {"from": bob, "value": "1000 wei"})

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


def test_withdraw_stale(token, auction_house_unpaused, deployer, split_recipient, alice, bob):
    balance_of_alice_before = alice.balance()
    balance_of_deployer_before = deployer.balance()
    balance_of_split_recipient_before = split_recipient.balance()

    create_pending_returns(auction_house_unpaused, alice, bob)
    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()

    assert token.ownerOf(40) == bob
    assert deployer.balance() == balance_of_deployer_before + 10
    assert split_recipient.balance() == balance_of_split_recipient_before + 190
    assert alice.balance() == balance_of_alice_before - 100
    assert auction_house_unpaused.pending_returns(alice) == 100
    auction_house_unpaused.withdraw_stale([alice])
    assert auction_house_unpaused.pending_returns(alice) == 0
    assert alice.balance() == balance_of_alice_before - 5  # Alice gets a 5% penalty
    assert (
        deployer.balance() == balance_of_deployer_before + 15
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
    assert token.ownerOf(40) == deployer


def test_settle_auction_when_not_paused(auction_house_unpaused):
    with brownie.reverts("Auction house is not paused"):
        auction_house_unpaused.settle_auction()


def test_settle_current_and_create_new_auction_no_bid(
    token, deployer, auction_house_unpaused, split_recipient
):
    assert not auction_house_unpaused.auction()["settled"]
    old_auction_id = auction_house_unpaused.auction()["llama_id"]
    chain.sleep(1000)
    auction_house_unpaused.settle_current_and_create_new_auction()
    new_auction_id = auction_house_unpaused.auction()["llama_id"]
    assert not auction_house_unpaused.auction()["settled"]
    assert old_auction_id < new_auction_id
    # Token was transferred to owner when no one bid
    assert token.ownerOf(40) == deployer


def test_settle_auction_with_bid(token, deployer, auction_house_unpaused, alice, split_recipient):
    assert not auction_house_unpaused.auction()["settled"]
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    chain.sleep(1000)
    auction_house_unpaused.pause()
    deployer_balance_before = deployer.balance()
    split_recipient_before = split_recipient.balance()
    auction_house_unpaused.settle_auction()
    deployer_balance_after = deployer.balance()
    split_recipient_after = split_recipient.balance()
    assert auction_house_unpaused.auction()["settled"]
    assert token.ownerOf(40) == alice
    assert deployer_balance_after == deployer_balance_before + 5
    assert split_recipient_after == split_recipient_before + 95


def test_settle_current_and_create_new_auction_with_bid_smart_contract_owner(
    token, smart_contract_owner, auction_house_sc_owner, alice, split_recipient
):
    assert not auction_house_sc_owner.auction()["settled"]
    auction_house_sc_owner.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    chain.sleep(1000)
    deployer_balance_before = smart_contract_owner.balance()
    split_recipient_before = split_recipient.balance()
    auction_house_sc_owner.settle_current_and_create_new_auction()
    deployer_balance_after = smart_contract_owner.balance()
    split_recipient_after = split_recipient.balance()
    assert auction_house_sc_owner.auction()["llama_id"] == 41
    assert token.ownerOf(40) == alice
    assert deployer_balance_after == deployer_balance_before + 5
    assert split_recipient_after == split_recipient_before + 95


def test_settle_current_and_create_new_auction_with_bid(
    deployer, auction_house_unpaused, alice, split_recipient
):
    assert not auction_house_unpaused.auction()["settled"]
    old_auction_id = auction_house_unpaused.auction()["llama_id"]
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    chain.sleep(1000)
    deployer_balance_before = deployer.balance()
    split_recipient_before = split_recipient.balance()
    auction_house_unpaused.settle_current_and_create_new_auction()
    deployer_balance_after = deployer.balance()
    split_recipient_after = split_recipient.balance()
    new_auction_id = auction_house_unpaused.auction()["llama_id"]
    assert not auction_house_unpaused.auction()["settled"]
    assert old_auction_id < new_auction_id
    assert deployer_balance_after == deployer_balance_before + 5
    assert split_recipient_after == split_recipient_before + 95


def test_settle_current_and_create_new_auction_when_paused(token, auction_house):
    token.set_minter(auction_house)
    with brownie.reverts("Auction house is paused"):
        auction_house.settle_current_and_create_new_auction()


def test_settle_auction_multiple_bids(
    token, deployer, auction_house_unpaused, split_recipient, alice, bob
):
    assert not auction_house_unpaused.auction()["settled"]
    alice_balance_start = alice.balance()
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    auction_house_unpaused.create_bid(40, 1000, {"from": bob, "value": "1000 wei"})
    chain.sleep(1000)
    auction_house_unpaused.pause()
    deployer_balance_before = deployer.balance()
    split_recipient_before = split_recipient.balance()
    auction_house_unpaused.settle_auction()
    deployer_balance_after = deployer.balance()
    split_recipient_after = split_recipient.balance()
    alice_balance_before_withdraw = alice.balance()
    assert alice_balance_before_withdraw == alice_balance_start - 100
    auction_house_unpaused.withdraw({"from": alice})
    alice_balance_after_withdraw = alice.balance()
    assert alice_balance_after_withdraw == alice_balance_start
    assert auction_house_unpaused.auction()["settled"]
    assert token.ownerOf(40) == bob
    assert deployer_balance_after == deployer_balance_before + 50
    assert split_recipient_after == split_recipient_before + 950


def test_bidder_outbids_prev_bidder(
    token, auction_house_unpaused, deployer, split_recipient, alice, bob
):
    assert not auction_house_unpaused.auction()["settled"]
    alice_balance_start = alice.balance()
    bob_balance_start = bob.balance()
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    auction_house_unpaused.create_bid(40, 1000, {"from": bob, "value": "1000 wei"})
    auction_house_unpaused.create_bid(40, 2000, {"from": alice, "value": "2000 wei"})
    chain.sleep(1000)
    deployer_balance_before = deployer.balance()
    split_recipient_before = split_recipient.balance()
    auction_house_unpaused.settle_current_and_create_new_auction()
    deployer_balance_after = deployer.balance()
    split_recipient_after = split_recipient.balance()
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
    assert token.ownerOf(40) == alice
    assert deployer_balance_after == deployer_balance_before + 100
    assert split_recipient_after == split_recipient_before + 1900


# AUCTION EXTENSION


def test_create_bid_auction_extended(auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    starting_block_timestamp = chain.time()
    chain.sleep(90)
    auction_house_unpaused.create_bid(40, 1000, {"from": bob, "value": "1000 wei"})
    assert auction_house_unpaused.auction()["end_time"] == starting_block_timestamp + 190
    assert not auction_house_unpaused.auction()["settled"]


def test_create_bid_auction_not_extended(auction_house_unpaused, alice, bob):
    auction_house_unpaused.create_bid(40, 100, {"from": alice, "value": "100 wei"})
    chain.sleep(101)
    with brownie.reverts("Auction expired"):
        auction_house_unpaused.create_bid(40, 1000, {"from": bob, "value": "1000 wei"})
