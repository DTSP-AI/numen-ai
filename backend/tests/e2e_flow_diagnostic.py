"""
E2E Flow Diagnostic Tool for HypnoAgent Application

This tool tests the complete user journey:
1. Health Check - Verify all services are operational
2. Intake Flow - Create intake session and process user information
3. Guide Creation - Generate personalized guide with avatar and voice
4. Chat Interaction - Test conversation with the created guide
5. Dashboard Verification - Verify guide appears in user's dashboard

Usage:
    python -m tests.e2e_flow_diagnostic

Environment Requirements:
    - Backend server running on port 8003
    - All required API keys in .env file
    - Supabase database configured and accessible
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


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


class E2EFlowDiagnostic:
    """Comprehensive E2E flow diagnostic tool"""

    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_data = {}
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total": 0
        }

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

    def print_step(self, text: str):
        """Print test step"""
        print(f"{Colors.OKCYAN}> {text}{Colors.ENDC}")

    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")
        self.results["passed"] += 1
        self.results["total"] += 1

    def print_failure(self, text: str):
        """Print failure message"""
        print(f"{Colors.FAIL}[FAIL] {text}{Colors.ENDC}")
        self.results["failed"] += 1
        self.results["total"] += 1

    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}[WARN] {text}{Colors.ENDC}")
        self.results["warnings"] += 1

    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKBLUE}[INFO] {text}{Colors.ENDC}")

    async def test_health_check(self) -> bool:
        """Test 1: Health Check - Verify all services are operational"""
        self.print_header("TEST 1: HEALTH CHECK")

        try:
            self.print_step("Checking backend health endpoint...")
            response = await self.client.get(f"{self.base_url}/health")

            if response.status_code != 200:
                self.print_failure(f"Health check failed with status {response.status_code}")
                return False

            health_data = response.json()
            self.print_success("Backend is responding")

            # Check overall status
            if health_data.get("status") == "healthy":
                self.print_success("Overall status: HEALTHY")
            else:
                self.print_warning(f"Overall status: {health_data.get('status', 'unknown').upper()}")

            # Check individual services
            services = health_data.get("services", {})

            # Database (required)
            db_status = services.get("database", {}).get("status")
            if db_status == "connected":
                self.print_success("Database: Connected")
            else:
                self.print_failure(f"Database: {db_status}")
                return False

            # OpenAI (required)
            openai_status = services.get("openai", {}).get("status")
            if openai_status == "configured":
                self.print_success("OpenAI: Configured")
            else:
                self.print_failure("OpenAI: Not configured (REQUIRED)")
                return False

            # Optional services
            elevenlabs_status = services.get("elevenlabs", {}).get("status")
            if elevenlabs_status == "configured":
                self.print_success("ElevenLabs: Configured")
            else:
                self.print_warning("ElevenLabs: Not configured (voice synthesis disabled)")

            deepgram_status = services.get("deepgram", {}).get("status")
            if deepgram_status == "configured":
                self.print_success("Deepgram: Configured")
            else:
                self.print_warning("Deepgram: Not configured (STT disabled)")

            livekit_status = services.get("livekit", {}).get("status")
            if livekit_status == "configured":
                self.print_success("LiveKit: Configured")
            else:
                self.print_warning("LiveKit: Not configured (realtime voice disabled)")

            mem0_status = services.get("mem0", {}).get("status")
            if mem0_status in ["configured", "local_mode"]:
                self.print_success(f"Mem0: {mem0_status}")
            else:
                self.print_warning(f"Mem0: {mem0_status}")

            # Check capabilities
            capabilities = health_data.get("capabilities", {})
            self.print_info(f"Capabilities: text_chat={capabilities.get('text_chat', False)}, "
                          f"voice_synthesis={capabilities.get('voice_synthesis', False)}, "
                          f"speech_recognition={capabilities.get('speech_recognition', False)}")

            return True

        except Exception as e:
            self.print_failure(f"Health check exception: {str(e)}")
            return False

    async def test_intake_flow(self) -> bool:
        """Test 2: Intake Flow - Create intake session and process user information"""
        self.print_header("TEST 2: INTAKE FLOW")

        try:
            # Generate unique test user ID
            test_user_id = f"test-user-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.test_data["user_id"] = test_user_id

            self.print_step(f"Creating intake session for user: {test_user_id}")

            # Step 1: Start intake
            intake_data = {
                "goals": "I want to overcome anxiety and build confidence in my daily life",
                "tone": "compassionate and wise",
                "session_type": "daily"
            }

            response = await self.client.post(
                f"{self.base_url}/api/intake/process",
                json=intake_data,
                headers={"X-User-ID": test_user_id}
            )

            if response.status_code != 200:
                self.print_failure(f"Intake start failed: {response.status_code} - {response.text}")
                return False

            intake_response = response.json()
            self.print_success("Intake session created")

            # Store the intake contract for agent creation
            self.test_data["intake_contract"] = intake_response

            # Log contract details
            if "persona" in intake_response:
                self.print_info(f"Persona: {intake_response['persona']}")
            if "tone" in intake_response:
                self.print_info(f"Tone: {intake_response['tone']}")

            return True

        except Exception as e:
            self.print_failure(f"Intake flow exception: {str(e)}")
            return False

    async def test_guide_creation(self) -> bool:
        """Test 3: Guide Creation - Generate personalized guide with avatar and voice"""
        self.print_header("TEST 3: GUIDE CREATION")

        try:
            user_id = self.test_data.get("user_id")
            if not user_id:
                self.print_failure("No user_id from previous test")
                return False

            self.print_step("Creating personalized guide from intake...")

            # Get the intake contract from previous test
            intake_contract = self.test_data.get("intake_contract")

            if not intake_contract:
                # If no intake contract, create agent directly
                guide_data = {
                    "name": "Test Guide",
                    "agent_type": "guide",
                    "persona": "Marcus Aurelius",
                    "system_prompt": "You are a wise and compassionate guide focused on stoic philosophy."
                }
                response = await self.client.post(
                    f"{self.base_url}/api/agents",
                    json=guide_data,
                    headers={"X-User-ID": user_id}
                )
            else:
                # Use the proper intake-to-agent flow
                response = await self.client.post(
                    f"{self.base_url}/api/agents/from_intake_contract",
                    json=intake_contract,
                    headers={"X-User-ID": user_id}
                )

            if response.status_code not in [200, 201]:
                self.print_failure(f"Guide creation failed: {response.status_code} - {response.text}")
                return False

            guide_response = response.json()
            self.print_success("Guide created successfully")

            # Store guide ID
            if "agent_id" in guide_response:
                self.test_data["agent_id"] = guide_response["agent_id"]
                self.print_info(f"Guide ID: {self.test_data['agent_id']}")
            elif "id" in guide_response:
                self.test_data["agent_id"] = guide_response["id"]
                self.print_info(f"Guide ID: {self.test_data['agent_id']}")
            else:
                self.print_warning("No agent_id in response")

            # Check guide properties
            if "name" in guide_response:
                self.print_info(f"Guide Name: {guide_response['name']}")

            if "avatar_url" in guide_response:
                self.print_success("Avatar URL generated")
                self.print_info(f"Avatar: {guide_response['avatar_url']}")
            else:
                self.print_warning("No avatar_url in response")

            if "voice_id" in guide_response:
                self.print_info(f"Voice ID: {guide_response['voice_id']}")

            return True

        except Exception as e:
            self.print_failure(f"Guide creation exception: {str(e)}")
            return False

    async def test_chat_interaction(self) -> bool:
        """Test 4: Chat Interaction - Test conversation with the created guide"""
        self.print_header("TEST 4: CHAT INTERACTION")

        try:
            agent_id = self.test_data.get("agent_id")
            user_id = self.test_data.get("user_id")

            if not agent_id or not user_id:
                self.print_failure("Missing agent_id or user_id from previous tests")
                return False

            self.print_step(f"Starting chat with guide {agent_id}...")

            # Send a test message
            chat_data = {
                "message": "Hello, I'm feeling anxious about an upcoming presentation. Can you help me?"
            }

            response = await self.client.post(
                f"{self.base_url}/api/agents/{agent_id}/chat",
                json=chat_data,
                headers={"X-User-ID": user_id}
            )

            if response.status_code != 200:
                self.print_failure(f"Chat message failed: {response.status_code} - {response.text}")
                return False

            chat_response = response.json()
            self.print_success("Chat message processed")

            # Check response
            if "response" in chat_response:
                response_text = chat_response["response"]
                self.print_info(f"Response length: {len(response_text)} characters")

                # Show first 150 characters of response
                preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
                self.print_info(f"Response preview: {preview}")

                # Check if response is meaningful
                if len(response_text) > 50:
                    self.print_success("Response contains substantial content")
                else:
                    self.print_warning("Response is very short")
            else:
                self.print_warning("No 'response' field in chat response")

            # Check for audio if voice is enabled
            if "audio_url" in chat_response:
                self.print_success("Audio response generated")
                self.print_info(f"Audio URL: {chat_response['audio_url']}")

            # Test getting chat threads
            self.print_step("Retrieving chat threads...")

            threads_response = await self.client.get(
                f"{self.base_url}/api/agents/{agent_id}/threads",
                headers={"X-User-ID": user_id}
            )

            if threads_response.status_code == 200:
                threads = threads_response.json()
                if isinstance(threads, list) and len(threads) > 0:
                    self.print_success(f"Chat threads retrieved: {len(threads)} threads")
                else:
                    self.print_info("No chat threads yet")
            else:
                self.print_warning(f"Could not retrieve chat threads: {threads_response.status_code}")

            return True

        except Exception as e:
            self.print_failure(f"Chat interaction exception: {str(e)}")
            return False

    async def test_dashboard_verification(self) -> bool:
        """Test 5: Dashboard Verification - Verify guide appears in user's dashboard"""
        self.print_header("TEST 5: DASHBOARD VERIFICATION")

        try:
            user_id = self.test_data.get("user_id")
            agent_id = self.test_data.get("agent_id")

            if not user_id:
                self.print_failure("No user_id from previous tests")
                return False

            self.print_step("Retrieving user's dashboard...")

            response = await self.client.get(
                f"{self.base_url}/api/dashboard/user/{user_id}",
                headers={"X-User-ID": user_id}
            )

            if response.status_code != 200:
                self.print_failure(f"Dashboard retrieval failed: {response.status_code} - {response.text}")
                return False

            dashboard_data = response.json()
            self.print_success("Dashboard data retrieved")

            # Check for guides/agents
            guides = dashboard_data.get("agents", []) or dashboard_data.get("guides", [])

            if not guides:
                self.print_failure("No guides found in dashboard")
                return False

            self.print_success(f"Found {len(guides)} guide(s) in dashboard")

            # Verify our test guide is present
            if agent_id:
                found = any(g.get("id") == agent_id or g.get("agent_id") == agent_id for g in guides)
                if found:
                    self.print_success("Test guide found in dashboard")
                else:
                    self.print_warning("Test guide not found in dashboard (may still be processing)")

            # Display guide info
            for idx, guide in enumerate(guides, 1):
                guide_id = guide.get("id") or guide.get("agent_id")
                guide_name = guide.get("name", "Unnamed")
                self.print_info(f"Guide {idx}: {guide_name} (ID: {guide_id})")

            return True

        except Exception as e:
            self.print_failure(f"Dashboard verification exception: {str(e)}")
            return False

    async def cleanup(self):
        """Cleanup resources and test data"""
        self.print_header("CLEANUP")

        user_id = self.test_data.get("user_id")
        agent_id = self.test_data.get("agent_id")

        if agent_id and user_id:
            try:
                self.print_step(f"Attempting to delete test guide {agent_id}...")
                response = await self.client.delete(
                    f"{self.base_url}/api/agents/{agent_id}",
                    headers={"X-User-ID": user_id}
                )
                if response.status_code == 200:
                    self.print_success("Test guide deleted")
                else:
                    self.print_warning(f"Could not delete test guide: {response.status_code}")
            except Exception as e:
                self.print_warning(f"Cleanup exception: {str(e)}")

        await self.client.aclose()
        self.print_info("Client connection closed")

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        warnings = self.results["warnings"]

        print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        print(f"  {Colors.OKGREEN}Passed:   {passed}/{total}{Colors.ENDC}")
        print(f"  {Colors.FAIL}Failed:   {failed}/{total}{Colors.ENDC}")
        print(f"  {Colors.WARNING}Warnings: {warnings}{Colors.ENDC}")

        if failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCESS] ALL TESTS PASSED{Colors.ENDC}")
            return True
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}[FAILURE] SOME TESTS FAILED{Colors.ENDC}")
            return False

    async def run_all_tests(self, cleanup_on_complete: bool = True):
        """Run all E2E tests in sequence"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("="*80)
        print("               HypnoAgent E2E Flow Diagnostic Tool                   ".center(80))
        print("          Test Suite: Complete User Journey                          ".center(80))
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        print(f"  Base URL: {self.base_url}".center(80))
        print("="*80)
        print(f"{Colors.ENDC}\n")

        try:
            # Run tests in sequence
            tests = [
                ("Health Check", self.test_health_check),
                ("Intake Flow", self.test_intake_flow),
                ("Guide Creation", self.test_guide_creation),
                ("Chat Interaction", self.test_chat_interaction),
                ("Dashboard Verification", self.test_dashboard_verification)
            ]

            for test_name, test_func in tests:
                success = await test_func()
                if not success:
                    self.print_warning(f"Test '{test_name}' failed - continuing with remaining tests...")

            # Cleanup
            if cleanup_on_complete:
                await self.cleanup()

            # Print summary
            all_passed = self.print_summary()

            return all_passed

        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
            await self.cleanup()
            return False
        except Exception as e:
            print(f"\n{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}")
            await self.cleanup()
            return False


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="HypnoAgent E2E Flow Diagnostic Tool")
    parser.add_argument("--url", default="http://localhost:8003", help="Backend URL (default: http://localhost:8003)")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip cleanup of test data")

    args = parser.parse_args()

    diagnostic = E2EFlowDiagnostic(base_url=args.url)
    success = await diagnostic.run_all_tests(cleanup_on_complete=not args.no_cleanup)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
