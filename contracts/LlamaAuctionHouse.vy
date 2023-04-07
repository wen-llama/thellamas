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
    def transferFrom(
        from_addr: address, to_addr: address, token_id: uint256
    ): nonpayable


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


event AuctionDurationUpdated:
    _duration: uint256


event AuctionCreated:
    _llama_id: indexed(uint256)
    _start_time: uint256
    _end_time: uint256


event AuctionSettled:
    _llama_id: indexed(uint256)
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
MAX_CONCURRENT_AUCTIONS: constant(uint256) = 20

# Auction
llamas: public(Llama)
time_buffer: public(uint256)
reserve_price: public(uint256)
min_bid_increment_percentage: public(uint256)
duration: public(uint256)
auctions: public(Auction[MAX_CONCURRENT_AUCTIONS])
pending_returns: public(HashMap[address, uint256])

# WL Auction
wl_enabled: public(bool)
wl_signer: public(address)
wl_auctions_won: public(HashMap[address, uint256])

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
    _duration: uint256,
):
    self.llamas = _llamas
    self.time_buffer = _time_buffer
    self.reserve_price = _reserve_price
    self.min_bid_increment_percentage = _min_bid_increment_percentage
    self.duration = _duration
    self.owner = msg.sender
    self.paused = True
    self.wl_enabled = True
    self.wl_signer = msg.sender
    self.auctions = empty(Auction[MAX_CONCURRENT_AUCTIONS])


### AUCTION CREATION/SETTLEMENT ###


@external
@nonreentrant("lock")
def settle_current_and_create_new_auction(auction_index: uint256):
    """
    @dev Settle the current auction and start a new one.
      Throws if the auction house is paused.
    """

    assert self.paused == False, "Auction house is paused"

    self._settle_auction(auction_index)
    self._create_auction(auction_index)


@external
@nonreentrant("lock")
def settle_auction(auction_index: uint256):
    """
    @dev Settle the current auction.
      Throws if the auction house is not paused.
    """

    assert self.paused == True, "Auction house is not paused"
    assert auction_index < MAX_CONCURRENT_AUCTIONS, "Auction index is invalid"

    self._settle_auction(auction_index)


### BIDDING ###


@external
@payable
@nonreentrant("lock")
def create_wl_bid(auction_index: uint256, bid_amount: uint256, sig: Bytes[65]):
    """
    @dev Create a bid.
      Throws if the whitelist is not enabled.
      Throws if the `sig` is invalid.
      Throws if the `msg.sender` has already won two whitelist auctions.
    """

    assert self.wl_enabled == True, "WL auction is not enabled"
    assert self._check_wl_signature(sig, msg.sender), "Signature is invalid"
    assert self.wl_auctions_won[msg.sender] < 2, "Already won 2 WL auctions"

    self._create_bid(auction_index, bid_amount)


@external
@payable
@nonreentrant("lock")
def create_bid(auction_index: uint256, bid_amount: uint256):
    """
    @dev Create a bid.
      Throws if the whitelist is enabled.
    """

    assert self.wl_enabled == False, "Public auction is not enabled"
    assert auction_index < MAX_CONCURRENT_AUCTIONS, "Auction index is invalid"

    self._create_bid(auction_index, bid_amount)


### WITHDRAW ###


@external
@nonreentrant("lock")
def withdraw():
    """
    @dev Withdraw ETH after losing auction.
    """

    pending_amount: uint256 = self.pending_returns[msg.sender]
    self.pending_returns[msg.sender] = 0
    send(msg.sender, pending_amount)

    log Withdraw(msg.sender, pending_amount)


### ADMIN FUNCTIONS


@external
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
        send(_address, withdrawer_return)
        total_fee += fee

    send(self.owner, total_fee)


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

    for i in range(MAX_CONCURRENT_AUCTIONS):
        if self.auctions[i].start_time == 0 or self.auctions[i].settled:
            self._create_auction(i)


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


@external
def enable_wl():
    """
    @notice Admin function to enable the whitelist.
    """

    assert msg.sender == self.owner, "Caller is not the owner"

    self.wl_enabled = True


@external
def disable_wl():
    """
    @notice Admin function to disable the whitelist.
    """

    assert msg.sender == self.owner, "Caller is not the owner"

    self.wl_enabled = False


@external
def set_wl_signer(_wl_signer: address):
    """
    @notice Admin function to set the whitelist signer.
    """

    assert msg.sender == self.owner, "Caller is not the owner"

    self.wl_signer = _wl_signer


@internal
def _create_auction(auction_index: uint256):
    _llama_id: uint256 = self.llamas.mint()
    _start_time: uint256 = block.timestamp
    _end_time: uint256 = _start_time + self.duration

    self.auctions[auction_index] = Auction(
        {
            llama_id: _llama_id,
            amount: 0,
            start_time: _start_time,
            end_time: _end_time,
            bidder: empty(address),
            settled: False,
        }
    )

    # TODO: Nouns has an auto pause on error here.
    log AuctionCreated(_llama_id, _start_time, _end_time)


@internal
def _settle_auction(auction_index: uint256):
    auction: Auction = self.auctions[auction_index]
    assert auction.start_time != 0, "Auction hasn't begun"
    assert auction.settled == False, "Auction has already been settled"
    assert block.timestamp > auction.end_time, "Auction hasn't completed"

    self.auctions[auction_index].settled = True

    if auction.bidder == empty(address):
        self.llamas.transferFrom(self, self.owner, auction.llama_id)
    else:
        self.llamas.transferFrom(self, auction.bidder, auction.llama_id)
        if self.wl_enabled:
            self.wl_auctions_won[auction.bidder] += 1
    if auction.amount > 0:
        send(self.owner, auction.amount)

    log AuctionSettled(auction.llama_id, auction.bidder, auction.amount)


@internal
@payable
def _create_bid(auction_index: uint256, amount: uint256):
    if msg.value < amount:
        missing_amount: uint256 = amount - msg.value
        # Try to use the users pending returns
        assert (
            self.pending_returns[msg.sender] >= missing_amount
        ), "Does not have enough pending returns to cover remainder"
        self.pending_returns[msg.sender] -= missing_amount
    auction: Auction = self.auctions[auction_index]
    assert auction.settled == False, "Auction already settled"
    assert block.timestamp < auction.end_time, "Auction expired"
    assert amount >= self.reserve_price, "Must send at least reservePrice"
    assert amount >= auction.amount + (
        (auction.amount * self.min_bid_increment_percentage) / 100
    ), "Must send more than last bid by min_bid_increment_percentage amount"

    last_bidder: address = auction.bidder

    if last_bidder != empty(address):
        self.pending_returns[last_bidder] += auction.amount

    auction.amount = amount
    auction.bidder = msg.sender

    extended: bool = auction.end_time - block.timestamp < self.time_buffer

    if extended:
        auction.end_time = block.timestamp + self.time_buffer

    self.auctions[auction_index] = auction

    log AuctionBid(auction.llama_id, msg.sender, amount, extended)

    if extended:
        log AuctionExtended(auction.llama_id, auction.end_time)


@internal
def _pause():
    self.paused = True


@internal
def _unpause():
    self.paused = False


@internal
@view
def _check_wl_signature(sig: Bytes[65], sender: address) -> bool:
    r: uint256 = convert(slice(sig, 0, 32), uint256)
    s: uint256 = convert(slice(sig, 32, 32), uint256)
    v: uint256 = convert(slice(sig, 64, 1), uint256)
    ethSignedHash: bytes32 = keccak256(
        concat(
            b"\x19Ethereum Signed Message:\n32",
            keccak256(_abi_encode("whitelist:", sender)),
        )
    )

    return self.wl_signer == ecrecover(ethSignedHash, v, r, s)
