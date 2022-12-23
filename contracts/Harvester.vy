# @version 0.3.7
# @notice Claim rewards from veCRV/Votium, swap them to CRV, lock 80% in veCRV and 20% into uCRV 
# @dev Interacts with Votium, Curve, and Llama Airforce
# @author The Llamas
# @license MIT
#
# ___________.__                 .____     .__
# \__    ___/|  |__    ____      |    |    |  |  _____     _____  _____     ______
#   |    |   |  |  \ _/ __ \     |    |    |  |  \__  \   /     \ \__  \   /  ___/
#   |    |   |   Y  \\  ___/     |    |___ |  |__ / __ \_|  Y Y  \ / __ \_ \___ \
#   |____|   |___|  / \___  >    |_______ \|____/(____  /|__|_|  /(____  //____  >
#                 \/      \/             \/           \/       \/      \/      \/

struct claimParam:
  token: address
  index: uint256
  amount: uint256
  merkleProof: bytes32

interface IMultiMerkleStash:
  def claim(token: address, index: uint256, account: address, amount: uint256, merkleProof: bytes32): nonpayable
  def claimMulti(account: address, claims: claimParam[50]): nonpayable

# Permissions
owner: public(address)

# Claim contracts
votium_merkle_stash: IMultiMerkleStash
curve_fee_distributor: constant(address) = 0xA464e6DCda8AC41e03616F95f4BC98a13b8922Dc

# Deposit contracts
ve_crv: constant(address) = 0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2
ucrv_vault: constant(address) = 0x83507cc8C8B67Ed48BADD1F59F684D5d02884C81

# Curve pools
three_pool: constant(address) = 0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7
tri_crypto: constant(address) = 0xD51a44d3FaE010294C616388b506AcdA1bfAAE46
crv_eth: constant(address) = 0x8301AE4fc9c624d1D396cbDAa1ed877821D7C511
cvx_crv: constant(address) = 0x9D0464996170c6B9e75eED71c68B99dDEDf279e8

@external
def __init__():
  self.owner = msg.sender

  self.votium_merkle_stash = IMultiMerkleStash(0x34590960981f98b55d236b70E8B4d9929ad89C9c)


@external
def harvest(votium_claim_params: claimParam[50]):
  # 1. Claim any rewards from Votium MerkleStash
  self.votium_merkle_stash.claimMulti(self.owner, votium_claim_params)
  # 2. Claim fees from Curve FeeDistributor
  # 3. Swap everything for CRV
  # 4. Lock 80% into veCRV
  # 5. Deposit 20% into uCRV


@external
def set_owner(new_addr: address):
    """
    @notice Admin function to update owner
    @param new_addr The new owner address to take over immediately
    """

    assert msg.sender == self.owner  # dev: Only Owner
    self.owner = new_addr