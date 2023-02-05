import brownie
from brownie import chain
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

def test_settle_auction(token, auction_house):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.auction()["settled"] == False
  chain.sleep(1000)
  auction_house.settle_auction()
  auction_house.auction()["settled"] == True
