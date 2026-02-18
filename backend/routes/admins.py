from fastapi import APIRouter, HTTPException, status, Request, Depends
from models import AdminResponse
from dependencies import get_current_admin, get_super_admin
from typing import List

router = APIRouter()

@router.get("/", response_model=List[AdminResponse])
async def list_admins(
    request: Request,
    current_admin: dict = Depends(get_super_admin)
):
    """List all admins (Super Admin only)"""
    db = request.app.state.db
    admins = await db.admins.find().to_list(length=None)
    return [AdminResponse(**admin) for admin in admins]

@router.post("/{admin_id}/credits", response_model=dict)
async def add_credits(
    admin_id: str,
    amount: int,
    request: Request,
    current_admin: dict = Depends(get_super_admin)
):
    """Add credits to an admin account (Super Admin only)"""
    from models import CreditLedger, CreditTransactionType
    from datetime import datetime
    
    db = request.app.state.db
    
    # Find admin
    admin = await db.admins.find_one({"id": admin_id})
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Update admin credits
    new_balance = admin["available_credits"] + amount
    await db.admins.update_one(
        {"id": admin_id},
        {
            "$set": {
                "available_credits": new_balance,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Create ledger entry
    ledger_entry = CreditLedger(
        admin_id=admin_id,
        transaction_type=CreditTransactionType.CREDIT,
        amount=amount,
        balance_after=new_balance,
        description=f"Credits added by Super Admin {current_admin['full_name']}"
    )
    await db.credit_ledger.insert_one(ledger_entry.dict())
    
    return {
        "message": "Credits added successfully",
        "new_balance": new_balance
    }