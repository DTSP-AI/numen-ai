"""
Quick test to verify OPENAI_API_KEY is being loaded correctly
"""
from config import settings

print("=" * 60)
print("OpenAI API Key Detection Test")
print("=" * 60)
print(f"settings.OPENAI_API_KEY: {settings.OPENAI_API_KEY[:20] if settings.OPENAI_API_KEY else 'None'}...")
print(f"settings.openai_api_key: {settings.openai_api_key[:20] if settings.openai_api_key else 'None'}...")
print(f"Key detected: {bool(settings.OPENAI_API_KEY or settings.openai_api_key)}")
print("=" * 60)

# Now test the avatar router logic
from routers.avatar import OPENAI_API_KEY, OPENAI_AVAILABLE
print(f"Avatar router OPENAI_API_KEY: {OPENAI_API_KEY[:20] if OPENAI_API_KEY else 'None'}...")
print(f"Avatar router OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")
print("=" * 60)
