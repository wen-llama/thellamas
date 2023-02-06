import brownie
from brownie import chain, ZERO_ADDRESS
import pytest

# Initialization vars

def test_owner(auction_house, deployer):
  assert auction_house.owner() == deployer

def test_llamas(auction_house, token):
  assert auction_house.llamas() == token

def test_weth_address(auction_house, charlie):
  assert auction_house.weth() == charlie

def test_time_buffer(auction_house):
  assert auction_house.time_buffer() == 100

def test_bid_after(auction_house):
  assert auction_house.reserve_price() == 100

def test_min_bid_increment_percentage(auction_house):
  assert auction_house.min_bid_increment_percentage() == 100

def test_duration(auction_house):
  assert auction_house.duration() == 100

def test_paused(auction_house):
  assert auction_house.paused() == True

# Pause

def test_pause_unpause(auction_house, token, deployer, minted_token_id):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.paused() == False
  assert auction_house.auction()["llama_id"] == minted_token_id
  auction_house.pause()
  assert auction_house.paused() == True

def test_pause_not_owner(auction_house, alice):
  with brownie.reverts():
    auction_house.pause({"from": alice})

def test_unpause_not_owner(auction_house, alice):
  with brownie.reverts():
    auction_house.unpause({"from": alice})

# Owner control

def test_set_time_buffer(auction_house):
  auction_house.set_time_buffer(200)
  assert auction_house.time_buffer() == 200

def test_set_time_buffer_not_owner(auction_house, alice):
  with brownie.reverts():
    auction_house.set_time_buffer(200, {"from": alice})

def test_set_reserve_price(auction_house):
  auction_house.set_reserve_price(200)
  assert auction_house.reserve_price() == 200

def test_set_reserve_price_not_owner(auction_house, alice):
  with brownie.reverts():
    auction_house.set_reserve_price(200, {"from": alice})

def test_set_min_bid_increment_percentage(auction_house):
  auction_house.set_min_bid_increment_percentage(200)
  assert auction_house.min_bid_increment_percentage() == 200

def test_set_min_bid_increment_percentage_not_owner(auction_house, alice):
  with brownie.reverts():
    auction_house.set_min_bid_increment_percentage(200, {"from": alice})

def test_create_bid(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  current_auction = auction_house.auction()
  assert current_auction["bidder"] == alice
  assert current_auction["amount"] == 100

def test_create_bid_send_more_than_last_bid(token, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  firt_bid = auction_house.auction()
  assert firt_bid["bidder"] == alice
  assert firt_bid["amount"] == 100

  auction_house.create_bid(20, {"from": bob, "value": "1000 wei"})
  second_bid = auction_house.auction()
  assert second_bid["bidder"] == bob 
  assert second_bid["amount"] == 1000

def test_create_bid_wrong_llama_id(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause() 
  with brownie.reverts("Llama not up for auction"):
    auction_house.create_bid(19, {"from": alice, "value": "100 wei"})

def test_create_bid_auction_expired(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause() 
  # Expire the auction
  chain.sleep(1000)
  with brownie.reverts("Auction expired"):
   auction_house.create_bid(20, {"from": alice, "value": "100 wei"}) 

def test_create_bid_value_too_low(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause() 
  with brownie.reverts("Must send at least reservePrice"):
   auction_house.create_bid(20, {"from": alice, "value": "1 wei"})

def test_create_bid_not_over_prev_bid(token, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  bid_before = auction_house.auction()
  assert bid_before["bidder"] == alice
  assert bid_before["amount"] == 100

  with brownie.reverts("Must send more than last bid by min_bid_increment_percentage amount"):
    auction_house.create_bid(20, {"from": bob, "value": "101 wei"})

  bid_after = auction_house.auction()
  assert bid_after["bidder"] == alice
  assert bid_after["amount"] == 100

def test_create_second_bid_and_withdraw(token, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  bid_before = auction_house.auction()
  assert bid_before["bidder"] == alice
  assert bid_before["amount"] == 100
  alice_balance_before = alice.balance()

  auction_house.create_bid(20, {"from": bob, "value": "1000 wei"})

  bid_after = auction_house.auction()
  assert bid_after["bidder"] == bob
  assert bid_after["amount"] == 1000

  auction_house.withdraw({"from": alice})

  alice_balance_after = alice.balance()

  assert alice_balance_after == alice_balance_before + 100

def test_withdraw_zero_pending(auction_house, alice):
  balance_before = alice.balance()
  auction_house.withdraw({"from":alice})
  balance_after = alice.balance()
  assert balance_before == balance_after

def test_settle_auction_no_bid(token, auction_house):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.auction()["settled"] == False
  chain.sleep(1000)
  auction_house.pause()
  auction_house.settle_auction()
  assert auction_house.auction()["settled"] == True

def test_settle_current_and_create_new_auction_no_bid(token, auction_house):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.auction()["settled" ] == False
  old_auction_id = auction_house.auction()["llama_id"]
  chain.sleep(1000)
  auction_house.settle_current_and_create_new_auction()
  new_auction_id = auction_house.auction()["llama_id"]
  assert auction_house.auction()["settled"] == False
  assert old_auction_id < new_auction_id

def test_settle_auction_with_bid(token, deployer, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.auction()["settled"] == False
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  chain.sleep(1000)
  auction_house.pause()
  deployer_balance_before = deployer.balance()
  auction_house.settle_auction()
  deployer_balance_after = deployer.balance()
  assert auction_house.auction()["settled"] == True
  assert token.ownerOf(20) == alice
  assert deployer_balance_after == deployer_balance_before + 100

def test_settle_current_and_create_new_auction_with_bid(token, deployer, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.auction()["settled" ] == False
  old_auction_id = auction_house.auction()["llama_id"]
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  chain.sleep(1000)
  deployer_balance_before = deployer.balance()
  auction_house.settle_current_and_create_new_auction()
  deployer_balance_after = deployer.balance()
  new_auction_id = auction_house.auction()["llama_id"]
  assert auction_house.auction()["settled"] == False
  assert old_auction_id < new_auction_id
  assert deployer_balance_after == deployer_balance_before + 100

def test_settle_auction_multiple_bids(token, deployer, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.auction()["settled"] == False
  alice_balance_start = alice.balance()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  auction_house.create_bid(20, {"from": bob, "value": "1000 wei"})
  chain.sleep(1000)
  auction_house.pause()
  deployer_balance_before = deployer.balance()
  auction_house.settle_auction()
  deployer_balance_after = deployer.balance()
  alice_balance_before_withdraw = alice.balance()
  assert alice_balance_before_withdraw == alice_balance_start - 100
  auction_house.withdraw({"from": alice})
  alice_balance_after_withdraw = alice.balance()
  assert alice_balance_after_withdraw == alice_balance_start
  assert auction_house.auction()["settled"] == True
  assert token.ownerOf(20) == bob
  assert deployer_balance_after == deployer_balance_before + 1000

def test_bidder_outbids_prev_bidder(token, auction_house, deployer, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.auction()["settled"] == False
  alice_balance_start = alice.balance()
  bob_balance_start = bob.balance()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  auction_house.create_bid(20, {"from": bob, "value": "1000 wei"})
  auction_house.create_bid(20, {"from": alice, "value": "2000 wei"})
  chain.sleep(1000)
  deployer_balance_before = deployer.balance()
  auction_house.settle_current_and_create_new_auction()
  deployer_balance_after = deployer.balance()
  alice_balance_before_withdraw = alice.balance()
  bob_balance_before_withdraw = bob.balance()
  assert alice_balance_before_withdraw == alice_balance_start - 2100
  assert bob_balance_before_withdraw == bob_balance_start - 1000
  auction_house.withdraw({"from": alice})
  auction_house.withdraw({"from": bob})
  alice_balance_after_withdraw = alice.balance()
  bob_balance_after_withdraw = bob.balance()
  assert alice_balance_after_withdraw == alice_balance_start - 2000
  assert bob_balance_after_withdraw == bob_balance_start
  assert auction_house.auction()["settled"] == False
  assert token.ownerOf(20) == alice
  assert deployer_balance_after == deployer_balance_before + 2000


  # TODO: Write some more tests dealing with auction expiration