from fastapi import APIRouter, HTTPException, status, Request, Depends
from models import CreditLedger
from dependencies import get_current_admin
from typing import List

router = APIRouter()

@router.get("/ledger", response_model=List[dict])
async def get_credit_ledger(
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Get credit transaction history for current admin"""
    db = request.app.state.db
    
    ledger_entries = await db.credit_ledger.find(
        {"admin_id": current_admin["id"]}
    ).sort("created_at", -1).to_list(length=None)
    
    return ledger_entries

@router.get("/balance", response_model=dict)
async def get_credit_balance(
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Get current credit balance"""
    db = request.app.state.db
    
    admin = await db.admins.find_one({"id": current_admin["id"]})
    
    return {
        "available_credits": admin["available_credits"],
        "admin_id": admin["id"],
        "admin_name": admin["full_name"]
    }

@router.get("/config", response_model=dict)
async def get_credit_config():
    """Get credit pricing configuration"""
    from models import CreditConfig
    config = CreditConfig()
    return {
        "designs": config.designs,
        "features": config.features
    }