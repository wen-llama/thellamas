import brownie
import pytest
from brownie import accounts


@pytest.fixture(scope="function")
def recovery_contract(Recovery, deployer):
    return Recovery.deploy({"from": deployer})


def test_recovery(
    recovery_contract,
    deployer,
):
    assert recovery_contract.admin() == deployer

    accounts[0].transfer(recovery_contract.address, "1 ether")

    balanceBefore = deployer.balance()
    print(balanceBefore)
    recovery_contract.recover({"from": deployer})
    balanceAfter = deployer.balance()
    print(balanceAfter)

    assert balanceAfter > balanceBefore


def test_recovery_only_admin(recovery_contract, alice, deployer):
    with brownie.reverts("Caller is not the admin"):
        recovery_contract.recover({"from": alice})
