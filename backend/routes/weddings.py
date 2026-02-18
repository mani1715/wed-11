from fastapi import APIRouter, HTTPException, status, Request, Depends
from models import (
    Wedding, WeddingCreate, WeddingUpdate, WeddingResponse, 
    WeddingStatus, PublishRequest, CreditLedger, CreditTransactionType
)
from dependencies import get_current_admin, get_super_admin
from credit_calculator import calculate_credit_cost
from typing import List
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=WeddingResponse, status_code=status.HTTP_201_CREATED)
async def create_wedding(
    wedding_data: WeddingCreate,
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new wedding in DRAFT status"""
    db = request.app.state.db
    
    # Check if slug is unique
    existing_wedding = await db.weddings.find_one({"slug": wedding_data.slug})
    if existing_wedding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists. Please choose a different slug."
        )
    
    # Create wedding
    new_wedding = Wedding(
        admin_id=current_admin["id"],
        title=wedding_data.title,
        slug=wedding_data.slug,
        status=WeddingStatus.DRAFT
    )
    
    await db.weddings.insert_one(new_wedding.dict())
    
    return WeddingResponse(**new_wedding.dict())

@router.get("/", response_model=List[WeddingResponse])
async def list_weddings(
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """List weddings for current admin (or all for super admin)"""
    db = request.app.state.db
    
    # Super admin can see all weddings
    if current_admin.get("role") == "SUPER_ADMIN":
        weddings = await db.weddings.find().to_list(length=None)
    else:
        # Regular admin sees only their weddings
        weddings = await db.weddings.find({"admin_id": current_admin["id"]}).to_list(length=None)
    
    return [WeddingResponse(**wedding) for wedding in weddings]

@router.get("/{wedding_id}", response_model=WeddingResponse)
async def get_wedding(
    wedding_id: str,
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Get a specific wedding"""
    db = request.app.state.db
    
    wedding = await db.weddings.find_one({"id": wedding_id})
    if not wedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wedding not found"
        )
    
    # Check ownership (unless super admin)
    if current_admin.get("role") != "SUPER_ADMIN" and wedding["admin_id"] != current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return WeddingResponse(**wedding)

@router.put("/{wedding_id}", response_model=WeddingResponse)
async def update_wedding(
    wedding_id: str,
    update_data: WeddingUpdate,
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a wedding"""
    db = request.app.state.db
    
    # Find wedding
    wedding = await db.weddings.find_one({"id": wedding_id})
    if not wedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wedding not found"
        )
    
    # Check ownership
    if current_admin.get("role") != "SUPER_ADMIN" and wedding["admin_id"] != current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if slug is being changed and is unique
    if update_data.slug and update_data.slug != wedding["slug"]:
        existing_wedding = await db.weddings.find_one({"slug": update_data.slug})
        if existing_wedding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already exists"
            )
    
    # Build update dict
    update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    # Recalculate credit cost if design or features changed
    if "selected_design_key" in update_dict or "selected_features" in update_dict:
        design_key = update_dict.get("selected_design_key", wedding.get("selected_design_key"))
        features = update_dict.get("selected_features", wedding.get("selected_features", []))
        
        if design_key:
            cost_data = calculate_credit_cost(design_key, features)
            update_dict["total_credit_cost"] = cost_data["total_cost"]
    
    # Update wedding
    await db.weddings.update_one(
        {"id": wedding_id},
        {"$set": update_dict}
    )
    
    # Fetch updated wedding
    updated_wedding = await db.weddings.find_one({"id": wedding_id})
    return WeddingResponse(**updated_wedding)

@router.post("/publish", response_model=dict)
async def publish_wedding(
    publish_request: PublishRequest,
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Publish a wedding (consumes credits)"""
    db = request.app.state.db
    
    wedding_id = publish_request.wedding_id
    
    # Find wedding
    wedding = await db.weddings.find_one({"id": wedding_id})
    if not wedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wedding not found"
        )
    
    # Check ownership
    if wedding["admin_id"] != current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if already published
    if wedding["status"] == WeddingStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wedding is already published"
        )
    
    # Validate required fields
    if not wedding.get("selected_design_key"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select a design before publishing"
        )
    
    # Calculate credits needed
    design_key = wedding["selected_design_key"]
    features = wedding.get("selected_features", [])
    cost_data = calculate_credit_cost(design_key, features)
    total_cost = cost_data["total_cost"]
    
    # Check if this is an upgrade (already published before)
    credits_to_deduct = total_cost
    if wedding.get("published_at"):
        # This is an upgrade - only charge the difference
        previous_cost = wedding.get("total_credit_cost", 0)
        credits_to_deduct = max(0, total_cost - previous_cost)
    
    # Check if admin has sufficient credits
    admin = await db.admins.find_one({"id": current_admin["id"]})
    available_credits = admin["available_credits"]
    
    if available_credits < credits_to_deduct:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Required: {credits_to_deduct}, Available: {available_credits}"
        )
    
    # Start transaction-like operation
    try:
        # Deduct credits
        new_balance = available_credits - credits_to_deduct
        await db.admins.update_one(
            {"id": current_admin["id"]},
            {
                "$set": {
                    "available_credits": new_balance,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Create ledger entry
        ledger_entry = CreditLedger(
            admin_id=current_admin["id"],
            transaction_type=CreditTransactionType.DEDUCT,
            amount=credits_to_deduct,
            balance_after=new_balance,
            description=f"Published wedding: {wedding['title']}",
            wedding_id=wedding_id
        )
        await db.credit_ledger.insert_one(ledger_entry.dict())
        
        # Update wedding status
        await db.weddings.update_one(
            {"id": wedding_id},
            {
                "$set": {
                    "status": WeddingStatus.PUBLISHED,
                    "published_at": datetime.utcnow(),
                    "total_credit_cost": total_cost,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "message": "Wedding published successfully",
            "credits_deducted": credits_to_deduct,
            "remaining_credits": new_balance,
            "wedding_url": f"/wedding/{wedding['slug']}"
        }
    
    except Exception as e:
        # If anything fails, we should rollback (in production use proper transactions)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish wedding: {str(e)}"
        )

@router.post("/{wedding_id}/archive", response_model=dict)
async def archive_wedding(
    wedding_id: str,
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Archive a wedding"""
    db = request.app.state.db
    
    # Find wedding
    wedding = await db.weddings.find_one({"id": wedding_id})
    if not wedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wedding not found"
        )
    
    # Check ownership
    if wedding["admin_id"] != current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Archive wedding
    await db.weddings.update_one(
        {"id": wedding_id},
        {
            "$set": {
                "status": WeddingStatus.ARCHIVED,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Wedding archived successfully"}

@router.get("/{wedding_id}/estimate", response_model=dict)
async def estimate_credits(
    wedding_id: str,
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Get credit estimation for a wedding"""
    db = request.app.state.db
    
    # Find wedding
    wedding = await db.weddings.find_one({"id": wedding_id})
    if not wedding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wedding not found"
        )
    
    # Check ownership
    if current_admin.get("role") != "SUPER_ADMIN" and wedding["admin_id"] != current_admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    design_key = wedding.get("selected_design_key")
    features = wedding.get("selected_features", [])
    
    if not design_key:
        return {
            "design_cost": 0,
            "features_cost": 0,
            "total_cost": 0,
            "breakdown": {}
        }
    
    cost_data = calculate_credit_cost(design_key, features)
    return cost_data