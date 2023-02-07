# @version 0.3.7
# @notice The Llamas auction house 
# @author The Llamas
# @license MIT
#
# ___________.__                 .____     .__
# \__    ___/|  |__    ____      |    |    |  |  _____     _____  _____     ______
#   |    |   |  |  \ _/ __ \     |    |    |  |  \__  \   /     \ \__  \   /  ___/
#   |    |   |   Y  \\  ___/     |    |___ |  |__ / __ \_|  Y Y  \ / __ \_ \___ \
#   |____|   |___|  / \___  >    |_______ \|____/(____  /|__|_|  /(____  //____  >
#                 \/      \/             \/           \/       \/      \/      \/

interface Llama:
  def mint() -> uint256: nonpayable
  def burn(token_id: uint256): nonpayable
  def transferFrom(from_addr: address, to_addr: address, token_id: uint256): nonpayable

struct Auction:
  llama_id: uint256
  amount: uint256
  start_time: uint256
  end_time: uint256
  bidder: address
  settled: bool

event AuctionBid:
  _llama_id: indexed(uint256)
  _sender: address
  _value: uint256
  _extended: bool

event AuctionExtended:
  _llama_id: indexed(uint256)
  _end_time: uint256

event AuctionTimeBufferUpdated:
  _time_buffer: uint256

event AuctionReservePriceUpdated:
  _reserve_price: uint256

event AuctionMinBidIncrementPercentageUpdated:
  _min_bid_increment_percentage: uint256

event AuctionCreated:
  _llama_id: indexed(uint256)
  _start_time: uint256
  _end_time: uint256

event AuctionSettled:
  _llama_id: indexed(uint256)
  _winner: address
  _amount: uint256

# Auction
llamas: public(Llama)
time_buffer: public(uint256)
reserve_price: public(uint256)
min_bid_increment_percentage: public(uint256)
duration: public(uint256)
auction: public(Auction)
pending_returns: public(HashMap[address, uint256])

# Permissions
owner: public(address)

# Pause
paused: public(bool)

@external
def __init__(
  _llamas: Llama,
  _time_buffer: uint256,
  _reserve_price: uint256,
  _min_bid_increment_percentage: uint256,
  _duration: uint256
):

  self.llamas = _llamas
  self.time_buffer = _time_buffer
  self.reserve_price = _reserve_price
  self.min_bid_increment_percentage = _min_bid_increment_percentage
  self.duration = _duration
  self.owner = msg.sender
  self.paused = True

@external
@nonreentrant("lock")
def settle_current_and_create_new_auction():
  assert self.paused == False, "Auction house is paused"

  self._settle_auction()
  self._create_auction()

@external
@nonreentrant("lock")
def settle_auction():
  assert self.paused == True, "Auction house is not paused"

  self._settle_auction()

@external
@payable
@nonreentrant("lock")
def create_bid(llama_id: uint256):
  assert self.auction.llama_id == llama_id, "Llama not up for auction"
  assert block.timestamp < self.auction.end_time, "Auction expired"
  assert msg.value >= self.reserve_price, "Must send at least reservePrice"
  assert msg.value >= self.auction.amount + ((self.auction.amount * self.min_bid_increment_percentage) / 100), "Must send more than last bid by min_bid_increment_percentage amount"

  last_bidder: address = self.auction.bidder

  if (last_bidder != empty(address)):
    self.pending_returns[last_bidder] += self.auction.amount

  self.auction.amount = msg.value
  self.auction.bidder = msg.sender

  extended: bool = self.auction.end_time - block.timestamp < self.time_buffer

  if (extended):
    self.auction.end_time = block.timestamp + self.time_buffer

  log AuctionBid(self.auction.llama_id, msg.sender, msg.value, extended)

  if (extended):
    log AuctionExtended(self.auction.llama_id, self.auction.end_time)

@external
@nonreentrant("lock")
def withdraw():
  pending_amount: uint256 = self.pending_returns[msg.sender]
  self.pending_returns[msg.sender] = 0
  send(msg.sender, pending_amount)

@external
def pause(): 
  assert msg.sender == self.owner
  self._pause()

@external
def unpause():
  assert msg.sender == self.owner
  self._unpause()

  if (self.auction.start_time == 0 or self.auction.settled):
    self._create_auction()

@external
def set_time_buffer(_time_buffer: uint256):
  assert msg.sender == self.owner

  self.time_buffer = _time_buffer

  log AuctionTimeBufferUpdated(_time_buffer)

@external
def set_reserve_price(_reserve_price: uint256):
  assert msg.sender == self.owner

  self.reserve_price = _reserve_price

  log AuctionReservePriceUpdated(_reserve_price)

@external
def set_min_bid_increment_percentage(_min_bid_increment_percentage: uint256):
  assert msg.sender == self.owner

  self.min_bid_increment_percentage = _min_bid_increment_percentage

  log AuctionMinBidIncrementPercentageUpdated(_min_bid_increment_percentage)

@internal
def _create_auction():
  _llama_id: uint256 = self.llamas.mint()
  _start_time: uint256 = block.timestamp
  _end_time: uint256 = _start_time + self.duration

  self.auction = Auction({
    llama_id: _llama_id,
    amount: 0,
    start_time: _start_time,
    end_time: _end_time,
    bidder: empty(address),
    settled: False
  })

  # TODO: Nouns has an auto pause on error here.
  log AuctionCreated(_llama_id, _start_time, _end_time)

@internal
def _settle_auction():
  assert self.auction.start_time != 0, "Auction hasn't begun"
  assert self.auction.settled == False, "Auction has already been settled"
  assert block.timestamp > self.auction.end_time, "Auction hasn't completed"

  self.auction.settled = True

  if (self.auction.bidder == empty(address)):
    self.llamas.burn(self.auction.llama_id)
  else:
    self.llamas.transferFrom(self, self.auction.bidder, self.auction.llama_id)

  if (self.auction.amount > 0):
    send(self.owner, self.auction.amount)

  log AuctionSettled(self.auction.llama_id, self.auction.bidder, self.auction.amount)

@internal
def _pause():
  self.paused = True

@internal
def _unpause():
  self.paused = False
