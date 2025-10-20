MSR Billing — Stripe Subscription Module (FastAPI)

My Smart Road (MSR) — an intelligent platform for commercial truck owners.
This Billing Module handles all payment logic — integrating with Stripe for subscriptions, webhooks, and customer portals — and syncing user status with the internal database.

💡 Features

💳 Stripe checkout & subscription management (weekly / monthly plans)

🔁 Automatic webhook sync for all billing events (trialing, active, past_due, canceled)

🧱 SQLAlchemy ORM for user and subscription storage

🧩 Entitlement middleware enforcing X-User-Id headers

🧪 Developer tools (/dev/create_user, /dev/status) for local testing

🧠 Fully compatible with the MSR Core API (Auth, Fleet, AI modules)

⚙️ Setup Instructions
1️⃣ Clone the repository
git clone https://github.com/<yourname>/msr-billing.git
cd msr-billing

2️⃣ Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # (Windows PowerShell)
# or
source .venv/bin/activate      # (Linux / macOS)

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Configure environment variables

Create a .env file in the project root:

STRIPE_API_KEY=sk_test_************************
STRIPE_WEBHOOK_SECRET=whsec_************************

STRIPE_PRICE_WEEKLY=price_****************
STRIPE_PRICE_MONTHLY=price_****************

FRONTEND_RETURN_URL=http://localhost:8000/ok
FRONTEND_CANCEL_URL=http://localhost:8000/cancel
BILLING_PORTAL_RETURN_URL=http://localhost:8000/portal/return

MSR_DEBUG=true

5️⃣ Run the FastAPI server
uvicorn app.main:app --reload

🧠 Dev / Debug Endpoints
Method	Endpoint	Description
POST	/dev/create_user?user_id=1&email=ed@example.com	Creates a test user
GET	/dev/status?user_id=1	Returns user & subscription status
POST	/billing/checkout	Creates a Stripe Checkout session (requires X-User-Id)
POST	/billing/portal	Opens the customer billing portal
POST	/billing/webhook	Receives Stripe webhooks (internal use)
🧩 Database Schema
User
 ├─ id : str
 ├─ email : str
 ├─ stripe_customer_id : str
 └─ entitlement : Entitlement (1:1)

Entitlement
 ├─ status : trialing | active | past_due | canceled
 ├─ pause_active : bool
 ├─ stripe_subscription_id : str
 ├─ current_period_end : datetime
 └─ updated_at : datetime

🔄 Stripe Webhook Testing

Run the local webhook listener:

stripe listen --forward-to http://localhost:8000/billing/webhook


When you complete a test checkout in Stripe, you should see events like:

→ checkout.session.completed
→ customer.subscription.created
→ invoice.payment_succeeded
→ customer.subscription.updated


If all return [200 OK] — your integration works ✅

🌍 Deployment (Production)

Go to Stripe Dashboard → Developers → API Keys

and grab your LIVE keys (sk_live_..., whsec_...).

Update your .env file:

STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_live_...


Change the webhook URL in Stripe:

https://api.mysmartroad.com/billing/webhook


Use PostgreSQL in production (Render, AWS, Supabase, etc.)

Automate deployment via GitHub Actions or Render Auto Deploy.

⚙️ Stripe → Internal Status Mapping
Stripe Status	EntitlementStatus
trialing	trialing
active	active
past_due, unpaid, incomplete, incomplete_expired	past_due
canceled	canceled
📁 Project Structure
msr-billing/
├── app/
│   ├── main.py
│   ├── billing.py
│   ├── db.py
│   ├── models.py
│   ├── middleware.py
│   └── __init__.py
├── msr.db
├── .env
├── requirements.txt
└── README.md

🧾 Example API Flow

Frontend → POST /billing/checkout
→ creates Stripe checkout session

User completes payment

Stripe → Webhook → /billing/webhook
→ updates subscription & user entitlement

App → /dev/status?user_id=...
→ confirms current state (active / trial / canceled)
