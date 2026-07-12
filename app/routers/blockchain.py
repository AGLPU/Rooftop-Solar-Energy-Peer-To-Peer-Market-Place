from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_read_db
from app.models.user import User, UserRole
from app.models.listing import Listing
from app.models.purchase import Purchase
from app.services.blockchain_service import get_blockchain_service
from app.utils.auth import get_current_active_user, require_admin

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])


# ─── Network Info ─────────────────────────────────────────────────────────────

@router.get(
    "/status",
    summary="Blockchain network status",
    description="Check if blockchain is connected and see contract info (token name, symbol, block number)."
)
def get_blockchain_status():
    blockchain = get_blockchain_service()
    return blockchain.get_network_info()


# ─── Token Balance for a Wallet ──────────────────────────────────────────────

@router.get(
    "/balance/{wallet_address}",
    summary="Get SEC token balance of a wallet",
    description=(
        "Returns how many SEC (Solar Energy Credit) tokens a wallet currently holds.\n\n"
        "- This is a **free read** — no gas, no transaction.\n"
        "- Balance is in **kWh** (1 SEC token = 1 kWh).\n"
        "- Use this to verify that tokens were **minted** to a seller after listing creation."
    )
)
def get_token_balance(wallet_address: str):
    blockchain = get_blockchain_service()
    if not blockchain.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service is not available"
        )
    balance = blockchain.get_energy_balance(wallet_address)
    return {
        "wallet_address": wallet_address,
        "balance_kwh": balance,
        "balance_sec_tokens": balance,
        "note": "1 SEC token = 1 kWh of solar energy"
    }


# ─── Verify Listing on Blockchain ────────────────────────────────────────────

@router.get(
    "/verify/listing/{listing_id}",
    summary="Verify a listing on the blockchain",
    description=(
        "Check if the SEC tokens were actually minted to the seller's wallet "
        "when this listing was created.\n\n"
        "Shows:\n"
        "- The seller's wallet address\n"
        "- The mint transaction hash (stored in DB)\n"
        "- Current token balance of the seller\n"
        "- Total energy ever produced by the seller"
    )
)
def verify_listing_on_blockchain(
    listing_id: UUID,
    db: Session = Depends(get_read_db),
    current_user: User = Depends(get_current_active_user)
):
    # Fetch listing from DB
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )

    # Only seller who owns it, or admin, can verify
    if current_user.role != UserRole.ADMIN and listing.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only verify your own listings"
        )

    # Fetch seller
    seller = listing.seller
    blockchain = get_blockchain_service()

    # Read blockchain data (all free reads — no gas)
    current_balance  = blockchain.get_energy_balance(seller.wallet_address) if seller.wallet_address else None
    total_produced   = blockchain.get_energy_produced(seller.wallet_address) if seller.wallet_address else None
    on_chain_listing = blockchain.get_listing_record(str(listing_id)) if seller.wallet_address else None

    # Verify the mint transaction if it exists
    tx_info = None
    if listing.blockchain_tx_hash:
        tx_info = blockchain.get_transaction_info(listing.blockchain_tx_hash)

    # ── Tamper Detection ──────────────────────────────────────────────────────
    tamper_warnings = []
    integrity_status = "VERIFIED"

    if not listing.blockchain_tx_hash:
        tamper_warnings.append(
            "NO BLOCKCHAIN RECORD: This listing has no mint transaction hash. "
            "Tokens were never minted on-chain — listing may have been inserted directly into DB."
        )
        integrity_status = "TAMPERED"

    elif tx_info is None:
        tamper_warnings.append(
            "TRANSACTION NOT FOUND: The stored tx_hash does not exist on the blockchain. "
            "The hash in DB may have been forged or the Hardhat node was reset."
        )
        integrity_status = "TAMPERED"

    elif tx_info.get("status") != "success":
        tamper_warnings.append(
            f"TRANSACTION FAILED on-chain (status={tx_info.get('status')}). "
            "Tokens were never actually minted."
        )
        integrity_status = "TAMPERED"

    # Cross-check DB vs on-chain listing snapshot
    if on_chain_listing:
        # Recompute hash from current DB values
        recomputed_hash = blockchain.compute_listing_hash(listing)
        on_chain_hash   = on_chain_listing["listing_hash"]

        if recomputed_hash != on_chain_hash:
            # Find exactly which fields changed
            tamper_warnings.append(
                f"HASH MISMATCH: One or more listing fields were modified in the DB after creation. "
                f"On-chain hash: {on_chain_hash[:16]}... | Current DB hash: {recomputed_hash[:16]}... "
                f"Any of these fields may have been changed: energy_kwh, price_per_kwh, title, "
                f"description, location, status, expires_at."
            )
            integrity_status = "TAMPERED"
        else:
            tamper_warnings.append(
                "HASH MATCH: SHA256 of all DB listing fields matches the on-chain hash. "
                "No tampering detected on any field."
            )

    return {
        "listing_id":            str(listing_id),
        "listing_title":         listing.title,
        "listing_energy_kwh":    listing.energy_kwh,
        "listing_price_per_kwh": str(listing.price_per_kwh),
        "listing_status":        listing.status,

        "seller": {
            "user_id":         str(listing.seller_id),
            "username":        seller.username,
            "wallet_address":  seller.wallet_address,
        },

        "blockchain": {
            "mint_tx_hash":               listing.blockchain_tx_hash,
            "mint_tx_status":             tx_info.get("status") if tx_info else "no transaction recorded",
            "mint_tx_block":              tx_info.get("block_number") if tx_info else None,
            "seller_current_balance_kwh": current_balance,
            "seller_total_produced_kwh":  total_produced,
            "tokens_minted_for_listing":  listing.energy_kwh,
            "on_chain_snapshot": {
                "energy_kwh":    on_chain_listing["energy_kwh"]   if on_chain_listing else None,
                "price_per_kwh": str(on_chain_listing["price_per_kwh"]) if on_chain_listing else None,
                "seller_wallet": on_chain_listing["seller"]       if on_chain_listing else None,
                "listing_hash":  on_chain_listing["listing_hash"] if on_chain_listing else None,
            } if on_chain_listing else "not available (listing predates on-chain hash storage)",
        },

        "integrity": {
            "status": integrity_status,
            "checks": tamper_warnings,
        },

        "explanation": (
            f"When this listing was created, the backend (Account #0) called "
            f"mintEnergy({seller.wallet_address}, {listing.energy_kwh}, price={listing.price_per_kwh}) "
            f"on the smart contract. The seller received {listing.energy_kwh} SEC tokens. "
            f"energy_kwh AND price_per_kwh are now both stored immutably on-chain and verified here."
        )
    }


# ─── Verify Purchase on Blockchain ───────────────────────────────────────────

@router.get(
    "/verify/purchase/{purchase_id}",
    summary="Verify a purchase on the blockchain",
    description=(
        "Check if the SEC tokens were actually transferred from seller → buyer "
        "when this purchase was made.\n\n"
        "Shows:\n"
        "- Seller and buyer wallet addresses\n"
        "- Purchase transaction hash\n"
        "- Current token balances of both seller and buyer\n"
        "- Consume transaction hash (if energy was consumed/burned)"
    )
)
def verify_purchase_on_blockchain(
    purchase_id: UUID,
    db: Session = Depends(get_read_db),
    current_user: User = Depends(get_current_active_user)
):
    # Fetch purchase from DB
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )

    # Only buyer, seller of that purchase, or admin can verify
    if current_user.role != UserRole.ADMIN:
        if purchase.buyer_id != current_user.id and purchase.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only verify your own purchases"
            )

    seller  = purchase.seller
    buyer   = purchase.buyer
    blockchain = get_blockchain_service()

    # All free reads — no gas
    seller_balance  = blockchain.get_energy_balance(seller.wallet_address) if seller.wallet_address else None
    buyer_balance   = blockchain.get_energy_balance(buyer.wallet_address)  if buyer.wallet_address  else None

    # Verify purchase transaction
    purchase_tx_info = None
    if purchase.blockchain_tx_hash:
        purchase_tx_info = blockchain.get_transaction_info(purchase.blockchain_tx_hash)

    # Verify consume/burn transaction (if energy was consumed)
    consume_tx_info = None
    if purchase.consume_tx_hash:
        consume_tx_info = blockchain.get_transaction_info(purchase.consume_tx_hash)

    return {
        "purchase_id":      str(purchase_id),
        "energy_kwh":       purchase.energy_kwh,
        "total_price_eth":  str(purchase.total_price),
        "status":           purchase.status,

        "seller": {
            "user_id":          str(purchase.seller_id),
            "username":         seller.username,
            "wallet_address":   seller.wallet_address,
            "current_balance_kwh": seller_balance,
        },

        "buyer": {
            "user_id":          str(purchase.buyer_id),
            "username":         buyer.username,
            "wallet_address":   buyer.wallet_address,
            "current_balance_kwh": buyer_balance,
        },

        "blockchain": {
            "purchase_tx_hash":     purchase.blockchain_tx_hash,
            "purchase_tx_status":   purchase_tx_info.get("status") if purchase_tx_info else "no transaction recorded",
            "purchase_tx_block":    purchase_tx_info.get("block_number") if purchase_tx_info else None,

            "consume_tx_hash":      purchase.consume_tx_hash,
            "consume_tx_status":    consume_tx_info.get("status") if consume_tx_info else "not consumed yet",
            "consume_tx_block":     consume_tx_info.get("block_number") if consume_tx_info else None,
        },

        "explanation": (
            f"When this purchase was made, the backend (Account #0) called "
            f"recordPurchase({seller.wallet_address}, {buyer.wallet_address}, {purchase.energy_kwh}) "
            f"on the smart contract. {purchase.energy_kwh} SEC tokens moved from seller → buyer."
        )
    }


# ─── Admin: Full Wallet Summary ───────────────────────────────────────────────

@router.get(
    "/admin/wallet/{wallet_address}",
    summary="[Admin] Full blockchain summary for a wallet",
    description=(
        "Admin-only endpoint.\n\n"
        "Returns complete blockchain history for any wallet:\n"
        "- Current SEC token balance\n"
        "- Total energy ever produced (as seller)\n"
        "- Total energy ever consumed (as buyer)"
    )
)
def admin_wallet_summary(
    wallet_address: str,
    _: User = Depends(require_admin)
):
    blockchain = get_blockchain_service()
    if not blockchain.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service is not available"
        )

    return {
        "wallet_address":           wallet_address,
        "current_balance_kwh":      blockchain.get_energy_balance(wallet_address),
        "total_produced_kwh":       blockchain.get_energy_produced(wallet_address),
        "total_consumed_kwh":       blockchain.get_energy_consumed(wallet_address),
        "note": (
            "current_balance = total_produced - tokens_sold - tokens_consumed. "
            "All reads are free (eth_call — no gas)."
        )
    }

