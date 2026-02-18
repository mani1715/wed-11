# Wedding Platform - Phase 37: Wedding Ownership, Draft System & Publish Workflow

## Overview
A complete wedding website management platform with admin authentication, credit-based publishing system, and wedding lifecycle management (Draft → Ready → Published → Archived).

## Features Implemented

### Backend (FastAPI + MongoDB)
- ✅ Admin authentication (register/login with JWT)
- ✅ Wedding CRUD operations
- ✅ Credit management system
- ✅ Publishing workflow with credit deduction
- ✅ Draft system (free, unlimited)
- ✅ Credit estimation engine
- ✅ Archive functionality
- ✅ Super Admin capabilities

### Frontend (React + Tailwind CSS)
- ✅ Admin Dashboard with wedding cards
- ✅ Login/Register pages
- ✅ Wedding Editor (step-based: Basic Info → Design → Features → Preview)
- ✅ Publish Modal with credit breakdown
- ✅ Real-time credit estimation
- ✅ Protected routes

## Tech Stack
- **Backend**: FastAPI, MongoDB (Motor), Python-JOSE, Passlib
- **Frontend**: React 19, React Router v7, Axios, Tailwind CSS, Headless UI
- **Authentication**: JWT tokens
- **Database**: MongoDB (local)

## Architecture

### Wedding Lifecycle
1. **DRAFT**: Free to create, unlimited edits
2. **READY**: All required fields filled, design selected
3. **PUBLISHED**: Credits consumed, live on public URL
4. **ARCHIVED**: Disabled public access, no refund

### Credit System
- **Designs**: Basic (10), Elegant (20), Luxury (30), Royal (50)
- **Features**: RSVP (5), Gallery (10), Guestbook (5), Countdown (3), Music (5), Video (15), Live Streaming (25), Gift Registry (10)
- Credits consumed only on publish
- Upgrades charge only the difference
- Downgrades don't refund credits

### Security
- Admin-specific data isolation
- JWT-based authentication
- Slug uniqueness validation
- Credit balance validation before publish

## API Endpoints

### Authentication
- POST `/api/auth/register` - Create admin account
- POST `/api/auth/login` - Login admin
- GET `/api/auth/me` - Get current admin

### Weddings
- POST `/api/weddings/` - Create wedding (draft)
- GET `/api/weddings/` - List weddings (filtered by admin)
- GET `/api/weddings/{id}` - Get wedding details
- PUT `/api/weddings/{id}` - Update wedding
- POST `/api/weddings/publish` - Publish wedding (consumes credits)
- POST `/api/weddings/{id}/archive` - Archive wedding
- GET `/api/weddings/{id}/estimate` - Get credit estimate

### Credits
- GET `/api/credits/balance` - Get current balance
- GET `/api/credits/ledger` - Get transaction history
- GET `/api/credits/config` - Get pricing configuration

### Admin (Super Admin only)
- GET `/api/admins/` - List all admins
- POST `/api/admins/{id}/credits` - Add credits to admin

## Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=wedding_platform
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Running the Application

### Start Services
```bash
sudo supervisorctl restart all
```

### Check Status
```bash
sudo supervisorctl status
```

### View Logs
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log

# Frontend logs
tail -f /var/log/supervisor/frontend.err.log
tail -f /var/log/supervisor/frontend.out.log
```

## Default Admin Account
You'll need to register a new admin account via the UI at `/register` or API.

For Super Admin capabilities, manually update the `role` field in MongoDB:
```javascript
db.admins.updateOne(
  { email: "admin@example.com" },
  { $set: { role: "SUPER_ADMIN" } }
)
```

## Database Schema

### Admin
- id (UUID)
- email
- hashed_password
- full_name
- role (ADMIN | SUPER_ADMIN)
- available_credits
- created_at, updated_at

### Wedding
- id (UUID)
- admin_id (owner)
- title
- slug (unique)
- status (DRAFT | READY | PUBLISHED | ARCHIVED)
- selected_design_key
- selected_features (array)
- total_credit_cost
- published_at
- created_at, updated_at

### CreditLedger
- id (UUID)
- admin_id
- transaction_type (CREDIT | DEDUCT)
- amount
- balance_after
- description
- wedding_id (optional)
- created_at

## Phase 37 Status: ✅ COMPLETE

All requirements implemented:
- ✅ Wedding ownership by admin
- ✅ Draft system (unlimited, free)
- ✅ Credit estimation engine
- ✅ Publish workflow with atomic credit deduction
- ✅ Post-publish editing and upgrades
- ✅ Archive system
- ✅ Admin dashboard with wedding cards
- ✅ Step-based wedding editor
- ✅ Publish modal with credit breakdown
- ✅ Security and data isolation
