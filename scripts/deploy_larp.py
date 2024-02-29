from ape import accounts, networks, project


def main():
    deployer = accounts.load("llama_deployer")

    al_merkle_root = bytes.fromhex("a253b2b545f5b63c0eabbc04e1ecb1b2bf3fada64fcbd164cbfc44a8fb15eba7") # AL root
    wl_merkle_root = bytes.fromhex("ffc494c343ff71f2ddd73bfb8561c045e673657940baf5031185c83cd70754f9") # WL root

    premint_addrs = [
        "0xAdE9e51C9E23d64E538A7A38656B78aB6Bcc349e",
        "0x56B9c77823c65a6A83E85e1e04d974642589B67a",
        "0xD28a4c5B3685e5948d8A57f124669eafB69F05Bb",
        "0x009d13e9bec94bf16791098ce4e5c168d27a9f07",
        "0x090E1Fdc0CB866317751F0621884a203a8d797aa",
        "0x765078e631EfC704EB5674866a7dCc06828E5C29",
        "0x402293a05fD5e6eD2A6cF828C77272F6b71b9Eb8",
        "0x79603115Df2Ba00659ADC63192325CF104ca529C",
        "0x73Eb240a06f0e0747C698A219462059be6AacCc8",
        "0xa25547A556439213176f9FECec50acc863305f59",
        "0x124f00837680245934b97D600F5e7144656482c1",
        "0x73Eb240a06f0e0747C698A219462059be6AacCc8",
        "0xbA22746D79E75931DD8C0336760332E5D4a372a5",
        "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683",
        "0xDCf789b4101E62bD423E5D3D982B2f210D16B840",
        "0xE10De56A61BC036fD58a497Af534D00C5B6D64a8",
        "0x73Eb240a06f0e0747C698A219462059be6AacCc8",
        "0xbf6a314764424ef942ed68962705981f1bb16c07",
        "0xA12aC5088dE5c394505D3dEd4c2B5f2A81858753",
        "0x9c9dC2110240391d4BEe41203bDFbD19c279B429"
    ]

    print("------------------------------")
    print("base fee", networks.provider.base_fee)
    print("priority fee", networks.provider.priority_fee)
    print("max gas", networks.provider.max_gas)
    print("deployer balance", deployer.balance)
    print("------------------------------")

    deployer.deploy(
        project.Larp,
        wl_merkle_root,
        al_merkle_root,
        premint_addrs
        # publish=True
    )
