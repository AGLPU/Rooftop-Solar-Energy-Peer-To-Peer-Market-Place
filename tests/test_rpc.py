from web3 import Web3

RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/qyeZzsuH51Phe5bytgDnj"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

print("Connected:", w3.is_connected())

if w3.is_connected():
    print("Chain ID:", w3.eth.chain_id)
    print("Latest Block:", w3.eth.block_number)