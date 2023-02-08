from brownie import LlamaAuctionHouse, accounts, web3

def main():
  acct = accounts.load('llama_deployer')
  llamas_addr = "0x56b30523cD85F8a89A31111492a9C39E9E0CC2c3"
  time_buffer = 300
  reserve_price = web3.toWei(0.1, "ether")
  min_bid_increment_percentage = 2
  duration = 25200 # 7 hours in seconds
  LlamaAuctionHouse.deploy(llamas_addr, time_buffer, reserve_price, min_bid_increment_percentage, duration, {'from': acct})