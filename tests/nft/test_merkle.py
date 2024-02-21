import hexbytes
from ape import Contract, accounts, project
from eth_utils import keccak, to_wei


def test_merkle_whitelist(deployer, project, preminter):
    larp_nft = deployer.deploy(
        project.Larp,
        bytes.fromhex("9e64e1669c93e236e43dc7d96e5387adbdf564359dd6aca2cda9982f0caef977"),
        bytes.fromhex("9e64e1669c93e236e43dc7d96e5387adbdf564359dd6aca2cda9982f0caef977"),
        [preminter] * 20
        # [5, 32, 56, 69, 87, 102, 123, 175, 189, 221, 232, 251, 277, 299, 301, 312, 331, 343, 374, 388]
    )
    
    larp_nft.start_wl_mint(sender=deployer)
    deployer.transfer("0x3A348d15f925236Ebb93F0aF6b25b84d540399DD", int(1e18))

    with accounts.use_sender("0x3A348d15f925236Ebb93F0aF6b25b84d540399DD"):
        larp_nft.whitelistMint(
            [
                bytes.fromhex("dac042183188463dae99d98d522e3c3964caf4e5c6d27c3f1b1679b037e1912a"),
                bytes.fromhex("e6856a359924ebadaaa49a231e1da45a0a3ec2ee276bb7ed2a146d32f53872be"),
                bytes.fromhex("dd289cb946e204f4751f33c5ffb9c912e46588e581e192f18a0d6801715b17dd"),
            ],
            value="0.3 ether"
        )
