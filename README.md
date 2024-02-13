# Llama Auction House

## install and configure things

0. make sure you use python 3.11.x at most (ape is not compatible with 3.12.x yet). `.python-version` is already configured for pyenv.

1. [create a virtual env](https://docs.python.org/3/library/venv.html) using `python -m venv .`

2. activate the environment `source bin/activate`

3. install requirements `pip install -r requirements.txt`

4. install [foundry](https://book.getfoundry.sh/getting-started/installation)

5. `ape plugins install .` to install the ape plugins

## buidl

### build and test

always activate the environment when starting to work source bin/activate

`ape compile -s`

gotta `export WEB3_ARBITRUM_MAINNET_ALCHEMY_PROJECT_ID=<ALCHEMY_API_KEY>` cause ape doesn't support `.env`

run  all tests with `ape test tests/ --network arbitrum:mainnet-fork:foundry -s`

run select testfile with `ape test tests/<testfile>.py --network arbitrum:mainnet-fork:foundry -s`

for running a specific test AND debugging the output, add `-k <test_case>` and `-v DEBUG`

### run scripts aka deploy

you need to configure ape with the accounts it'll use to make transactions

for test/main-nets either `ape accounts import deployer` with your own account OR `ape accounts generate deployer` - you need to make sure your account is funded

#### local / fork

0. you can import one of the private keys from anvil, that's guaranteed to have enough eth

1. spin up the node using anvil: `anvil --fork-url <https://arb-mainnet.g.alchemy.com/v2/$WEB3_ARBITRUM_MAINNET_ALCHEMY_API_KEY> --balance 1000000000`

2. and then run a script
`ape run <scriptname> --network ::foundry`

#### testnets / mainnets

0. import an account with enough eth

1. make sure the RPC is set on `ape-config.yaml`

2. and then run
`ape run deploy_larp --network arbitrum:sepolia:geth`
`ape run deploy_auction_house --network arbitrum:sepolia:geth`

available networks:
 `--network ethereum:sepolia:alchemy`
`--network arbitrum:mainnet:alchemy`
