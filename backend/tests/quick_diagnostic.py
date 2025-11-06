"""
Quick Diagnostic Tool

Rapid health check and basic flow validation for HypnoAgent.
Use this for quick verification during development.

Usage:
    python -m tests.quick_diagnostic
    python -m tests.quick_diagnostic --health-only
    python -m tests.quick_diagnostic --stress-test 5
"""

import asyncio
import httpx
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_utils import TestDataGenerator, APITestClient, TestTimer, Colors


class QuickDiagnostic:
    """Quick diagnostic tool for rapid testing"""

    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.client = APITestClient(base_url)

    async def health_check(self) -> bool:
        """Quick health check"""
        print(f"\n{Colors.OKCYAN}Running health check...{Colors.ENDC}")

        try:
            with TestTimer() as timer:
                response = await self.client.get("/health")

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")

                if status == "healthy":
                    print(f"{Colors.OKGREEN}[OK] Backend is HEALTHY (took {timer.elapsed_ms()}ms){Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}[WARN] Backend status: {status.upper()} (took {timer.elapsed_ms()}ms){Colors.ENDC}")

                # Show service statuses
                services = data.get("services", {})
                print(f"\n{Colors.BOLD}Service Status:{Colors.ENDC}")
                for service_name, service_data in services.items():
                    svc_status = service_data.get("status", "unknown")
                    required = service_data.get("required", False)
                    marker = "[OK]" if svc_status in ["connected", "configured"] else "[FAIL]"
                    color = Colors.OKGREEN if svc_status in ["connected", "configured"] else Colors.WARNING
                    req_label = " (REQUIRED)" if required else ""
                    print(f"  {color}{marker} {service_name}: {svc_status}{req_label}{Colors.ENDC}")

                return status == "healthy"
            else:
                print(f"{Colors.FAIL}[FAIL] Health check failed: {response.status_code}{Colors.ENDC}")
                return False

        except Exception as e:
            print(f"{Colors.FAIL}[FAIL] Health check error: {str(e)}{Colors.ENDC}")
            return False

    async def quick_flow_test(self) -> bool:
        """Quick test of intake → guide creation → chat flow"""
        print(f"\n{Colors.OKCYAN}Running quick flow test...{Colors.ENDC}")

        try:
            # Generate test data
            user_id = TestDataGenerator.generate_user_id("quick-test")
            self.client.set_user_id(user_id)

            print(f"{Colors.OKBLUE}[INFO] Test User ID: {user_id}{Colors.ENDC}")

            # Step 1: Intake
            print(f"\n{Colors.BOLD}Step 1: Creating intake...{Colors.ENDC}")
            intake_data = {
                "goals": "I want to overcome anxiety and build confidence",
                "tone": "compassionate and supportive",
                "session_type": "daily"
            }

            with TestTimer() as timer:
                response = await self.client.post("/api/intake/process", json=intake_data)

            if response.status_code == 200:
                print(f"{Colors.OKGREEN}[OK] Intake created (took {timer.elapsed_ms()}ms){Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[FAIL] Intake failed: {response.status_code}{Colors.ENDC}")
                return False

            # Step 2: Create guide from intake contract
            print(f"\n{Colors.BOLD}Step 2: Creating guide...{Colors.ENDC}")
            intake_contract = response.json()

            with TestTimer() as timer:
                response = await self.client.post("/api/agents/from_intake_contract", json=intake_contract)

            if response.status_code in [200, 201]:
                guide_response = response.json()
                agent_id = guide_response.get("agent_id") or guide_response.get("id")
                print(f"{Colors.OKGREEN}[OK] Guide created (took {timer.elapsed_ms()}ms){Colors.ENDC}")
                print(f"{Colors.OKBLUE}[INFO] Guide ID: {agent_id}{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[FAIL] Guide creation failed: {response.status_code}{Colors.ENDC}")
                return False

            # Step 3: Send chat message
            print(f"\n{Colors.BOLD}Step 3: Testing chat...{Colors.ENDC}")
            test_message = "Hello, I'm feeling anxious. Can you help me?"

            chat_data = {
                "message": test_message
            }

            with TestTimer() as timer:
                response = await self.client.post(f"/api/agents/{agent_id}/chat", json=chat_data)

            if response.status_code == 200:
                chat_response = response.json()
                response_text = chat_response.get("response", "")
                print(f"{Colors.OKGREEN}[OK] Chat response received (took {timer.elapsed_ms()}ms){Colors.ENDC}")
                print(f"{Colors.OKBLUE}[INFO] Response: {response_text[:100]}...{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[FAIL] Chat failed: {response.status_code}{Colors.ENDC}")
                return False

            # Cleanup
            print(f"\n{Colors.BOLD}Cleanup: Deleting test guide...{Colors.ENDC}")
            await self.client.delete(f"/api/agents/{agent_id}")
            print(f"{Colors.OKGREEN}[OK] Cleanup complete{Colors.ENDC}")

            return True

        except Exception as e:
            print(f"{Colors.FAIL}[FAIL] Quick flow test error: {str(e)}{Colors.ENDC}")
            return False

    async def stress_test(self, num_requests: int = 10) -> Dict[str, Any]:
        """Stress test the health endpoint"""
        print(f"\n{Colors.OKCYAN}Running stress test ({num_requests} requests)...{Colors.ENDC}")

        results = {
            "total": num_requests,
            "successful": 0,
            "failed": 0,
            "total_time_ms": 0,
            "avg_time_ms": 0,
            "min_time_ms": float('inf'),
            "max_time_ms": 0
        }

        tasks = []
        for _ in range(num_requests):
            tasks.append(self._stress_test_request())

        with TestTimer() as total_timer:
            request_times = await asyncio.gather(*tasks, return_exceptions=True)

        results["total_time_ms"] = total_timer.elapsed_ms()

        # Process results
        for time_ms in request_times:
            if isinstance(time_ms, Exception):
                results["failed"] += 1
            else:
                results["successful"] += 1
                results["min_time_ms"] = min(results["min_time_ms"], time_ms)
                results["max_time_ms"] = max(results["max_time_ms"], time_ms)

        if results["successful"] > 0:
            results["avg_time_ms"] = sum(
                t for t in request_times if not isinstance(t, Exception)
            ) / results["successful"]
        else:
            results["min_time_ms"] = 0

        # Print results
        print(f"\n{Colors.BOLD}Stress Test Results:{Colors.ENDC}")
        print(f"  Total Requests: {results['total']}")
        print(f"  {Colors.OKGREEN}Successful: {results['successful']}{Colors.ENDC}")
        print(f"  {Colors.FAIL}Failed: {results['failed']}{Colors.ENDC}")
        print(f"  Total Time: {results['total_time_ms']}ms")
        print(f"  Avg Response Time: {results['avg_time_ms']:.1f}ms")
        print(f"  Min Response Time: {results['min_time_ms']}ms")
        print(f"  Max Response Time: {results['max_time_ms']}ms")
        print(f"  Requests/sec: {(results['successful'] / (results['total_time_ms'] / 1000)):.1f}")

        return results

    async def _stress_test_request(self) -> int:
        """Single stress test request"""
        try:
            with TestTimer() as timer:
                response = await self.client.get("/health")
            if response.status_code == 200:
                return timer.elapsed_ms()
            else:
                raise Exception(f"Status {response.status_code}")
        except Exception as e:
            return e

    async def run(self, health_only: bool = False, stress_count: int = 0):
        """Run diagnostics"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("="*80)
        print("                  HypnoAgent Quick Diagnostic Tool                      ".center(80))
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        print(f"  Base URL: {self.base_url}".center(80))
        print("="*80)
        print(f"{Colors.ENDC}")

        try:
            # Always run health check
            health_ok = await self.health_check()

            if not health_ok:
                print(f"\n{Colors.FAIL}Backend is not healthy. Stopping diagnostics.{Colors.ENDC}")
                return False

            # If health-only mode, stop here
            if health_only:
                print(f"\n{Colors.OKGREEN}Health check complete.{Colors.ENDC}")
                return True

            # Run stress test if requested
            if stress_count > 0:
                await self.stress_test(stress_count)
                return True

            # Otherwise run quick flow test
            flow_ok = await self.quick_flow_test()

            if flow_ok:
                print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCESS] ALL DIAGNOSTICS PASSED{Colors.ENDC}")
                return True
            else:
                print(f"\n{Colors.FAIL}{Colors.BOLD}[FAILURE] SOME DIAGNOSTICS FAILED{Colors.ENDC}")
                return False

        finally:
            await self.client.close()


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="HypnoAgent Quick Diagnostic Tool")
    parser.add_argument("--url", default="http://localhost:8003", help="Backend URL")
    parser.add_argument("--health-only", action="store_true", help="Only run health check")
    parser.add_argument("--stress-test", type=int, metavar="N", help="Run stress test with N requests")

    args = parser.parse_args()

    diagnostic = QuickDiagnostic(base_url=args.url)
    success = await diagnostic.run(
        health_only=args.health_only,
        stress_count=args.stress_test or 0
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
