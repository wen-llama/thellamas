# @version 0.3.10

owner: public(address)


@external
def __init__():
    pass


@external
@payable
def __default__():
    # Do something that wastes gas.
    self.owner = msg.sender
