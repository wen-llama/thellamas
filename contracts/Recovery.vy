# @version 0.3.7

# @notice Contract to recover ETH stuck at deployed address
# @author The Llamas
# @license MIT
#
# ___________.__                 .____     .__
# \__    ___/|  |__    ____      |    |    |  |  _____     _____  _____     ______
#   |    |   |  |  \ _/ __ \     |    |    |  |  \__  \   /     \ \__  \   /  ___/
#   |    |   |   Y  \\  ___/     |    |___ |  |__ / __ \_|  Y Y  \ / __ \_ \___ \
#   |____|   |___|  / \___  >    |_______ \|____/(____  /|__|_|  /(____  //____  >
#                 \/      \/             \/           \/       \/      \/      \/


admin: public(address)


@external
def __init__():
    self.admin = msg.sender


@external
def recover():
    """
    @notice Transfer stuck ETH to msg.sender
    """
    assert msg.sender == self.admin, "Caller is not the admin"
    selfdestruct(self.admin)
