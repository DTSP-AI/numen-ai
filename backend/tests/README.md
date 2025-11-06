# HypnoAgent Test & Diagnostic Suite

Comprehensive testing and diagnostic tools for the HypnoAgent application.

## Overview

This test suite provides:

- **E2E Flow Diagnostic**: Complete user journey testing (intake → guide creation → chat)
- **Quick Diagnostic**: Rapid health checks and basic flow validation
- **Test Utilities**: Reusable test helpers, data generators, and assertion tools

## Quick Start

### Prerequisites

1. Backend server running on port 8003 (or specify with `--url`)
2. All required environment variables set in `.env`
3. Supabase database configured and accessible
4. Required API keys (OpenAI, optionally ElevenLabs, Deepgram, LiveKit)

### Installation

```bash
cd backend
pip install httpx pytest pytest-asyncio
```

## Running Diagnostics

### 1. Quick Diagnostic (Recommended for Development)

Fast health check and basic flow validation:

```bash
# Full quick diagnostic (health + flow test)
python -m tests.quick_diagnostic

# Health check only
python -m tests.quick_diagnostic --health-only

# Stress test (10 requests)
python -m tests.quick_diagnostic --stress-test 10

# Custom backend URL
python -m tests.quick_diagnostic --url http://localhost:8000
```

**Output:**
- Service health status
- Basic intake/guide/chat flow
- Response times
- Success/failure indicators

**When to use:**
- Before starting development session
- After making changes to verify nothing broke
- Quick verification during development
- CI/CD pre-deployment checks

### 2. E2E Flow Diagnostic (Comprehensive)

Complete end-to-end testing of all user flows:

```bash
# Run full E2E test suite
python -m tests.e2e_flow_diagnostic

# Keep test data (don't cleanup)
python -m tests.e2e_flow_diagnostic --no-cleanup

# Custom backend URL
python -m tests.e2e_flow_diagnostic --url http://localhost:8000
```

**Tests Performed:**
1. **Health Check** - Verify all services operational
2. **Intake Flow** - Create intake session with user data
3. **Guide Creation** - Generate personalized guide with avatar/voice
4. **Chat Interaction** - Test conversation and response generation
5. **Dashboard Verification** - Verify guide appears in dashboard

**When to use:**
- Before major releases
- After significant changes
- Pre-production validation
- Weekly regression testing

## Test Structure

```
backend/tests/
├── __init__.py                    # Package initialization
├── e2e_flow_diagnostic.py        # Comprehensive E2E test suite
├── quick_diagnostic.py           # Quick health + flow validation
├── test_utils.py                 # Shared utilities and helpers
└── README.md                     # This file
```

## Test Utilities

### TestDataGenerator

Generate realistic test data:

```python
from tests.test_utils import TestDataGenerator

# Generate user ID
user_id = TestDataGenerator.generate_user_id("test-user")

# Generate intake data
intake_data = TestDataGenerator.generate_intake_data(
    name="John Doe",
    age=35,
    goals="Overcome anxiety"
)

# Generate guide data
guide_data = TestDataGenerator.generate_guide_data(
    persona_type="Marcus Aurelius",
    voice_id="alloy"
)

# Get test chat messages
messages = TestDataGenerator.generate_chat_messages()
```

### APITestClient

Enhanced HTTP client with user context:

```python
from tests.test_utils import APITestClient

client = APITestClient("http://localhost:8003")
client.set_user_id("test-user-123")

# Requests automatically include X-User-ID header
response = await client.get("/api/dashboard")
response = await client.post("/api/agents/create", json=guide_data)

await client.close()
```

### TestTimer

Measure test performance:

```python
from tests.test_utils import TestTimer

# Context manager
with TestTimer() as timer:
    response = await client.get("/health")
print(f"Request took {timer.elapsed_ms()}ms")

# Manual control
timer = TestTimer()
timer.start()
# ... do work ...
timer.stop()
print(f"Elapsed: {timer.elapsed_seconds()}s")
```

### AssertionHelper

Common test assertions:

```python
from tests.test_utils import AssertionHelper

# Assert response OK (2xx)
AssertionHelper.assert_response_ok(response, "Health check failed")

# Assert required fields present
AssertionHelper.assert_has_fields(data, ["id", "name", "status"])

# Assert not empty
AssertionHelper.assert_not_empty(guide_list, "No guides found")

# Assert type
AssertionHelper.assert_type(response_data, dict, "Invalid response type")
```

## Writing Custom Tests

### Example: Custom E2E Test

```python
import asyncio
from tests.test_utils import (
    APITestClient,
    TestDataGenerator,
    TestTimer,
    Colors
)

async def test_custom_flow():
    client = APITestClient()

    # Setup
    user_id = TestDataGenerator.generate_user_id()
    client.set_user_id(user_id)

    try:
        # Test intake
        print(f"{Colors.OKCYAN}Testing intake...{Colors.ENDC}")
        intake_data = TestDataGenerator.generate_intake_data()

        with TestTimer() as timer:
            response = await client.post("/api/intake/start", json=intake_data)

        if response.status_code == 200:
            print(f"{Colors.OKGREEN}✓ Intake OK ({timer.elapsed_ms()}ms){Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Intake failed{Colors.ENDC}")
            return False

        # More tests...

        return True

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_custom_flow())
```

## Interpreting Results

### Health Check Status

- **✓ HEALTHY** - All required services operational
- **⚠ DEGRADED** - Required services OK, optional services missing
- **✗ FAILED** - Required services not available

### Service Status Indicators

- **connected** - Database connection established
- **configured** - API key present and valid
- **not_configured** - Optional service not configured
- **missing** - Required configuration missing
- **error** - Service check failed

### Test Results

- **[OK] Green** - Test passed
- **[FAIL] Red** - Test failed (critical issue)
- **[WARN] Yellow** - Warning (non-critical issue)
- **[INFO] Blue** - Information

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

Use in CI/CD:
```bash
python -m tests.quick_diagnostic
if [ $? -eq 0 ]; then
    echo "Tests passed, proceeding with deployment"
else
    echo "Tests failed, blocking deployment"
    exit 1
fi
```

## Troubleshooting

### "Backend is not responding"

**Solution:**
1. Verify backend is running: `netstat -ano | findstr :8003`
2. Check backend logs for errors
3. Verify `.env` file is present with required keys

### "Database connection failed"

**Solution:**
1. Check `SUPABASE_DB_URL` in `.env`
2. Verify Supabase project is running
3. Check network connectivity
4. Review database logs in Supabase dashboard

### "OpenAI API key missing"

**Solution:**
1. Set `OPENAI_API_KEY` in `.env`
2. Verify key is valid
3. Check API quota/limits

### "Test data not cleaning up"

**Solution:**
- Use `--no-cleanup` flag to inspect test data
- Manually delete test guides from dashboard
- Check database for orphaned records with `test-user-*` prefix

### "Timeout errors"

**Solution:**
1. Increase timeout: Edit `APITestClient(timeout=120.0)`
2. Check for slow OpenAI API responses
3. Verify network latency
4. Check if backend is under heavy load

## Best Practices

1. **Run quick diagnostic frequently** - Before and after changes
2. **Run E2E diagnostic before releases** - Full validation
3. **Keep test data clean** - Always cleanup unless debugging
4. **Monitor response times** - Use timers to track performance
5. **Check all service statuses** - Don't ignore warnings
6. **Use realistic test data** - Use TestDataGenerator for consistency

## CI/CD Integration

### GitHub Actions Example

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install httpx pytest pytest-asyncio

      - name: Start backend
        run: |
          cd backend
          python main.py &
          sleep 10
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}

      - name: Run quick diagnostic
        run: |
          cd backend
          python -m tests.quick_diagnostic

      - name: Run E2E tests
        run: |
          cd backend
          python -m tests.e2e_flow_diagnostic
```

## Future Enhancements

Planned improvements:

- [ ] Performance benchmarking suite
- [ ] Load testing with concurrent users
- [ ] Memory leak detection
- [ ] Database migration testing
- [ ] API contract testing
- [ ] Security vulnerability scanning
- [ ] Test coverage reporting
- [ ] Automated regression detection

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review backend logs: `backend_log.txt`
3. Check Supabase dashboard for database issues
4. Review `.env` configuration

## License

Part of the HypnoAgent application.
