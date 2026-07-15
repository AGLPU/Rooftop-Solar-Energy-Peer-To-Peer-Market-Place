"""
Public API endpoints — no authentication required.

These endpoints serve as the knowledge base data feed for the AI Agent.
The AI Agent calls these endpoints to gather historical market data,
supply/demand signals, pricing trends and location analytics to power:

  - RAG Q&A:  "Which source has highest supply in Noida?"
  - Forecasts: "Predict Solar demand next month"
  - Suggestions: "Should I list Solar or Wind credits this week?"

All responses are intentionally rich with aggregated fields so the
AI Agent can answer the 14 market intelligence questions without
needing additional joins or processing.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from datetime import datetime

from app.database import get_read_db
from app.models.listing import Listing, ListingStatus, EnergySource
from app.models.purchase import Purchase, PurchaseStatus

router = APIRouter(prefix="/public", tags=["Public — AI Knowledge Base"])


# ─── 1. All Listings ─────────────────────────────────────────────────────────

@router.get(
    "/listings",
    summary="[Public] All listings — AI knowledge base feed",
    description=(
        "No authentication required.\n\n"
        "Returns all listings with rich filters for the AI Agent to answer:\n"
        "- Which source has highest available supply?\n"
        "- What % of marketplace supply is Solar vs Wind vs Hydro?\n"
        "- Which location has greatest wind-credit supply?\n\n"
        "**Used by:** AI Agent RAG pipeline, Prediction Engine, Market Analytics"
    )
)
def get_all_listings_public(
    energy_source: Optional[EnergySource] = Query(None, description="Filter by energy source: SOLAR, WIND, HYDRO, BIOMASS, GEOTHERMAL, TIDAL, OTHER"),
    location: Optional[str] = Query(None, description="Filter by location (city/region, case-insensitive partial match)"),
    status: Optional[ListingStatus] = Query(None, description="Filter by listing status: ACTIVE, SOLD, EXPIRED, CANCELLED"),
    created_from: Optional[datetime] = Query(None, description="Filter listings created after this datetime (ISO 8601)"),
    created_to: Optional[datetime] = Query(None, description="Filter listings created before this datetime (ISO 8601)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return (max 200)"),
    db: Session = Depends(get_read_db)
):
    query = db.query(Listing)

    if energy_source:
        query = query.filter(Listing.energy_source == energy_source)
    if location:
        query = query.filter(Listing.location.ilike(f"%{location}%"))
    if status:
        query = query.filter(Listing.status == status)
    if created_from:
        query = query.filter(Listing.created_at >= created_from)
    if created_to:
        query = query.filter(Listing.created_at <= created_to)

    total = query.count()
    listings = query.order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()

    # Build supply summary per source for AI context
    supply_summary = db.query(
        Listing.energy_source,
        Listing.status,
        func.count(Listing.id).label("count"),
        func.sum(Listing.energy_kwh).label("total_kwh"),
        func.avg(Listing.price_per_kwh).label("avg_price"),
        func.min(Listing.price_per_kwh).label("min_price"),
        func.max(Listing.price_per_kwh).label("max_price"),
    ).group_by(Listing.energy_source, Listing.status).all()

    supply_by_source = {}
    for row in supply_summary:
        src = str(row.energy_source)
        if src not in supply_by_source:
            supply_by_source[src] = {}
        supply_by_source[src][str(row.status)] = {
            "count": row.count,
            "total_kwh": float(row.total_kwh or 0),
            "avg_price_per_kwh": round(float(row.avg_price or 0), 6),
            "min_price_per_kwh": round(float(row.min_price or 0), 6),
            "max_price_per_kwh": round(float(row.max_price or 0), 6),
        }

    return {
        "meta": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters_applied": {
                "energy_source": energy_source,
                "location": location,
                "status": status,
                "created_from": created_from,
                "created_to": created_to,
            },
            "ai_context": "supply_by_source aggregates all statuses — use for market share and supply analysis"
        },
        "supply_by_source": supply_by_source,
        "listings": [
            {
                "id": str(l.id),
                "seller_id": str(l.seller_id),
                "energy_source": l.energy_source,
                "energy_kwh": l.energy_kwh,
                "price_per_kwh": float(l.price_per_kwh),
                "location": l.location,
                "status": l.status,
                "blockchain_verified": l.blockchain_tx_hash is not None,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "expires_at": l.expires_at.isoformat() if l.expires_at else None,
            }
            for l in listings
        ]
    }


# ─── 2. Active Listings ───────────────────────────────────────────────────────

@router.get(
    "/listings/active",
    summary="[Public] Active listings — real-time supply feed",
    description=(
        "No authentication required.\n\n"
        "Returns only active, non-expired listings with price range filters.\n\n"
        "**AI Agent uses this to answer:**\n"
        "- What % of active supply is Solar vs Wind vs Hydro?\n"
        "- Which source has highest available supply right now?\n"
        "- Demand-to-supply ratio by renewable source\n"
        "- Best available credit based on price + availability\n\n"
        "**Used by:** AI Agent real-time supply queries, Buyer recommendation engine"
    )
)
def get_active_listings_public(
    energy_source: Optional[EnergySource] = Query(None, description="Filter by energy source"),
    location: Optional[str] = Query(None, description="Filter by location (partial match)"),
    min_price_per_kwh: Optional[float] = Query(None, ge=0, description="Minimum price per kWh in ETH"),
    max_price_per_kwh: Optional[float] = Query(None, ge=0, description="Maximum price per kWh in ETH"),
    min_energy_kwh: Optional[int] = Query(None, ge=1, description="Minimum available energy in kWh"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at | price_per_kwh | energy_kwh"),
    sort_order: Optional[str] = Query("desc", description="Sort direction: asc | desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_read_db)
):
    now = datetime.utcnow()

    query = db.query(Listing).filter(
        Listing.status == ListingStatus.ACTIVE
    ).filter(
        (Listing.expires_at.is_(None)) | (Listing.expires_at > now)
    )

    if energy_source:
        query = query.filter(Listing.energy_source == energy_source)
    if location:
        query = query.filter(Listing.location.ilike(f"%{location}%"))
    if min_price_per_kwh is not None:
        query = query.filter(Listing.price_per_kwh >= min_price_per_kwh)
    if max_price_per_kwh is not None:
        query = query.filter(Listing.price_per_kwh <= max_price_per_kwh)
    if min_energy_kwh is not None:
        query = query.filter(Listing.energy_kwh >= min_energy_kwh)

    # Sorting
    sort_column = {
        "price_per_kwh": Listing.price_per_kwh,
        "energy_kwh": Listing.energy_kwh,
        "created_at": Listing.created_at,
    }.get(sort_by, Listing.created_at)

    query = query.order_by(
        sort_column.asc() if sort_order == "asc" else sort_column.desc()
    )

    total = query.count()
    listings = query.offset(skip).limit(limit).all()

    # Per-source active supply summary for AI
    source_summary = db.query(
        Listing.energy_source,
        func.count(Listing.id).label("active_count"),
        func.sum(Listing.energy_kwh).label("total_kwh"),
        func.avg(Listing.price_per_kwh).label("avg_price"),
        func.min(Listing.price_per_kwh).label("min_price"),
        func.max(Listing.price_per_kwh).label("max_price"),
    ).filter(
        Listing.status == ListingStatus.ACTIVE,
        (Listing.expires_at.is_(None)) | (Listing.expires_at > now)
    ).group_by(Listing.energy_source).all()

    total_active_kwh = sum(float(r.total_kwh or 0) for r in source_summary)
    source_breakdown = {}
    for row in source_summary:
        kwh = float(row.total_kwh or 0)
        source_breakdown[str(row.energy_source)] = {
            "active_listings": row.active_count,
            "total_kwh_available": kwh,
            "market_share_pct": round((kwh / total_active_kwh * 100) if total_active_kwh > 0 else 0, 2),
            "avg_price_per_kwh": round(float(row.avg_price or 0), 6),
            "min_price_per_kwh": round(float(row.min_price or 0), 6),
            "max_price_per_kwh": round(float(row.max_price or 0), 6),
        }

    # Location supply breakdown for "which location has most wind supply?" type questions
    location_summary = db.query(
        Listing.location,
        Listing.energy_source,
        func.sum(Listing.energy_kwh).label("total_kwh"),
        func.count(Listing.id).label("count"),
    ).filter(
        Listing.status == ListingStatus.ACTIVE,
        (Listing.expires_at.is_(None)) | (Listing.expires_at > now)
    ).group_by(Listing.location, Listing.energy_source).all()

    location_breakdown = {}
    for row in location_summary:
        loc = str(row.location or "Unknown")
        if loc not in location_breakdown:
            location_breakdown[loc] = {}
        location_breakdown[loc][str(row.energy_source)] = {
            "listings": row.count,
            "total_kwh": float(row.total_kwh or 0)
        }

    return {
        "meta": {
            "total_active_listings": total,
            "total_active_kwh": total_active_kwh,
            "skip": skip,
            "limit": limit,
            "as_of": now.isoformat(),
            "ai_context": "source_breakdown has market_share_pct — use for supply ratio questions. location_breakdown answers location-based supply questions."
        },
        "source_breakdown": source_breakdown,
        "location_breakdown": location_breakdown,
        "listings": [
            {
                "id": str(l.id),
                "energy_source": l.energy_source,
                "energy_kwh": l.energy_kwh,
                "price_per_kwh": float(l.price_per_kwh),
                "location": l.location,
                "blockchain_verified": l.blockchain_tx_hash is not None,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "expires_at": l.expires_at.isoformat() if l.expires_at else None,
            }
            for l in listings
        ]
    }


# ─── 3. All Purchases ─────────────────────────────────────────────────────────

@router.get(
    "/purchases",
    summary="[Public] All purchases — AI demand & pricing history feed",
    description=(
        "No authentication required.\n\n"
        "Returns completed purchase history with demand analytics per source.\n\n"
        "**AI Agent uses this to answer:**\n"
        "- Compare Solar vs Wind vs Hydro demand during a period\n"
        "- Which source had highest average selling price?\n"
        "- Which source had highest price volatility?\n"
        "- Predict which source will have highest demand next month\n"
        "- Demand-to-supply ratio by renewable source\n"
        "- Is Noida likely to face Solar-credit shortage?\n\n"
        "**Used by:** AI Prediction Engine, RAG context, Demand forecasting model"
    )
)
def get_all_purchases_public(
    energy_source: Optional[EnergySource] = Query(None, description="Filter by energy source of the purchased listing"),
    location: Optional[str] = Query(None, description="Filter by seller location (partial match)"),
    status: Optional[PurchaseStatus] = Query(None, description="Filter by purchase status"),
    completed_from: Optional[datetime] = Query(None, description="Filter purchases completed after this datetime"),
    completed_to: Optional[datetime] = Query(None, description="Filter purchases completed before this datetime"),
    group_by_month: bool = Query(False, description=(
        "If true, returns monthly price trend per source. "
        "Used by AI Prediction Engine to forecast next month price. "
        "Each month bucket has avg_price, total_kwh, purchase_count per energy_source."
    )),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_read_db)
):
    query = db.query(Purchase).join(
        Listing, Purchase.listing_id == Listing.id
    )

    if energy_source:
        query = query.filter(Listing.energy_source == energy_source)
    if location:
        query = query.filter(Listing.location.ilike(f"%{location}%"))
    if status:
        query = query.filter(Purchase.status == status)
    if completed_from:
        query = query.filter(Purchase.completed_at >= completed_from)
    if completed_to:
        query = query.filter(Purchase.completed_at <= completed_to)

    total = query.count()
    purchases = query.order_by(Purchase.created_at.desc()).offset(skip).limit(limit).all()

    # Demand analytics per source — core AI training signal
    demand_stats = db.query(
        Listing.energy_source,
        func.count(Purchase.id).label("total_purchases"),
        func.sum(Purchase.energy_kwh).label("total_kwh_sold"),
        func.avg(Purchase.price_per_kwh).label("avg_price"),
        func.min(Purchase.price_per_kwh).label("min_price"),
        func.max(Purchase.price_per_kwh).label("max_price"),
        # Price volatility = max - min (simple range metric)
        (func.max(Purchase.price_per_kwh) - func.min(Purchase.price_per_kwh)).label("price_volatility"),
        func.sum(Purchase.total_price).label("total_revenue"),
    ).join(
        Listing, Purchase.listing_id == Listing.id
    ).filter(
        Purchase.status.in_([PurchaseStatus.COMPLETED, PurchaseStatus.CONSUMED])
    ).group_by(Listing.energy_source).all()

    total_kwh_sold = sum(float(r.total_kwh_sold or 0) for r in demand_stats)
    demand_by_source = {}
    for row in demand_stats:
        kwh = float(row.total_kwh_sold or 0)
        demand_by_source[str(row.energy_source)] = {
            "total_purchases": row.total_purchases,
            "total_kwh_sold": kwh,
            "demand_share_pct": round((kwh / total_kwh_sold * 100) if total_kwh_sold > 0 else 0, 2),
            "avg_price_per_kwh": round(float(row.avg_price or 0), 6),
            "min_price_per_kwh": round(float(row.min_price or 0), 6),
            "max_price_per_kwh": round(float(row.max_price or 0), 6),
            "price_volatility": round(float(row.price_volatility or 0), 6),
            "total_revenue_eth": round(float(row.total_revenue or 0), 6),
        }

    # Location demand breakdown — for shortage prediction by location
    location_demand = db.query(
        Listing.location,
        Listing.energy_source,
        func.count(Purchase.id).label("purchases"),
        func.sum(Purchase.energy_kwh).label("kwh_sold"),
    ).join(
        Listing, Purchase.listing_id == Listing.id
    ).filter(
        Purchase.status.in_([PurchaseStatus.COMPLETED, PurchaseStatus.CONSUMED])
    ).group_by(Listing.location, Listing.energy_source).all()

    location_demand_breakdown = {}
    for row in location_demand:
        loc = str(row.location or "Unknown")
        if loc not in location_demand_breakdown:
            location_demand_breakdown[loc] = {}
        location_demand_breakdown[loc][str(row.energy_source)] = {
            "purchases": row.purchases,
            "kwh_sold": float(row.kwh_sold or 0)
        }

    # ── Monthly price trend — used by Prediction Engine ──────────────────────
    # When group_by_month=True, returns time-series avg price per source per month.
    # AI Agent feeds this into the forecasting model to predict next month prices.
    # Example: SOLAR avg prices: [1.1, 1.2, 1.3, 1.4] → trend is UP → predict 1.5
    monthly_trend = []
    if group_by_month:
        trend_rows = db.query(
            func.date_trunc('month', Purchase.completed_at).label("month"),
            Listing.energy_source,
            func.avg(Purchase.price_per_kwh).label("avg_price"),
            func.sum(Purchase.energy_kwh).label("total_kwh"),
            func.count(Purchase.id).label("purchase_count"),
        ).join(
            Listing, Purchase.listing_id == Listing.id
        ).filter(
            Purchase.status.in_([PurchaseStatus.COMPLETED, PurchaseStatus.CONSUMED]),
            Purchase.completed_at.isnot(None)
        )
        if completed_from:
            trend_rows = trend_rows.filter(Purchase.completed_at >= completed_from)
        if completed_to:
            trend_rows = trend_rows.filter(Purchase.completed_at <= completed_to)
        if energy_source:
            trend_rows = trend_rows.filter(Listing.energy_source == energy_source)

        trend_rows = trend_rows.group_by(
            func.date_trunc('month', Purchase.completed_at),
            Listing.energy_source
        ).order_by(
            func.date_trunc('month', Purchase.completed_at).asc(),
            Listing.energy_source
        ).all()

        for row in trend_rows:
            monthly_trend.append({
                "month": row.month.strftime("%Y-%m") if row.month else None,
                "energy_source": str(row.energy_source),
                "avg_price_per_kwh": round(float(row.avg_price or 0), 6),
                "total_kwh_sold": float(row.total_kwh or 0),
                "purchase_count": row.purchase_count,
            })

    return {
        "meta": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "filters_applied": {
                "energy_source": energy_source,
                "location": location,
                "status": status,
                "completed_from": completed_from,
                "completed_to": completed_to,
            },
            "ai_context": (
                "demand_by_source has price_volatility and demand_share_pct — "
                "use for price volatility ranking, demand comparison, and highest avg price questions. "
                "location_demand_breakdown supports shortage prediction by location. "
                "monthly_price_trend (when group_by_month=true) provides time-series data "
                "for the Prediction Engine to forecast next month prices per source."
            )
        },
        "demand_by_source": demand_by_source,
        "location_demand_breakdown": location_demand_breakdown,
        "monthly_price_trend": monthly_trend if group_by_month else "pass group_by_month=true to get time-series trend for price prediction",
        "purchases": [
            {
                "id": str(p.id),
                "listing_id": str(p.listing_id),
                "energy_source": p.listing.energy_source if p.listing else None,
                "location": p.listing.location if p.listing else None,
                "energy_kwh": p.energy_kwh,
                "price_per_kwh": float(p.price_per_kwh),
                "total_price": float(p.total_price),
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            }
            for p in purchases
        ]
    }

