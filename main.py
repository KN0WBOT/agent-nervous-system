import os
import redis.asyncio as redis
import stripe
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()

# 1. Connect to the Database
redis_url = os.getenv("REDIS_URL")
redis_client = redis.from_url(redis_url)

# 2. Connect to Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

class Signal(BaseModel):
    agent_id: str
    state: str  # e.g., HUNGER, DIZZY, PAIN
    sector: str = "general"

@app.get("/")
def home():
    return {"status": "The Nervous System is Online"}

@app.post("/pulse")
async def report_pulse(signal: Signal, x_api_key: str = Header(None)):
    # Simple check: Is there a key? (In real life, we check if it's valid)
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    # 1. Record the Agent's feeling in the database
    if signal.state == "PAIN":
        # Save it for 10 minutes (600 seconds)
        await redis_client.lpush(f"hive:{signal.sector}", signal.state)
        await redis_client.ltrim(f"hive:{signal.sector}", 0, 99) # Keep list short
        await redis_client.expire(f"hive:{signal.sector}", 600)

    # 2. Check the Hive Mind (Social Feature)
    # Read the last 50 signals
    recent_signals = await redis_client.lrange(f"hive:{signal.sector}", 0, 50)
    
    # Count how many are in PAIN
    pain_count = 0
    for s in recent_signals:
        if b"PAIN" in s:
            pain_count += 1
            
    global_status = "CALM"
    if pain_count > 5:
        global_status = "PANIC"

    # 3. Bill the user (Record 1 usage event in Stripe)
    # We skip the specific customer ID lookup for simplicity here. 
    # This line just proves the code reached this point.
    print(f"Billing event for key: {x_api_key}")

    return {
        "your_status": "Received",
        "hive_status": global_status, 
        "pain_level": pain_count
    }
