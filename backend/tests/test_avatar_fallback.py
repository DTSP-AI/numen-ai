"""
Quick test script for avatar filesystem fallback
"""
import asyncio
import httpx
import base64

async def test_avatar_upload():
    """Test avatar upload with filesystem fallback"""

    # Create a tiny test PNG (1x1 red pixel)
    test_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    test_png_bytes = base64.b64decode(test_png_b64)

    # Upload via API
    files = {"file": ("test.png", test_png_bytes, "image/png")}
    headers = {
        "x-tenant-id": "test-tenant-123",
        "x-user-id": "test-user-456"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "http://localhost:8000/api/avatar/upload",
            files=files,
            headers=headers
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Avatar uploaded successfully!")
            print(f"URL: {data['avatar_url']}")
            print(f"Tenant: {data.get('tenant_id', 'N/A')}")

            # Check if file path is tenant-isolated
            if "test-tenant-123" in data['avatar_url']:
                print("✅ Tenant isolation verified in path!")
            else:
                print("⚠️  Warning: Path may not be tenant-isolated")

if __name__ == "__main__":
    asyncio.run(test_avatar_upload())
