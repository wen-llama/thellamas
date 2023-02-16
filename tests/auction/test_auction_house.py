import brownie
from brownie import chain, web3, ZERO_ADDRESS
import pytest
from eth_account.messages import encode_defunct
from eth_account import Account
from eth_abi import encode

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
  assert auction_house.min_bid_increment_percentage() == 100

def test_duration(auction_house):
  assert auction_house.duration() == 100

def test_paused(auction_house):
  assert auction_house.paused() == True

def test_wl_enabled(auction_house):
  assert auction_house.wl_enabled() == True

def test_wl_signer(auction_house, deployer):
  assert auction_house.wl_signer() == deployer

# Pause

def test_pause_unpause(auction_house, token, deployer, minted_token_id):
  token.set_minter(auction_house)
  auction_house.unpause()
  assert auction_house.paused() == False
  assert auction_house.auction()["llama_id"] == minted_token_id
  assert auction_house.auction()["settled"] == False
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

def test_enable_disable_wl(auction_house):
  assert auction_house.wl_enabled() == True
  auction_house.disable_wl()
  assert auction_house.wl_enabled() == False
  auction_house.enable_wl()
  assert auction_house.wl_enabled() == True


# WL Bidding

def test_create_wl_bid(token, auction_house, alice, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  auction_house.create_wl_bid(20, signed_message.signature, {"from": alice, "value": "100 wei"})
  current_auction = auction_house.auction()
  assert current_auction["bidder"] == alice
  assert current_auction["amount"] == 100

def test_create_wl_bid_invalid_signature(token, auction_house, alice, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  alice_encoded = encode(["string", "address"], ["blah:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  with brownie.reverts("Signature is invalid"):
    auction_house.create_wl_bid(20, signed_message.signature, {"from": alice, "value": "100 wei"})

def test_create_wl_bid_wl_not_enabled(token, auction_house, alice, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
  alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  with brownie.reverts("WL auction is not enabled"):
    auction_house.create_wl_bid(20, signed_message.signature, {"from": alice, "value": "100 wei"})

def test_create_wl_bid_wrong_llama_id(token, auction_house, alice, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  with brownie.reverts("Llama not up for auction"):
    auction_house.create_wl_bid(21, signed_message.signature, {"from": alice, "value": "100 wei"})

def test_create_wl_bid_auction_expired(token, auction_house, alice, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  chain.sleep(1000)
  with brownie.reverts("Auction expired"):
    auction_house.create_wl_bid(20, signed_message.signature, {"from": alice, "value": "100 wei"}) 

def test_create_wl_bid_less_than_reserve_price(token, auction_house, alice, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  with brownie.reverts("Must send at least reservePrice"):
    auction_house.create_wl_bid(20, signed_message.signature, {"from": alice, "value": "99 wei"})

def test_create_wl_bid_not_over_prev_bid(token, auction_house, alice, bob, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  alice_signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  auction_house.create_wl_bid(20, alice_signed_message.signature, {"from": alice, "value": "100 wei"})
  bid_before = auction_house.auction()
  assert bid_before["bidder"] == alice
  assert bid_before["amount"] == 100

  bob_encoded = encode(["string", "address"], ["whitelist:", bob.address])
  bob_hashed = web3.keccak(bob_encoded)
  bob_signable_message = encode_defunct(bob_hashed)
  bob_signed_message = Account.sign_message(bob_signable_message, deployer.private_key)

  with brownie.reverts("Must send more than last bid by min_bid_increment_percentage amount"):
    auction_house.create_wl_bid(20, bob_signed_message.signature, {"from": bob, "value": "101 wei"})

  bid_after = auction_house.auction()
  assert bid_after["bidder"] == alice
  assert bid_after["amount"] == 100

def test_create_wl_bid_can_only_win_two_wl_auctions(token, auction_house, alice, bob, deployer):
  token.set_minter(auction_house)
  auction_house.unpause()
  alice_encoded = encode(["string", "address"], ["whitelist:", alice.address])
  alice_hashed = web3.keccak(alice_encoded)
  alice_signable_message = encode_defunct(alice_hashed)
  alice_signed_message = Account.sign_message(alice_signable_message, deployer.private_key)
  auction_house.create_wl_bid(20, alice_signed_message.signature, {"from": alice, "value": "100 wei"})
  bid_before = auction_house.auction()
  assert bid_before["bidder"] == alice
  assert bid_before["amount"] == 100

  chain.sleep(1000)
  auction_house.settle_current_and_create_new_auction()

  assert token.ownerOf(20) == alice
  assert auction_house.wl_auctions_won(alice) == 1
  assert auction_house.auction()["llama_id"] == 21

  auction_house.create_wl_bid(21, alice_signed_message.signature, {"from": alice, "value": "100 wei"})
  chain.sleep(1000)
  auction_house.settle_current_and_create_new_auction()

  assert token.ownerOf(21) == alice
  assert auction_house.wl_auctions_won(alice) == 2
  assert auction_house.auction()["llama_id"] == 22

  # Alice can't win any more wl auctions.
  with brownie.reverts("Already won 2 WL auctions"):
    auction_house.create_wl_bid(22, alice_signed_message.signature, {"from": alice, "value": "100 wei"})

  # Bob can still win a wl auction.
  bob_encoded = encode(["string", "address"], ["whitelist:", bob.address])
  bob_hashed = web3.keccak(bob_encoded)
  bob_signable_message = encode_defunct(bob_hashed)
  bob_signed_message = Account.sign_message(bob_signable_message, deployer.private_key)

  auction_house.create_wl_bid(22, bob_signed_message.signature, {"from": bob, "value": "100 wei"})
  chain.sleep(1000)
  auction_house.settle_current_and_create_new_auction()

  assert token.ownerOf(22) == bob
  assert auction_house.wl_auctions_won(bob) == 1
  assert auction_house.auction()["llama_id"] == 23
  

# Public Bidding

def test_create_bid(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  current_auction = auction_house.auction()
  assert current_auction["bidder"] == alice
  assert current_auction["amount"] == 100

def test_create_bid_wl_enabled(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause()
  with brownie.reverts("Public auction is not enabled"):
    auction_house.create_bid(20, {"from": alice, "value": "100 wei"})

def test_create_bid_send_more_than_last_bid(token, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
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
  auction_house.disable_wl()
  with brownie.reverts("Llama not up for auction"):
    auction_house.create_bid(19, {"from": alice, "value": "100 wei"})

def test_create_bid_auction_expired(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause() 
  auction_house.disable_wl()
  # Expire the auction
  chain.sleep(1000)
  with brownie.reverts("Auction expired"):
   auction_house.create_bid(20, {"from": alice, "value": "100 wei"}) 

def test_create_bid_value_too_low(token, auction_house, alice):
  token.set_minter(auction_house)
  auction_house.unpause() 
  auction_house.disable_wl()
  with brownie.reverts("Must send at least reservePrice"):
   auction_house.create_bid(20, {"from": alice, "value": "1 wei"})

def test_create_bid_not_over_prev_bid(token, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
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
  auction_house.disable_wl()
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

def test_settle_auction_when_not_paused(auction_house, token):
  token.set_minter(auction_house)
  auction_house.unpause()
  with brownie.reverts("Auction house is not paused"):
    auction_house.settle_auction()

def test_settle_current_and_create_new_auction_no_bid(token, auction_house):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
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
  auction_house.disable_wl()
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
  auction_house.disable_wl()
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

def test_settle_current_and_create_new_auction_when_paused(token, auction_house):
  token.set_minter(auction_house)
  with brownie.reverts("Auction house is paused"):
    auction_house.settle_current_and_create_new_auction()

def test_settle_auction_multiple_bids(token, deployer, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
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
  auction_house.disable_wl()
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

def test_create_bid_auction_extended(token, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  starting_block_timestamp = chain.time()
  chain.sleep(90)
  auction_house.create_bid(20, {"from": bob, "value": "1000 wei"})
  assert auction_house.auction()["end_time"] == starting_block_timestamp + 190
  assert auction_house.auction()["settled"] == False

def test_create_bid_auction_not_extended(token, auction_house, alice, bob):
  token.set_minter(auction_house)
  auction_house.unpause()
  auction_house.disable_wl()
  auction_house.create_bid(20, {"from": alice, "value": "100 wei"})
  chain.sleep(101)
  with brownie.reverts("Auction expired"):
    auction_house.create_bid(20, {"from": bob, "value": "1000 wei"})