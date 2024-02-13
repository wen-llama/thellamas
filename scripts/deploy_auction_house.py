from ape import accounts, networks, project
from eth_utils import keccak, to_wei


def main():
    deployer = accounts.load("llama_deployer")
    llamas_addr = "0xde8991d758f36cad8c546b0983deae7bdc99a8ab"
    time_buffer = 300
    reserve_price = to_wei(0.2, "ether")
    min_bid_increment_percentage = 2
    duration = 5400

    deployer.deploy(
        project.LlamaAuctionHouse,
        llamas_addr, # token
        time_buffer, # time buffer
        reserve_price, # reserve price
        min_bid_increment_percentage, # min bid increment %
        duration, # duration
        "0x52EF1F3c4A1068d0079093cD2DCAe9eBE9Edcb8F", # proceeds receiver - TODO: CHANGE THIS
        95 # split percentage - TODO: change this
    )
