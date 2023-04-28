from brownie import LlamaAuctionHouse, accounts, web3


def main():
    acct = accounts.load("llama_deployer")
    llamas_addr = "0xe127cE638293FA123Be79C25782a5652581Db234"
    time_buffer = 300
    reserve_price = web3.toWei(0.2, "ether")
    min_bid_increment_percentage = 2
    duration = 5400
    LlamaAuctionHouse.deploy(
        llamas_addr,
        time_buffer,
        reserve_price,
        min_bid_increment_percentage,
        duration,
        {"from": acct},
    )
