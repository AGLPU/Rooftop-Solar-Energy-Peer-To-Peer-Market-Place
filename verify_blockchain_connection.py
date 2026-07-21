#!/usr/bin/env python3
"""Verify blockchain connection and RPC endpoint"""

import sys
import io
from web3 import Web3
from app.config import get_settings

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

settings = get_settings()

print("=" * 70)
print("BLOCKCHAIN CONNECTION VERIFICATION")
print("=" * 70)

# Check if blockchain is enabled
if not settings.blockchain_enabled:
    print("[FAIL] BLOCKCHAIN_ENABLED=False")
    sys.exit(1)

print(f"[OK] BLOCKCHAIN_ENABLED={settings.blockchain_enabled}")

# Check RPC URL
rpc_url = settings.blockchain_rpc_url
print(f"[INFO] RPC URL: {rpc_url}")

if not rpc_url:
    print("[FAIL] NO RPC URL CONFIGURED")
    sys.exit(1)

# Connect to Web3
try:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    print(f"[INFO] Web3 created")
except Exception as e:
    print(f"[FAIL] Failed to create Web3 instance: {e}")
    sys.exit(1)

# Check if connected
is_connected = w3.is_connected()
status = "OK" if is_connected else "FAIL"
print(f"[{status}] Connected: {is_connected}")

if not is_connected:
    print("[FAIL] RPC endpoint is not responding. Check your URL.")
    sys.exit(1)

# Get network info
try:
    chain_id = w3.eth.chain_id
    print(f"[INFO] Chain ID: {chain_id}")
    
    if chain_id == 11155111:
        print("[OK] This is Sepolia testnet")
    else:
        print(f"[WARN] This is NOT Sepolia (expected 11155111, got {chain_id})")
        
    block_number = w3.eth.block_number
    print(f"[INFO] Latest block: {block_number}")
    
    gas_price = w3.eth.gas_price
    print(f"[INFO] Current gas price: {w3.from_wei(gas_price, 'gwei')} gwei")
except Exception as e:
    print(f"[FAIL] Failed to get network info: {e}")
    sys.exit(1)

# Check backend account
private_key = settings.blockchain_private_key
if not private_key:
    print("[FAIL] NO BLOCKCHAIN_PRIVATE_KEY CONFIGURED")
    sys.exit(1)

try:
    account = w3.eth.account.from_key(private_key)
    print(f"\nBACKEND ACCOUNT")
    print(f"[INFO] Address: {account.address}")
    
    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, 'ether')
    print(f"[INFO] Balance: {balance_eth} ETH ({balance} wei)")
    
    if float(balance_eth) < 0.01:
        print("[WARN] Very low balance! Need at least 0.01 ETH for gas")
except Exception as e:
    print(f"[FAIL] Failed to check account: {e}")
    sys.exit(1)

# Check contract
contract_address = settings.blockchain_contract_address
print(f"\nSMART CONTRACT")
print(f"[INFO] Address: {contract_address}")

try:
    # Try to get code at contract address
    contract_code = w3.eth.get_code(contract_address)
    if contract_code == b'':
        print("[FAIL] No contract code at this address!")
    else:
        print(f"[OK] Contract exists ({len(contract_code)} bytes)")
except Exception as e:
    print(f"[FAIL] Failed to check contract: {e}")

print("\n" + "=" * 70)
print("BLOCKCHAIN CONNECTION VERIFICATION COMPLETE")
print("=" * 70)

