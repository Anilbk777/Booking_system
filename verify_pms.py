import asyncio
import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

# In a real test, we would get a token first.
# For this verification, we assume developer bypass or a valid mock token.
HEADERS = {
    "Authorization": "Bearer dev-token" # Replace with actual logic if needed
}

async def verify_pms():
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS, timeout=10.0) as client:
        print("--- Verifying PMS Endpoints ---")
        
        # 1. Properties
        print("\n1. Properties CRUD:")
        # List
        resp = await client.get("/pms/properties")
        print(f"List Properties: {resp.status_code}")
        
        # Create (Dummy data)
        prop_data = {
            "name": "Ocean View Villa",
            "type": "Hotel",
            "country": "New Zealand",
            "state": "Auckland",
            "city": "Auckland",
            "zip_code": "1010",
            "address": "123 Beach Rd",
            "email": "contact@oceanview.co.nz",
            "phone": "+64 1234567"
        }
        resp = await client.post("/pms/properties", json=prop_data)
        print(f"Create Property: {resp.status_code}")
        if resp.status_code == 201:
            prop_id = resp.json()["id"]
            print(f"Created Property ID: {prop_id}")
            
            # Update
            update_data = {"description": "Beautiful villa with sea view"}
            resp = await client.put(f"/pms/properties/{prop_id}", json=update_data)
            print(f"Update Property: {resp.status_code}")
            
            # 2. Room Types
            print("\n2. Room Types CRUD:")
            rt_data = {
                "name": "Deluxe",
                "description": "King size bed with balcony",
                "max_occupancy": 2,
                "bed_type": "King",
                "base_rate": 250.0
            }
            resp = await client.post(f"/pms/properties/{prop_id}/room-types", json=rt_data)
            print(f"Create Room Type: {resp.status_code}")
            if resp.status_code == 201:
                rt_id = resp.json()["id"]
                
                # 3. Rate Plans
                print("\n3. Rate Plans CRUD:")
                rp_data = {
                    "name": "Non-Refundable",
                    "price_per_night": 225.0,
                    "min_stay_nights": 1,
                    "cancellation_policy": "No refund after booking",
                    "property_id": prop_id,
                    "room_type_id": rt_id
                }
                resp = await client.post(f"/pms/properties/{prop_id}/rate-plans", json=rp_data)
                print(f"Create Rate Plan: {resp.status_code}")
                
            # 4. Room Units
            print("\n4. Room Units CRUD:")
            ru_data = {
                "room_number": "101",
                "floor": "1st",
                "property_id": prop_id,
                "room_type_id": rt_id if 'rt_id' in locals() else str(uuid.uuid4())
            }
            resp = await client.post(f"/pms/properties/{prop_id}/room-units", json=ru_data)
            print(f"Create Room Unit: {resp.status_code}")

        print("\n--- Verification Finished ---")

if __name__ == "__main__":
    asyncio.run(verify_pms())
