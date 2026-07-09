"""
Blockchain service for interacting with the EnergyToken smart contract.
The contract lives in the sibling project:  solar-blockchain/

ABI file path (generated after 'npm run compile' in solar-blockchain/):
  ../solar-blockchain/artifacts/contracts/EnergyToken.sol/EnergyToken.json
"""
from decimal import Decimal
from typing import Optional, Dict, Any
import json
import logging
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BlockchainService:
    """Service for blockchain interactions"""

    def __init__(self):
        self.w3 = None
        self._Web3 = None
        self.contract = None
        self.contract_address: Optional[str] = None
        self.is_connected = FalseC

        try:
            self._initialize_connection()
        except Exception as e:
            logger.warning(f"Blockchain initialization failed: {e}")
            logger.info("Running in DATABASE-ONLY mode (no blockchain)")

    def _initialize_connection(self):
        """Initialize Web3 connection and load contract"""

        # Skip if blockchain is disabled
        if not hasattr(settings, 'blockchain_enabled') or not settings.blockchain_enabled:
            logger.info("Blockchain disabled in settings")
            return

        # Lazy import — web3 is optional; server starts fine without it
        try:
            from web3 import Web3
            self._Web3 = Web3
        except ImportError:
            logger.warning("web3 package not installed. Run: pip install web3")
            logger.info("Running in DATABASE-ONLY mode")
            return

        # Get RPC URL from settings
        rpc_url = getattr(settings, 'blockchain_rpc_url', None)
        if not rpc_url:
            logger.info("No blockchain RPC URL configured")
            return

        # Connect to blockchain
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to blockchain network")

        logger.info(f"✅ Connected to blockchain: {rpc_url}")
        logger.info(f"   Chain ID: {self.w3.eth.chain_id}")
        logger.info(f"   Latest block: {self.w3.eth.block_number}")

        # Load contract
        self.contract_address = getattr(settings, 'blockchain_contract_address', None)
        if not self.contract_address:
            logger.warning("No contract address configured")
            return

        # ABI lives in the sibling solar-blockchain project
        # rooftop-solar-marketplace/  ← this project
        # solar-blockchain/           ← sibling blockchain project
        abi_path = (
            Path(__file__).parent  # services/
            .parent                # app/
            .parent                # rooftop-solar-marketplace/
            .parent                # hackathon/
            / "solar-blockchain"
            / "artifacts"
            / "contracts"
            / "EnergyToken.sol"
            / "EnergyToken.json"
        )

        if not abi_path.exists():
            logger.warning(f"Contract ABI not found at: {abi_path}")
            logger.info("Run 'npm run compile' inside the solar-blockchain/ project first")
            return

        with open(abi_path, 'r') as f:
            contract_json = json.load(f)
            contract_abi = contract_json['abi']

        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=self._Web3.to_checksum_address(self.contract_address),
            abi=contract_abi
        )

        logger.info(f"✅ Contract loaded: {self.contract_address}")

        # Verify contract
        token_name = self.contract.functions.name().call()
        token_symbol = self.contract.functions.symbol().call()
        logger.info(f"   Token: {token_name} ({token_symbol})")

        self.is_connected = True

    def is_available(self) -> bool:
        """Check if blockchain service is available"""
        return self.is_connected and self.contract is not None

    def get_account(self) -> Optional[str]:
        """Get platform account address"""
        if not self.is_available():
            return None

        private_key = getattr(settings, 'blockchain_private_key', None)
        if not private_key:
            return None

        account = self.w3.eth.account.from_key(private_key)
        return account.address

    def mint_energy(
        self,
        seller_address: str,
        energy_kwh: int,
        metadata: str = ""
    ) -> Optional[str]:
        """
        Mint energy tokens for a seller

        Args:
            seller_address: Ethereum address of the seller
            energy_kwh: Amount of energy produced in kWh
            metadata: Additional information (listing ID, date, etc.)

        Returns:
            Transaction hash or None if blockchain unavailable
        """
        if not self.is_available():
            logger.info("Blockchain unavailable - skipping mint")
            return None

        try:
            # Get platform account
            private_key = getattr(settings, 'blockchain_private_key', None)
            if not private_key:
                logger.error("No private key configured")
                return None

            account = self.w3.eth.account.from_key(private_key)

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(account.address)

            transaction = self.contract.functions.mintEnergy(
                self._Web3.to_checksum_address(seller_address),
                energy_kwh,
                metadata
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
            })

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt['status'] == 1:
                logger.info(f"✅ Energy minted: {energy_kwh} kWh to {seller_address}")
                return tx_hash.hex()
            else:
                logger.error(f"❌ Transaction failed: {tx_hash.hex()}")
                return None

        except Exception as e:
            logger.error(f"Error minting energy: {e}")
            return None

    def record_purchase(
        self,
        seller_address: str,
        buyer_address: str,
        energy_kwh: int,
        price_eth: Decimal
    ) -> Optional[str]:
        """
        Record energy purchase on blockchain

        Args:
            seller_address: Seller's Ethereum address
            buyer_address: Buyer's Ethereum address
            energy_kwh: Amount of energy purchased
            price_eth: Price paid in ETH

        Returns:
            Transaction hash or None
        """
        if not self.is_available():
            logger.info("Blockchain unavailable - skipping purchase record")
            return None

        try:
            private_key = getattr(settings, 'blockchain_private_key', None)
            if not private_key:
                return None

            account = self.w3.eth.account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)

            # Convert price to wei
            price_wei = self._Web3.to_wei(float(price_eth), 'ether')

            transaction = self.contract.functions.recordPurchase(
                self._Web3.to_checksum_address(seller_address),
                self._Web3.to_checksum_address(buyer_address),
                energy_kwh,
                price_wei
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 250000,
                'gasPrice': self.w3.eth.gas_price,
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt['status'] == 1:
                logger.info(f"✅ Purchase recorded: {energy_kwh} kWh from {seller_address} to {buyer_address}")
                return tx_hash.hex()
            else:
                logger.error(f"❌ Purchase transaction failed")
                return None

        except Exception as e:
            logger.error(f"Error recording purchase: {e}")
            return None

    def get_energy_balance(self, address: str) -> Optional[int]:
        """Get energy token balance for an address (in kWh)"""
        if not self.is_available():
            return None

        try:
            balance = self.contract.functions.getEnergyBalance(
                self._Web3.to_checksum_address(address)
            ).call()
            return balance
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None

    def get_network_info(self) -> Dict[str, Any]:
        """Get blockchain network information"""
        if not self.is_available():
            return {
                "connected": False,
                "message": "Blockchain service unavailable"
            }

        try:
            return {
                "connected": True,
                "chain_id": self.w3.eth.chain_id,
                "block_number": self.w3.eth.block_number,
                "contract_address": self.contract_address,
                "token_name": self.contract.functions.name().call(),
                "token_symbol": self.contract.functions.symbol().call(),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }


# Singleton instance
_blockchain_service: Optional[BlockchainService] = None


def get_blockchain_service() -> BlockchainService:
    """Get singleton blockchain service instance"""
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    return _blockchain_service

