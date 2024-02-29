import pytest


def test_contract_uri_exists(token):
    assert len(token.contractURI()) > 10


@pytest.mark.skip()
def test_contract_prereveal_is_initially_false(token):
    assert not token.revealed()


def test_prereveal_token_uri_is_default(minted, alice, bob):
    default_uri = minted.default_uri()
    minted.tokenURI(1) == default_uri


def test_postreveal_token_uri_is_base_plus_id(minted, deployer):
    minted.set_revealed(True, sender=deployer)
    assert minted.tokenURI(1) == f"{minted.base_uri()}{1}"
