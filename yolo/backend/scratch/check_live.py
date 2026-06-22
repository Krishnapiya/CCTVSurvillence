import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # First, login to get access token
        login_res = await client.post(
            "http://localhost:8005/api/v1/auth/login",
            data={"username": "admin", "password": "password"}
        )
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.status_code} {login_res.text}")
            return
            
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get live status
        status_res = await client.get("http://localhost:8005/api/v1/cameras/status/live", headers=headers)
        print("\n=== LIVE CAMERA STATUS ===")
        for cam in status_res.json():
            print(f"Name: {cam['name']}")
            print(f"ID: {cam['id']}")
            print(f"Status: {cam['status']}")
            print(f"FPS: {cam['fps']}")
            print(f"Last Seen: {cam['last_seen']}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
