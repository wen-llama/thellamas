from ape import accounts, networks, project
from eth_utils import keccak


def main():
    deployer = accounts.load("llama_deployer")
    llamas_addr = "0xe127cE638293FA123Be79C25782a5652581Db234"
    time_buffer = 300
    reserve_price = toWei(0.2, "ether")
    min_bid_increment_percentage = 2
    duration = 5400

    deployer.deploy(
        project.LlamaAuctionHouse,
        llamas_addr,
        time_buffer,
        reserve_price,
        min_bid_increment_percentage,
        duration
    )
