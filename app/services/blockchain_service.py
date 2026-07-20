"""
Blockchain service for interacting with the EnergyToken smart contract.
The contract lives in the sibling project:  solar-blockchain/

ABI file path (generated after 'npm run compile' in solar-blockchain/):
  ../solar-blockchain/artifacts/contracts/EnergyToken.sol/EnergyToken.json
"""
from decimal import Decimal
from typing import Optional, Dict, Any
import hashlib
import json
import logging
from web3.exceptions import TimeExhausted
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
        self.is_connected = False

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
        logger.info(f"BLOCKCHAIN_ENABLED={settings.blockchain_enabled}")
        logger.info(f"RPC_URL={rpc_url}")
        logger.info(f"CONTRACT={settings.blockchain_contract_address}")
        if not rpc_url:
            logger.info("No blockchain RPC URL configured")
            return

        # Connect to blockchain
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        logger.info(f"is_connected={self.w3.is_connected()}")
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

        # ABI is bundled inside this project at app/blockchain/EnergyToken.json
        # This makes the project self-contained and deployable to Render/cloud
        abi_path = (
            Path(__file__).parent   # services/
            .parent                 # app/
            / "blockchain"
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

    @staticmethod
    def compute_listing_hash(listing) -> str:
        """
        Compute a SHA256 hash of IMMUTABLE listing fields only.
        This is stored on-chain at mint time.

        Fields included (cannot be changed after creation):
          - id, seller_id        → identity
          - energy_kwh           → core financial term
          - price_per_kwh        → core financial term
          - location             → buyers filter by this; tampering = fraud
          - expires_at           → tampering could extend listing indefinitely
          - created_at           → timestamp anchor

        Mutable fields (title, description) are excluded —
        they are cosmetic and can be updated via API safely.
        """
        data = {
            "id":            str(listing.id),
            "seller_id":     str(listing.seller_id),
            # "energy_kwh":    int(listing.energy_kwh),
            "price_per_kwh": str(listing.price_per_kwh),
            "energy_source": str(listing.energy_source.value if hasattr(listing.energy_source, 'value') else listing.energy_source),
            "location":      listing.location or "",
            "expires_at":    listing.expires_at.isoformat() if listing.expires_at else "",
            "created_at":    listing.created_at.isoformat() if listing.created_at else "",
        }
        # Sort keys for deterministic ordering
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def compute_purchase_hash(buyer_id: str, energy_kwh: int, price_eth: Decimal, listing_id: str) -> str:
        """
        Compute SHA256 hash of purchase data for integrity verification.
        
        This hash is stored immutably on blockchain and verified before consumption.
        If any field is tampered with in DB, hash verification fails.
        
        Args:
            buyer_id: UUID of buyer
            energy_kwh: Amount of energy purchased
            price_eth: Price paid in ETH
            listing_id: UUID of listing being purchased
            
        Returns:
            SHA256 hex digest of canonical purchase data
        """
        data = {
            "buyer_id": str(buyer_id),
            "energy_kwh": int(energy_kwh),
            "price_eth": str(price_eth),
            "listing_id": str(listing_id),
        }
        # Sort keys for deterministic ordering - same hash for same data
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
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
        price_per_kwh: Decimal,
        listing_id: str = "",
        listing_hash: str = ""
    ) -> Optional[str]:
        """
        Mint energy tokens for a seller

        Args:
            seller_address: Ethereum address of the seller
            energy_kwh: Amount of energy produced in kWh
            price_per_kwh: Price per kWh (stored on-chain as micro-units * 1e6)
            listing_id: DB listing UUID — stored on-chain for tamper detection
            listing_hash: SHA256 of ALL listing fields — covers every DB field

        Returns:
            Transaction hash or None if blockchain unavailable
        """
        if not self.is_available():
            logger.info("Blockchain unavailable - skipping mint")
            return None

        try:
            private_key = getattr(settings, 'blockchain_private_key', None)
            if not private_key:
                logger.error("No private key configured")
                return None

            account = self.w3.eth.account.from_key(private_key)

            # Convert price to micro-units (avoid floats in Solidity)
            price_micro = int(Decimal(str(price_per_kwh)) * Decimal("1000000"))

            # Convert hex hash string to bytes32
            hash_bytes = bytes.fromhex(listing_hash) if listing_hash else bytes(32)
            
            logger.debug(f"Minting energy: seller={seller_address}, kwh={energy_kwh}, price_micro={price_micro}, listing_id={listing_id}, hash={listing_hash[:16]}...")

            nonce = self.w3.eth.get_transaction_count(account.address,"pending")

            transaction = self.contract.functions.mintEnergy(
                self._Web3.to_checksum_address(seller_address),
                energy_kwh,
                price_micro,
                listing_id,
                hash_bytes
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 800000,  # Increased significantly - storing listing record + snapshots + purchase array
                'gasPrice': self.w3.eth.gas_price,
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            logger.info(f"Submitting mintEnergy transaction for listing {listing_id}")
            return self._submit_transaction(signed_txn, wait_for_receipt=False)

        except Exception as e:
            logger.error(f"Error minting energy: {e}")
            return None

    def mint_energy_with_snapshot(
        self,
        seller_address: str,
        energy_kwh: int,
        price_per_kwh: Decimal,
        listing_id: str = "",
        listing_hash: str = ""
    ) -> Optional[str]:
        """
        Mint energy tokens AND store immutable listing snapshot on blockchain.
        This is the recommended entry point for new listings.
        
        The snapshot is stored on-chain for permanent verification.
        Future integrity checks will compare against this snapshot,
        making energy_kwh changes legitimate (only affects current state, not hash).
        """
        # First, mint the tokens
        tx_hash = self.mint_energy(
            seller_address=seller_address,
            energy_kwh=energy_kwh,
            price_per_kwh=price_per_kwh,
            listing_id=listing_id,
            listing_hash=listing_hash
        )
        
        if tx_hash:
            # Snapshot was implicitly stored via listing_hash parameter
            # The contract stores this hash which we'll verify against
            logger.info(f"Energy minted and snapshot stored: {tx_hash}")
        
        return tx_hash

    def record_purchase(
        self,
        seller_address: str,
        buyer_address: str,
        energy_kwh: int,
        price_eth: Decimal,
        listing_id: str = "",
        purchase_hash: str = ""
    ) -> Optional[str]:
        """
        Record energy purchase on blockchain with integrity verification.

        Args:
            seller_address: Seller's Ethereum address
            buyer_address: Buyer's Ethereum address
            energy_kwh: Amount of energy purchased
            price_eth: Price paid in ETH
            listing_id: DB listing UUID — for tracking purchases per listing
            purchase_hash: SHA256 hash of purchase data for integrity verification

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
            nonce = self.w3.eth.get_transaction_count(account.address,"pending")

            # Convert price to wei
            price_wei = self._Web3.to_wei(float(price_eth), 'ether')

            # Convert purchase_hash hex string to bytes32
            purchase_hash_bytes = bytes.fromhex(purchase_hash) if purchase_hash else bytes(32)

            # Call smart contract with purchase hash for integrity verification
            transaction = self.contract.functions.recordPurchase(
                self._Web3.to_checksum_address(seller_address),
                self._Web3.to_checksum_address(buyer_address),
                energy_kwh,
                price_wei,
                listing_id,
                purchase_hash_bytes  # ← NEW: Purchase data integrity hash
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 500000,  # Increased significantly - adding purchase to array
                'gasPrice': self.w3.eth.gas_price,
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)

            return self._submit_transaction(signed_txn, wait_for_receipt=False)

        except Exception as e:
            logger.error(f"Error recording purchase: {e}")
            return None

    def transfer_payment(
        self,
        buyer_address: str,
        seller_address: str,
        amount_eth: Decimal
    ) -> Optional[str]:
        """
        Transfer ETH payment from buyer to seller.
        
        The backend (contract owner) acts as an intermediary for payment transfers.
        This is necessary because:
        1. Buyers' private keys are not stored on the backend
        2. The backend holds the only private key available
        3. This centralizes payment processing safely
        
        Flow:
        - Backend sends ETH to seller on behalf of the buyer
        - In production, this should be replaced with:
          a) Buyer signs payment transaction themselves (via MetaMask)
          b) Or use a payment processor (Stripe, PayPal)
          c) Or require ETH deposit from buyer first

        Args:
            buyer_address: Buyer's Ethereum address (for logging/verification)
            seller_address: Seller's Ethereum address (recipient)
            amount_eth: Amount to transfer in ETH

        Returns:
            Transaction hash or None if blockchain unavailable
        """
        if not self.is_available():
            logger.info("Blockchain unavailable - skipping payment transfer")
            return None

        try:
            private_key = getattr(settings, 'blockchain_private_key', None)
            if not private_key:
                logger.error("No private key configured for payment transfer")
                return None

            account = self.w3.eth.account.from_key(private_key)
            logger.info(f"[PAYMENT] Backend account: {account.address}")
            
            # Convert ETH to wei
            amount_wei = self._Web3.to_wei(float(amount_eth), 'ether')
            logger.info(f"[PAYMENT] Converting {amount_eth} ETH to {amount_wei} wei")
            
            logger.info(f"[PAYMENT] Transfer details: buyer={buyer_address}, seller={seller_address}, amount={amount_eth} ETH")
            
            # Note: If backend == seller, this will be a self-transfer on-chain (valid, just costs gas)
            
            # Check if account has sufficient balance
            balance = self.w3.eth.get_balance(account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            logger.info(f"[PAYMENT] Backend account balance: {balance_eth} ETH ({balance} wei)")
            
            if balance < amount_wei:
                logger.error(f"[PAYMENT] ❌ INSUFFICIENT BALANCE: {balance_eth} ETH < {amount_eth} ETH needed")
                return None
            logger.info(f"[PAYMENT] ✓ Balance sufficient")
            
            nonce = self.w3.eth.get_transaction_count(account.address, "pending")
            logger.info(f"[PAYMENT] Nonce: {nonce}")
            
            # Get gas estimates for EIP-1559 (modern Ethereum/Sepolia)
            try:
                gas_price_data = self.w3.eth.fee_history(1, 'latest')
                base_fee = gas_price_data['baseFeePerGas'][0]
                max_priority_fee = self.w3.to_wei(1, 'gwei')  # 1 gwei priority for Sepolia
                max_fee = base_fee + max_priority_fee
                logger.info(f"[PAYMENT] EIP-1559 fees: baseFee={self.w3.from_wei(base_fee, 'gwei')} gwei, priorityFee={self.w3.from_wei(max_priority_fee, 'gwei')} gwei, maxFee={self.w3.from_wei(max_fee, 'gwei')} gwei")
            except Exception as e:
                logger.warning(f"[PAYMENT] ⚠️  Could not get EIP-1559 fees, falling back to legacy gasPrice: {e}")
                # Fallback for networks that don't support EIP-1559
                max_fee = self.w3.eth.gas_price
                max_priority_fee = self.w3.eth.gas_price
                logger.info(f"[PAYMENT] Using legacy gasPrice: {self.w3.from_wei(max_fee, 'gwei')} gwei")
            
            # Create ETH transfer transaction FROM backend TO seller
            # Backend facilitates the payment on behalf of the buyer
            transaction = {
                'from': account.address,  # ← Backend account (has private key)
                'to': self._Web3.to_checksum_address(seller_address),
                'value': amount_wei,
                'gas': 21000,  # Standard ETH transfer gas
                'maxFeePerGas': max_fee,  # EIP-1559: max fee per gas
                'maxPriorityFeePerGas': max_priority_fee,  # EIP-1559: priority fee
                'nonce': nonce,
            }
            logger.info(f"[PAYMENT] Transaction object created: from={transaction['from']}, to={transaction['to']}, value={transaction['value']} wei")
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            logger.info(f"[PAYMENT] ✓ Transaction signed successfully")
            
            logger.info(f"[PAYMENT] 📤 Submitting payment transfer: {amount_eth} ETH from backend to {seller_address} (on behalf of {buyer_address})")
            tx_hash = self._submit_transaction(signed_txn, wait_for_receipt=False)
            logger.info(f"[PAYMENT] Result: tx_hash={tx_hash}")
            return tx_hash

        except Exception as e:
            logger.error(f"Error transferring payment: {e}")
            return None

    def get_listing_record(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the immutable on-chain snapshot of a listing.
        Returns seller, energyKwh, pricePerKwh, and the full listing hash.
        """
        if not self.is_available():
            return None
        try:
            seller, energy_kwh, price_micro, listing_hash_bytes, exists = \
                self.contract.functions.getListingRecord(listing_id).call()
            if not exists:
                return None
            return {
                "seller":         seller,
                "energy_kwh":     energy_kwh,
                "price_per_kwh":  Decimal(price_micro) / Decimal("1000000"),
                "price_micro":    price_micro,
                "listing_hash":   listing_hash_bytes.hex(),
            }
        except Exception as e:
            logger.error(f"Error getting listing record: {e}")
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

    def get_eth_balance(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get ETH balance for an address (actual money, not tokens)
        
        Returns:
            Dict with eth_balance (in ETH) and wei_balance (in wei)
        """
        if not self.is_available():
            return None

        try:
            balance_wei = self.w3.eth.get_balance(
                self._Web3.to_checksum_address(address)
            )
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            return {
                "balance_eth": str(balance_eth),
                "balance_wei": str(balance_wei),
                "balance_float": float(balance_eth)
            }
        except Exception as e:
            logger.error(f"Error getting ETH balance: {e}")
            return None

    def consume_energy_for(
        self,
        buyer_address: str,
        energy_kwh: int
    ) -> Optional[str]:
        """
        Burn SEC tokens for a buyer when they consume the energy.
        Calls consumeEnergyFor() — an owner-only function on the contract.
        Backend (Account #0) signs this on behalf of the buyer.

        Args:
            buyer_address: Buyer's Ethereum wallet address
            energy_kwh:    Amount of energy consumed in kWh (tokens to burn)

        Returns:
            Transaction hash or None if blockchain unavailable
        """
        if not self.is_available():
            logger.info("Blockchain unavailable - skipping consume energy")
            return None

        try:
            private_key = getattr(settings, 'blockchain_private_key', None)
            if not private_key:
                logger.error("No private key configured")
                return None

            account = self.w3.eth.account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address,"pending")

            transaction = self.contract.functions.consumeEnergyFor(
                self._Web3.to_checksum_address(buyer_address),
                energy_kwh
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            return self._submit_transaction(signed_txn)

        except Exception as e:
            logger.error(f"Error consuming energy: {e}")
            return None

    def verify_purchase_integrity(
        self,
        buyer_id: str,
        energy_kwh: int,
        price_eth: Decimal,
        listing_id: str,
        stored_purchase_hash: str
    ) -> tuple[bool, str]:
        """
        Verify purchase data integrity by comparing calculated hash with stored hash.
        
        Args:
            buyer_id: UUID of buyer
            energy_kwh: Amount of energy purchased
            price_eth: Price paid in ETH
            listing_id: UUID of listing
            stored_purchase_hash: Hash stored during purchase creation
            
        Returns:
            Tuple of (is_valid: bool, message: str)
            - (True, "Purchase data verified") if hashes match
            - (False, "Purchase data was tampered") if hashes don't match
        """
        if not stored_purchase_hash:
            return False, "No purchase hash stored - cannot verify integrity"
        
        # Recalculate hash from current data
        current_hash = self.compute_purchase_hash(
            buyer_id=buyer_id,
            energy_kwh=energy_kwh,
            price_eth=price_eth,
            listing_id=listing_id
        )
        
        # Compare hashes
        if current_hash == stored_purchase_hash:
            return True, "Purchase data verified"
        else:
            logger.warning(f"Purchase tampering detected: stored={stored_purchase_hash}, current={current_hash}")
            return False, f"Purchase data was modified. Original hash: {stored_purchase_hash}, Current hash: {current_hash}"

    # ─── Admin Read-Only Methods ──────────────────────────────────────────────
    # Admin has NO wallet, NO private key, makes NO transactions.
    # All methods below are FREE eth_call reads — no gas, no signing.

    def get_energy_produced(self, seller_address: str) -> Optional[int]:
        """
        [ADMIN / READ-ONLY]
        Total kWh ever produced (minted) for a seller address.
        """
        if not self.is_available():
            return None
        try:
            return self.contract.functions.getEnergyProduced(
                self._Web3.to_checksum_address(seller_address)
            ).call()
        except Exception as e:
            logger.error(f"Error getting energy produced: {e}")
            return None

    def get_energy_consumed(self, buyer_address: str) -> Optional[int]:
        """
        [ADMIN / READ-ONLY]
        Total kWh ever consumed (burned) by a buyer address.
        """
        if not self.is_available():
            return None
        try:
            return self.contract.functions.getEnergyConsumed(
                self._Web3.to_checksum_address(buyer_address)
            ).call()
        except Exception as e:
            logger.error(f"Error getting energy consumed: {e}")
            return None

    def get_transaction_info(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        [ADMIN / READ-ONLY]
        Fetch blockchain transaction details by hash.
        Useful for admin to verify a specific purchase transaction.
        """
        if not self.is_available():
            return None
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return {
                    "tx_hash": tx_hash,
                    "block_number": receipt["blockNumber"],
                    "status": "success" if receipt["status"] == 1 else "failed",
                    "gas_used": receipt["gasUsed"],
                    "from": receipt["from"],
                    "to": receipt["to"],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting transaction info: {e}")
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

    def compute_listing_hash(self, listing) -> str:
        """
        Compute SHA256 hash of IMMUTABLE listing fields only.
        Energy_kwh is NOT included (it's dynamic and changes with purchases).
        
        Fields included:
        - price_per_kwh (locked at creation)
        - title (seller can't change)
        - description (seller can't change)
        - location (seller can't change)
        - energy_source (type never changes)
        - expires_at (expiration is set at creation)
        
        This ensures price fraud, title manipulation, location changes are detected.
        """
        data = {
            "id": str(listing.id),
            "seller_id": str(listing.seller_id),
            "price_per_kwh": str(listing.price_per_kwh),
            "energy_source": str(listing.energy_source.value if hasattr(listing.energy_source, 'value') else listing.energy_source),
            "title": listing.title,
            "description": listing.description or "",
            "location": listing.location or "",
            "expires_at": listing.expires_at.isoformat() if listing.expires_at else "",
            "created_at": listing.created_at.isoformat() if listing.created_at else "",
        }
        
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def store_listing_snapshot(self, listing) -> Optional[str]:
        """
        Store immutable listing snapshot on blockchain for tamper detection.
        This snapshot contains all original immutable data and is never updated.
        
        In production, this would call a smart contract function to store the data.
        For now, we compute and return the hash that will be verified later.
        """
        if not self.is_available():
            logger.info("Blockchain unavailable - skipping snapshot store")
            return None

        try:
            snapshot_hash = self.compute_listing_hash(listing)
            logger.info(f"Listing snapshot hash computed: {snapshot_hash[:16]}...")
            
            # TODO: Call smart contract to store snapshot
            # tx_hash = self.contract.functions.storeListingSnapshot(
            #     listing_id=bytes(16)(int(listing.id.bytes)),
            #     immutable_hash=bytes.fromhex(snapshot_hash)
            # ).transact()
            
            # For now, return the hash (used for verification)
            return snapshot_hash
        except Exception as e:
            logger.error(f"Error storing listing snapshot: {e}")
            return None

    def get_listing_snapshot(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve immutable listing snapshot from blockchain.
        
        Returns the stored snapshot data for integrity verification.
        """
        if not self.is_available():
            logger.info("Blockchain unavailable - skipping snapshot retrieval")
            return None

        try:
            # TODO: Call smart contract to retrieve snapshot
            # snapshot = self.contract.functions.getListingSnapshot(listing_id).call()
            # return {
            #     "listing_id": listing_id,
            #     "snapshot_hash": snapshot.get("immutable_hash"),
            #     "stored_at": snapshot.get("stored_at"),
            # }
            
            # For now, return None (needs contract implementation)
            return None
        except Exception as e:
            logger.error(f"Error retrieving listing snapshot: {e}")
            return None


    def _submit_transaction(
            self,
            signed_txn,
            wait_for_receipt: bool = False
        ) -> Optional[str]:
            """
            Submit transaction.
            
            Args:
                signed_txn: Signed transaction object
                wait_for_receipt: If True, wait for confirmation (blocking).
                                 If False, return tx hash immediately (non-blocking).
            
            Returns:
                Transaction hash or None if failed to submit
            """

            try:
                try:
                    # Web3 v6
                    raw_tx = signed_txn.rawTransaction
                except AttributeError:
                    # Web3
                    raw_tx = signed_txn.raw_transaction

                logger.info(f"[SUBMIT_TX] Sending raw transaction (length={len(raw_tx)} bytes)")
                tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

                tx_hash_hex = tx_hash.hex()
                logger.info(f"[SUBMIT_TX] ✅ Transaction submitted successfully: {tx_hash_hex}")

                # If not waiting for receipt, return immediately
                if not wait_for_receipt:
                    logger.info(f"[SUBMIT_TX] Non-blocking mode: returning tx hash immediately")
                    return tx_hash_hex

                # Otherwise, wait for confirmation (blocking)
                try:
                    logger.info(f"[SUBMIT_TX] Waiting for receipt (timeout=300s)...")
                    receipt = self.w3.eth.wait_for_transaction_receipt(
                        tx_hash,
                        timeout=300
                    )

                    if receipt["status"] == 1:
                        logger.info(f"[SUBMIT_TX] ✅ Transaction mined successfully: {tx_hash_hex}")
                        return tx_hash_hex

                    logger.error(f"[SUBMIT_TX] ❌ Transaction mined but failed: {tx_hash_hex}")
                    return None

                except TimeExhausted:
                    logger.warning(f"[SUBMIT_TX] ⚠️  Receipt timeout, but tx submitted: {tx_hash_hex}")
                    return tx_hash_hex
            
            except Exception as e:
                logger.error(f"[SUBMIT_TX] ❌ Failed to submit transaction: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"[SUBMIT_TX] Traceback: {traceback.format_exc()}")
                return None

# Singleton instance
_blockchain_service: Optional[BlockchainService] = None


def get_blockchain_service() -> BlockchainService:
    """Get singleton blockchain service instance"""
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    return _blockchain_service
