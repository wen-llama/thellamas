from brownie import Llama, accounts


def main():
    acct = accounts.load("llama_deployer")
    premint_addrs = [acct] * 20
    Llama.deploy(premint_addrs, {"from": acct})
