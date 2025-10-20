#!/usr/bin/env python3
"""
Direct database fix for the ajuda.vip reseller issue.
This will directly update the MongoDB database.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'support_chat')

# Target data
REPORTED_EMAIL = "michaelrv@gmail.com"  # Expected email from review request
REPORTED_PASSWORD = "ab181818ab"
REPORTED_DOMAIN = "ajuda.vip"

async def fix_reseller():
    """Fix the reseller directly in the database"""
    print("🔧 DIRECT DATABASE FIX FOR AJUDA.VIP RESELLER")
    print("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Find the reseller with ajuda.vip domain
        print(f"🔍 Finding reseller with domain: {REPORTED_DOMAIN}")
        
        reseller = await db.resellers.find_one({
            "$or": [
                {"custom_domain": REPORTED_DOMAIN},
                {"domain": REPORTED_DOMAIN}
            ]
        })
        
        if not reseller:
            print(f"❌ No reseller found with domain {REPORTED_DOMAIN}")
            return
            
        reseller_id = reseller.get('id')
        current_email = reseller.get('email')
        current_name = reseller.get('name')
        
        print(f"✅ Found reseller:")
        print(f"   ID: {reseller_id}")
        print(f"   Name: {current_name}")
        print(f"   Current Email: {current_email}")
        print(f"   Domain: {reseller.get('domain')}")
        print(f"   Custom Domain: {reseller.get('custom_domain')}")
        
        # Generate new password hash
        print(f"🔐 Generating password hash for: {REPORTED_PASSWORD}")
        pass_hash = bcrypt.hashpw(REPORTED_PASSWORD.encode(), bcrypt.gensalt()).decode()
        
        # Update the reseller
        print(f"📝 Updating reseller with:")
        print(f"   New Email: {REPORTED_EMAIL}")
        print(f"   New Password: {REPORTED_PASSWORD}")
        
        result = await db.resellers.update_one(
            {"id": reseller_id},
            {"$set": {
                "email": REPORTED_EMAIL,
                "pass_hash": pass_hash
            }}
        )
        
        if result.modified_count > 0:
            print("✅ Reseller updated successfully in database")
        else:
            print("❌ Failed to update reseller in database")
            return
            
        # Verify the update
        print("🔍 Verifying update...")
        updated_reseller = await db.resellers.find_one({"id": reseller_id})
        
        if updated_reseller:
            print(f"✅ Verification successful:")
            print(f"   Email: {updated_reseller.get('email')}")
            print(f"   Password hash updated: {'Yes' if updated_reseller.get('pass_hash') != reseller.get('pass_hash') else 'No'}")
            
            # Test password hash
            stored_hash = updated_reseller.get('pass_hash')
            if bcrypt.checkpw(REPORTED_PASSWORD.encode(), stored_hash.encode()):
                print("✅ Password hash verification successful")
            else:
                print("❌ Password hash verification failed")
        else:
            print("❌ Could not verify update")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        client.close()
        
    print("\n" + "=" * 60)
    print("🎯 DATABASE FIX COMPLETED")
    print(f"   Domain: {REPORTED_DOMAIN}")
    print(f"   Email: {REPORTED_EMAIL}")
    print(f"   Password: {REPORTED_PASSWORD}")
    print("   Status: ✅ UPDATED IN DATABASE")

if __name__ == "__main__":
    asyncio.run(fix_reseller())