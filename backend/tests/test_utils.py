"""
Test Utilities for HypnoAgent Diagnostics

Provides common utilities, helpers, and fixtures for testing.
"""

import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import random
import string


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestDataGenerator:
    """Generate realistic test data for various scenarios"""

    @staticmethod
    def generate_user_id(prefix: str = "test-user") -> str:
        """Generate unique test user ID"""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{prefix}-{timestamp}-{random_suffix}"

    @staticmethod
    def generate_intake_data(
        name: Optional[str] = None,
        age: Optional[int] = None,
        goals: Optional[str] = None,
        challenges: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate intake form data"""
        return {
            "name": name or f"Test User {random.randint(1000, 9999)}",
            "age": age or random.randint(25, 65),
            "goals": goals or random.choice([
                "I want to overcome anxiety and build confidence",
                "I need help with stress management and better sleep",
                "I want to develop a positive mindset and self-love",
                "I need to overcome fear and achieve my goals"
            ]),
            "challenges": challenges or random.choice([
                "Stress from work, negative self-talk, difficulty sleeping",
                "Anxiety, fear of failure, low self-esteem",
                "Depression, lack of motivation, feeling stuck",
                "Overwhelm, burnout, difficulty focusing"
            ]),
            "preferred_voice": random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"]),
            "session_frequency": random.choice(["daily", "weekly", "as_needed"])
        }

    @staticmethod
    def generate_guide_data(
        persona_type: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate guide creation data"""
        return {
            "persona_type": persona_type or random.choice([
                "Marcus Aurelius",
                "Deepak Chopra",
                "Carl Jung",
                "Buddha",
                "Rumi"
            ]),
            "voice_id": voice_id or random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"]),
            "custom_instructions": "Focus on practical wisdom and compassionate guidance"
        }

    @staticmethod
    def generate_chat_messages() -> List[str]:
        """Generate realistic chat messages for testing"""
        return [
            "Hello, I'm feeling anxious about an upcoming presentation. Can you help me?",
            "I've been having trouble sleeping lately. What should I do?",
            "Can you guide me through a quick meditation?",
            "I'm struggling with negative self-talk. How can I change this pattern?",
            "What affirmations would you recommend for building confidence?",
            "I feel overwhelmed by my responsibilities. Help me prioritize.",
            "Can you help me set intentions for the day?",
            "I'm facing a difficult decision. Can you guide me?"
        ]


class APITestClient:
    """Enhanced HTTP client for API testing"""

    def __init__(self, base_url: str = "http://localhost:8003", timeout: float = 60.0):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
        self.default_headers = {}

    def set_user_id(self, user_id: str):
        """Set default user ID for requests"""
        self.default_headers["X-User-ID"] = user_id

    async def get(self, path: str, headers: Optional[Dict] = None, **kwargs) -> httpx.Response:
        """GET request with default headers"""
        merged_headers = {**self.default_headers, **(headers or {})}
        return await self.client.get(f"{self.base_url}{path}", headers=merged_headers, **kwargs)

    async def post(self, path: str, headers: Optional[Dict] = None, **kwargs) -> httpx.Response:
        """POST request with default headers"""
        merged_headers = {**self.default_headers, **(headers or {})}
        return await self.client.post(f"{self.base_url}{path}", headers=merged_headers, **kwargs)

    async def put(self, path: str, headers: Optional[Dict] = None, **kwargs) -> httpx.Response:
        """PUT request with default headers"""
        merged_headers = {**self.default_headers, **(headers or {})}
        return await self.client.put(f"{self.base_url}{path}", headers=merged_headers, **kwargs)

    async def delete(self, path: str, headers: Optional[Dict] = None, **kwargs) -> httpx.Response:
        """DELETE request with default headers"""
        merged_headers = {**self.default_headers, **(headers or {})}
        return await self.client.delete(f"{self.base_url}{path}", headers=merged_headers, **kwargs)

    async def close(self):
        """Close client connection"""
        await self.client.aclose()


class TestTimer:
    """Simple timer for measuring test performance"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start timer"""
        self.start_time = datetime.now()
        return self

    def stop(self):
        """Stop timer"""
        self.end_time = datetime.now()
        return self

    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds"""
        return int(self.elapsed_seconds() * 1000)

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.stop()


class AssertionHelper:
    """Helper for common test assertions"""

    @staticmethod
    def assert_response_ok(response: httpx.Response, message: str = "Request failed"):
        """Assert response status is 2xx"""
        if not (200 <= response.status_code < 300):
            raise AssertionError(
                f"{message}: Status {response.status_code}\n"
                f"Response: {response.text[:500]}"
            )

    @staticmethod
    def assert_has_fields(data: Dict, required_fields: List[str], message: str = "Missing fields"):
        """Assert dictionary has required fields"""
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise AssertionError(f"{message}: {', '.join(missing)}")

    @staticmethod
    def assert_not_empty(value: Any, message: str = "Value is empty"):
        """Assert value is not empty"""
        if not value:
            raise AssertionError(message)

    @staticmethod
    def assert_type(value: Any, expected_type: type, message: str = "Type mismatch"):
        """Assert value is of expected type"""
        if not isinstance(value, expected_type):
            raise AssertionError(
                f"{message}: Expected {expected_type.__name__}, got {type(value).__name__}"
            )


def print_test_separator(char: str = "=", length: int = 80):
    """Print a separator line"""
    print(char * length)


def print_test_section(title: str, width: int = 80):
    """Print a formatted test section header"""
    print("\n")
    print("=" * width)
    print(title.center(width))
    print("=" * width)
    print()


async def wait_for_condition(
    condition_func,
    timeout_seconds: float = 30.0,
    check_interval: float = 1.0,
    timeout_message: str = "Condition timeout"
):
    """Wait for a condition to become true"""
    start_time = datetime.now()

    while True:
        if await condition_func():
            return True

        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed >= timeout_seconds:
            raise TimeoutError(f"{timeout_message} (waited {elapsed:.1f}s)")

        await asyncio.sleep(check_interval)


def format_json(data: Any, indent: int = 2) -> str:
    """Format data as pretty JSON"""
    import json
    return json.dumps(data, indent=indent, default=str)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
