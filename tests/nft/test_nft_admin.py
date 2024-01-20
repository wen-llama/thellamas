import ape
import pytest


def test_set_base_uri(token, deployer):
    new_base_uri = "test"
    token.set_base_uri(new_base_uri, sender=deployer)
    assert token.base_uri() == new_base_uri


def test_set_contract_uri(token, deployer):
    new_contract_uri = "test"
    token.set_contract_uri(new_contract_uri, sender=deployer)
    assert token.contractURI() == new_contract_uri


def test_can_set_owner(token, deployer, alice):
    token.set_owner(alice, sender=deployer)
    assert token.owner() == alice


def test_new_owner_can_set_old_owner(token, deployer, alice):
    token.set_owner(alice, sender=deployer)
    token.set_owner(deployer, sender=alice)
    assert token.owner() == deployer


def test_rando_cannot_set_owner(token, alice):
    with ape.reverts("Caller is not the owner"):
        token.set_owner(alice, sender=alice)


def test_rando_cannot_set_base_uri(token, alice):
    with ape.reverts("Caller is not the owner"):
        token.set_base_uri("malware", sender=alice)
    assert token.base_uri() != "malware"


def test_rando_cannot_set_contract_uri(token, alice):
    with ape.reverts("Caller is not the owner"):
        token.set_contract_uri("malware", sender=alice)
    assert token.base_uri() != "malware"


def test_rando_cannot_set_revealed(token, alice):
    assert alice != token.owner()
    with ape.reverts("Caller is not the owner"):
        token.set_revealed(True, sender=alice)


@pytest.mark.skip()
def test_admin_can_withdraw_erc20(token, alice, erc20, deployer):
    erc20.mint(token, 10**18, sender=deployer)
    assert erc20.balanceOf(alice) == 0
    assert erc20.balanceOf(token) == 10**18

    token.admin_withdraw_erc20(erc20, alice, erc20.balanceOf(token), sender=deployer)
    assert erc20.balanceOf(alice) == 10**18
    assert erc20.balanceOf(token) == 0


@pytest.mark.skip()
def test_rando_cannot_withdraw_erc20(alice, token, erc20, deployer):
    erc20.mint(token, 10**18, sender=deployer)
    assert erc20.balanceOf(alice) == 0
    assert erc20.balanceOf(token) == 10**18
    assert erc20.owner() != alice
    assert erc20.minter() != alice
    with ape.reverts("Caller is not the owner"):
        token.admin_withdraw_erc20(erc20, alice, erc20.balanceOf(token), sender=alice)
