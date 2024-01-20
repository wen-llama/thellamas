# @version 0.3.10

# @notice The tokens auction house
# @author The tokens
# @license MIT
#
# ___________.__                 .____     .__
# \__    ___/|  |__    ____      |    |    |  |  _____     _____  _____     ______
#   |    |   |  |  \ _/ __ \     |    |    |  |  \__  \   /     \ \__  \   /  ___/
#   |    |   |   Y  \\  ___/     |    |___ |  |__ / __ \_|  Y Y  \ / __ \_ \___ \
#   |____|   |___|  / \___  >    |_______ \|____/(____  /|__|_|  /(____  //____  >
#                 \/      \/             \/           \/       \/      \/      \/


interface Token:
    def mint() -> uint256: nonpayable
    def burn(token_id: uint256): nonpayable
    def transferFrom(
        from_addr: address, to_addr: address, token_id: uint256
    ): nonpayable


struct Auction:
        token_id: uint256
        amount: uint256
        start_time: uint256
        end_time: uint256
        bidder: address
        settled: bool


event AuctionBid:
    _token_id: indexed(uint256)
    _sender: address
    _value: uint256
    _extended: bool


event AuctionExtended:
    _token_id: indexed(uint256)
    _end_time: uint256


event AuctionTimeBufferUpdated:
    _time_buffer: uint256


event AuctionReservePriceUpdated:
    _reserve_price: uint256


event AuctionMinBidIncrementPercentageUpdated:
    _min_bid_increment_percentage: uint256


event AuctionDurationUpdated:
    _duration: uint256


event AuctionCreated:
    _token_id: indexed(uint256)
    _start_time: uint256
    _end_time: uint256


event AuctionSettled:
    _token_id: indexed(uint256)
    _winner: address
    _amount: uint256


event Withdraw:
    _withdrawer: indexed(address)
    _amount: uint256


# Technically vyper doesn't need this as it is automatic
# in all recent vyper versions, but Etherscan verification
# will bork without it.
IDENTITY_PRECOMPILE: constant(
    address
) = 0x0000000000000000000000000000000000000004

ADMIN_MAX_WITHDRAWALS: constant(uint256) = 100

# Auction
tokens: public(Token)
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

# Proceeds
proceeds_receiver: public(address)
proceeds_receiver_split_percentage: public(uint256)


@external
def __init__(
    _tokens: Token,
    _time_buffer: uint256,
    _reserve_price: uint256,
    _min_bid_increment_percentage: uint256,
    _duration: uint256,
    _proceeds_receiver: address,
    _proceeds_receiver_split_percentage: uint256,
):
    self.tokens = _tokens
    self.time_buffer = _time_buffer
    self.reserve_price = _reserve_price
    self.min_bid_increment_percentage = _min_bid_increment_percentage
    self.duration = _duration
    self.owner = msg.sender
    self.paused = True
    self.proceeds_receiver = _proceeds_receiver
    self.proceeds_receiver_split_percentage = _proceeds_receiver_split_percentage  # This should be a number between 1-99


### AUCTION CREATION/SETTLEMENT ###


@external
@nonreentrant("lock")
def settle_current_and_create_new_auction():
    """
    @dev Settle the current auction and start a new one.
      Throws if the auction house is paused.
    """

    assert self.paused == False, "Auction house is paused"

    self._settle_auction()
    self._create_auction()


@external
@nonreentrant("lock")
def settle_auction():
    """
    @dev Settle the current auction.
      Throws if the auction house is not paused.
    """

    assert self.paused == True, "Auction house is not paused"

    self._settle_auction()


### BIDDING ###


@external
@payable
@nonreentrant("lock")
def create_bid(token_id: uint256, bid_amount: uint256):
    """
    @dev Create a bid.
      Throws if the whitelist is enabled.
    """

    self._create_bid(token_id, bid_amount)


### WITHDRAW ###


@external
@nonreentrant("lock")
def withdraw():
    """
    @dev Withdraw ETH after losing auction.
    """

    pending_amount: uint256 = self.pending_returns[msg.sender]
    self.pending_returns[msg.sender] = 0
    raw_call(msg.sender, b"", value=pending_amount)

    log Withdraw(msg.sender, pending_amount)


### ADMIN FUNCTIONS


@external
@nonreentrant("lock")
def withdraw_stale(addresses: DynArray[address, ADMIN_MAX_WITHDRAWALS]):
    """
    @dev Admin function to withdraw pending returns that have not been claimed.
    """

    assert msg.sender == self.owner, "Caller is not the owner"

    total_fee: uint256 = 0
    for _address in addresses:
        pending_amount: uint256 = self.pending_returns[_address]
        if pending_amount == 0:
            continue
        # Take a 5% fee
        fee: uint256 = (pending_amount * 5) / 100
        withdrawer_return: uint256 = pending_amount - fee
        self.pending_returns[_address] = 0
        raw_call(_address, b"", value=withdrawer_return)
        total_fee += fee

    raw_call(self.owner, b"", value=total_fee)


@external
def pause():
    """
    @notice Admin function to pause to auction house.
    """

    assert msg.sender == self.owner, "Caller is not the owner"
    self._pause()


@external
def unpause():
    """
    @notice Admin function to unpause to auction house.
    """

    assert msg.sender == self.owner, "Caller is not the owner"
    self._unpause()

    if self.auction.start_time == 0 or self.auction.settled:
        self._create_auction()


@external
def set_time_buffer(_time_buffer: uint256):
    """
    @notice Admin function to set the time buffer.
    """

    assert msg.sender == self.owner, "Caller is not the owner"

    self.time_buffer = _time_buffer

    log AuctionTimeBufferUpdated(_time_buffer)


@external
def set_reserve_price(_reserve_price: uint256):
    """
    @notice Admin function to set the reserve price.
    """

    assert msg.sender == self.owner, "Caller is not the owner"

    self.reserve_price = _reserve_price

    log AuctionReservePriceUpdated(_reserve_price)


@external
def set_min_bid_increment_percentage(_min_bid_increment_percentage: uint256):
    """
    @notice Admin function to set the min bid increment percentage.
    """

    assert msg.sender == self.owner, "Caller is not the owner"
    assert (
        _min_bid_increment_percentage >= 2
        and _min_bid_increment_percentage <= 15
    ), "_min_bid_increment_percentage out of range"

    self.min_bid_increment_percentage = _min_bid_increment_percentage

    log AuctionMinBidIncrementPercentageUpdated(_min_bid_increment_percentage)


@external
def set_duration(_duration: uint256):
    """
    @notice Admin function to set the duration.
    """

    assert msg.sender == self.owner, "Caller is not the owner"
    assert _duration >= 3600 and _duration <= 259200, "_duration out of range"

    self.duration = _duration

    log AuctionDurationUpdated(_duration)


@external
def set_owner(_owner: address):
    """
    @notice Admin function to set the owner
    """

    assert msg.sender == self.owner, "Caller is not the owner"
    assert _owner != empty(address), "Cannot set owner to zero address"

    self.owner = _owner


@internal
def _create_auction():
    _token_id: uint256 = self.tokens.mint()
    _start_time: uint256 = block.timestamp
    _end_time: uint256 = _start_time + self.duration

    self.auction = Auction(
        {
            token_id: _token_id,
            amount: 0,
            start_time: _start_time,
            end_time: _end_time,
            bidder: empty(address),
            settled: False,
        }
    )

    log AuctionCreated(_token_id, _start_time, _end_time)


@internal
def _settle_auction():
    assert self.auction.start_time != 0, "Auction hasn't begun"
    assert self.auction.settled == False, "Auction has already been settled"
    assert block.timestamp > self.auction.end_time, "Auction hasn't completed"

    self.auction.settled = True

    if self.auction.bidder == empty(address):
        self.tokens.transferFrom(self, self.owner, self.auction.token_id)
    else:
        self.tokens.transferFrom(
            self, self.auction.bidder, self.auction.token_id
        )
    if self.auction.amount > 0:
        fee: uint256 = (
            self.auction.amount * self.proceeds_receiver_split_percentage
        ) / 100
        owner_amount: uint256 = self.auction.amount - fee
        raw_call(self.owner, b"", value=owner_amount)
        raw_call(self.proceeds_receiver, b"", value=fee)

    log AuctionSettled(
        self.auction.token_id, self.auction.bidder, self.auction.amount
    )


@internal
@payable
def _create_bid(token_id: uint256, amount: uint256):
    if msg.value < amount:
        missing_amount: uint256 = amount - msg.value
        # Try to use the users pending returns
        assert (
            self.pending_returns[msg.sender] >= missing_amount
        ), "Does not have enough pending returns to cover remainder"
        self.pending_returns[msg.sender] -= missing_amount
    assert self.auction.token_id == token_id, "Token not up for auction"
    assert block.timestamp < self.auction.end_time, "Auction expired"
    assert amount >= self.reserve_price, "Must send at least reservePrice"
    assert amount >= self.auction.amount + (
        (self.auction.amount * self.min_bid_increment_percentage) / 100
    ), "Must send more than last bid by min_bid_increment_percentage amount"

    last_bidder: address = self.auction.bidder

    if last_bidder != empty(address):
        self.pending_returns[last_bidder] += self.auction.amount

    self.auction.amount = amount
    self.auction.bidder = msg.sender

    extended: bool = self.auction.end_time - block.timestamp < self.time_buffer

    if extended:
        self.auction.end_time = block.timestamp + self.time_buffer

    log AuctionBid(self.auction.token_id, msg.sender, amount, extended)

    if extended:
        log AuctionExtended(self.auction.token_id, self.auction.end_time)


@internal
def _pause():
    self.paused = True


@internal
def _unpause():
    self.paused = False
