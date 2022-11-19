import pytest
from brownie import *  # InterfaceChecker, accounts, exceptions


def test_supports_interface_direct(token):
    assert token.supportsInterface(
        0x0000000000000000000000000000000000000000000000000000000001FFC9A7
    )


def test_supports_interface_direct_misc(token):
    interfaces = {
        "ERC165": "0x01FFC9A7",
        "ERC721": "0x80AC58CD",
        "ERC721TokenReceiver": "0x150B7A02",
        "ERC721Enumerable": "0x780E9D63",
        "ERC721Metadata": "0x5B5E139F",
    }
    for i, j in interfaces.items():
        assert token.supportsInterface(j)
