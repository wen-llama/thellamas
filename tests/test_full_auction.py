import ape


def test_full_auction(
    deployer, preminter, alice, bob, token, auction_house, split_recipient
):
    print("------------------ START")
    print("token count", token.token_count())

    # check that the last 20 nfts have been correctly airdropped
    print("------------------ checking premints")
    for i in range(401,421):
      assert token.ownerOf(i) == preminter
    print("premints checked")

    print("------------------ setting auction house as minter")
    token.set_minter(auction_house, sender=deployer)
    print("set")

    #  start allowlist minting
    print("------------------ starting al")
    token.start_al_mint(sender=deployer)
    token.allowlistMint(
        [
            bytes.fromhex("8a7ac7b0677d62d733b642bc2a06c609d04354cbba5d6ac08d359cef96a966e1"),
            bytes.fromhex("464788a278e5bf8ee6275f84b4ef51ff9461809129ee60aad3ce1864ef5f1a70"),
            bytes.fromhex("3ca892a7fc01fdf94e036ea38339a6811167ab843d780c8dc9bf7860379da568")
        ],
        sender=bob,
        value="0.1 ether"
    )
    token.stop_al_mint(sender=deployer)
    assert token.ownerOf(1) == bob
    print("al finished, token count", token.token_count())

    # start whitelist minting
    print("------------------ starting wl")
    token.start_wl_mint(sender=deployer)
    token.whitelistMint(
        [
            bytes.fromhex("01d406d4747bd12193a48c0e49c2d4f64e82b88d62e90f5ffbcec6c3cd853951"),
            bytes.fromhex("dde94d9c8f562df87d019849933c6f4c5588f278e731af5dda4a3fe0208f74d6"),
            bytes.fromhex("40cf18ab9bd51f9d58054254246f31fd04090cac179cd40780c17de8706572be"),
            bytes.fromhex("02c541d566951c2470a31dcfd33617d8048956b9241fe2202ac2df867bd69f33"),
            bytes.fromhex("038657d4f4bcc47bbd18ba0d36183cc5b533b5d459a9043eacc9edd542f2dff0"),
            bytes.fromhex("329572f27f6cb8520d730695735833ece47bf0d0d6e759b778ef8c05b34f70de"),
            bytes.fromhex("c58cb8c5f0fa318ebc4e0e145102da447d654314514927170c3a85d7e16ed58b"),
            bytes.fromhex("5ebdddf044b8fa76cada5612e61d1eef0003c4060040d5423b504f6d511d141b")
        ],
        sender=alice,
        value="0.3 ether"
    )
    token.stop_wl_mint(sender=deployer)
    assert token.ownerOf(2) == alice
    print("wl finished, token count", token.token_count())

    # start the auction and simulate the auction/bid minting
    print("------------------ starting regular auction")
    auction_house.unpause(sender=deployer)
    max_iter = 420-20-20-2 # 420 - 20 honoraries - 20 discorders - 1 al - 1wl = 378
    for i in range(max_iter):
        token_id = auction_house.auction()["token_id"]

        print("bidding for", token_id)
        auction_house.create_bid(token_id, 100, sender=alice, value="100 wei")

        ape.networks.provider.set_timestamp(ape.networks.provider.get_block("latest").timestamp + (1000))
        ape.networks.provider.mine(1)

        deployer_balance_before = deployer.balance
        split_recipient_before = split_recipient.balance

        print("settling auction")
        if i == max_iter - 1:
            auction_house.pause(sender=deployer)
            auction_house.settle_auction(sender=deployer)
        else:
            auction_house.settle_current_and_create_new_auction(sender=deployer)

        deployer_balance_after = deployer.balance
        split_recipient_after = split_recipient.balance

        assert deployer_balance_after == deployer_balance_before + 5
        assert split_recipient_after == split_recipient_before + 95

        print("token count", token.token_count())
    print("regular auction finished")

    # airdrop to discorders
    print("------------------ airdropping discorders")    
    token.airdrop_discorders([alice, bob] * 10, sender=deployer)
    print("airdrop done, token count", token.token_count())

    print("just double checking the airdrop went well")
    assert token.ownerOf(381) == alice
    assert token.ownerOf(384) == bob
