"""
Contract Validator - Filesystem-Database Sync Validation

Ensures agent contracts in database match filesystem storage
to maintain single source of truth integrity.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.agent import AgentContract
from database import get_pg_pool

logger = logging.getLogger(__name__)


class ContractSyncValidationError(Exception):
    """Raised when database and filesystem contracts diverge"""
    pass


class ContractValidator:
    """Validates contract synchronization between database and filesystem"""

    def __init__(self):
        self.contracts_dir = Path("backend/prompts")

    async def validate_agent_contract(
        self,
        agent_id: str,
        auto_repair: bool = False
    ) -> Dict[str, Any]:
        """
        Validate that database contract matches filesystem contract

        Args:
            agent_id: Agent UUID
            auto_repair: If True, repair filesystem from database

        Returns:
            Dict with validation results

        Raises:
            ContractSyncValidationError: If validation fails and auto_repair=False
        """
        pool = get_pg_pool()

        try:
            # 1. Load contract from database
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT contract FROM agents WHERE id = $1::uuid
                """, agent_id)

                if not row:
                    return {
                        "valid": False,
                        "error": f"Agent {agent_id} not found in database"
                    }

                db_contract = row["contract"]

            # 2. Load contract from filesystem
            contract_path = self.contracts_dir / agent_id / "agent_contract.json"

            if not contract_path.exists():
                logger.warning(f"Filesystem contract missing for {agent_id}")

                if auto_repair:
                    logger.info(f"Auto-repairing: Creating filesystem contract from database")
                    await self._write_filesystem_contract(agent_id, db_contract)
                    return {
                        "valid": True,
                        "repaired": True,
                        "action": "created_filesystem_contract"
                    }
                else:
                    raise ContractSyncValidationError(
                        f"Filesystem contract missing for agent {agent_id}"
                    )

            with open(contract_path, 'r', encoding='utf-8') as f:
                fs_contract = json.load(f)

            # 3. Compare contracts
            differences = self._find_differences(db_contract, fs_contract)

            if differences:
                logger.warning(f"Contract mismatch for {agent_id}: {len(differences)} differences")

                if auto_repair:
                    logger.info(f"Auto-repairing: Overwriting filesystem from database")
                    await self._write_filesystem_contract(agent_id, db_contract)
                    return {
                        "valid": True,
                        "repaired": True,
                        "differences": differences,
                        "action": "overwrote_filesystem_from_database"
                    }
                else:
                    raise ContractSyncValidationError(
                        f"Contract mismatch for agent {agent_id}: {differences}"
                    )

            # 4. Validation passed
            return {
                "valid": True,
                "agent_id": agent_id,
                "db_version": db_contract.get("version"),
                "fs_version": fs_contract.get("version"),
                "checked_at": datetime.utcnow().isoformat()
            }

        except ContractSyncValidationError:
            raise
        except Exception as e:
            logger.error(f"Contract validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }

    async def validate_all_agents(
        self,
        tenant_id: Optional[str] = None,
        auto_repair: bool = False
    ) -> Dict[str, Any]:
        """
        Validate all agents in database against filesystem

        Args:
            tenant_id: Optional tenant filter
            auto_repair: If True, repair mismatches

        Returns:
            Summary of validation results
        """
        pool = get_pg_pool()

        try:
            # Get all agents
            query = "SELECT id, name FROM agents WHERE status != 'archived'"
            params = []

            if tenant_id:
                query += " AND tenant_id = $1::uuid"
                params.append(tenant_id)

            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

            total = len(rows)
            valid = 0
            repaired = 0
            failed = []

            # Validate each agent
            for row in rows:
                agent_id = str(row["id"])
                agent_name = row["name"]

                try:
                    result = await self.validate_agent_contract(agent_id, auto_repair)

                    if result.get("valid"):
                        valid += 1
                        if result.get("repaired"):
                            repaired += 1
                    else:
                        failed.append({
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "error": result.get("error")
                        })

                except Exception as e:
                    logger.error(f"Validation failed for {agent_name} ({agent_id}): {e}")
                    failed.append({
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "error": str(e)
                    })

            return {
                "total_agents": total,
                "valid": valid,
                "repaired": repaired,
                "failed": len(failed),
                "failed_agents": failed,
                "checked_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Bulk validation failed: {e}")
            return {
                "error": str(e)
            }

    def _find_differences(
        self,
        db_contract: Dict[str, Any],
        fs_contract: Dict[str, Any],
        path: str = ""
    ) -> List[str]:
        """Recursively find differences between two contracts"""
        differences = []

        # Compare keys
        db_keys = set(db_contract.keys())
        fs_keys = set(fs_contract.keys())

        # Missing keys
        for key in db_keys - fs_keys:
            differences.append(f"{path}.{key} missing in filesystem")

        for key in fs_keys - db_keys:
            differences.append(f"{path}.{key} missing in database")

        # Compare values for common keys
        for key in db_keys & fs_keys:
            db_value = db_contract[key]
            fs_value = fs_contract[key]

            current_path = f"{path}.{key}" if path else key

            if isinstance(db_value, dict) and isinstance(fs_value, dict):
                # Recurse into nested dicts
                nested_diffs = self._find_differences(db_value, fs_value, current_path)
                differences.extend(nested_diffs)

            elif db_value != fs_value:
                # Skip timestamp comparisons (these can naturally differ)
                if key not in ["updated_at", "created_at"]:
                    differences.append(
                        f"{current_path}: DB={db_value} vs FS={fs_value}"
                    )

        return differences

    async def _write_filesystem_contract(
        self,
        agent_id: str,
        contract: Dict[str, Any]
    ):
        """Write contract to filesystem (repair operation)"""
        from services.agent_service import AgentService

        # Use agent service method to ensure consistency
        service = AgentService()

        # Create agent directory
        agent_dir = self.contracts_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Save contract
        contract_path = agent_dir / "agent_contract.json"
        with open(contract_path, 'w', encoding='utf-8') as f:
            json.dump(contract, f, indent=2, default=str)

        # Regenerate system prompt from contract
        from models.agent import AgentContract
        agent_contract = AgentContract(**contract)

        system_prompt = service._generate_system_prompt(agent_contract)
        prompt_path = agent_dir / "system_prompt.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(system_prompt)

        logger.info(f"✅ Filesystem contract repaired for {agent_id}")

    async def get_contract_hash(self, agent_id: str) -> Optional[str]:
        """
        Generate hash of contract for quick comparison

        Args:
            agent_id: Agent UUID

        Returns:
            SHA256 hash of contract JSON
        """
        import hashlib

        pool = get_pg_pool()

        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT contract FROM agents WHERE id = $1::uuid
                """, agent_id)

                if not row:
                    return None

                contract_json = json.dumps(row["contract"], sort_keys=True, default=str)
                return hashlib.sha256(contract_json.encode()).hexdigest()

        except Exception as e:
            logger.error(f"Failed to generate contract hash: {e}")
            return None


# Singleton instance
validator = ContractValidator()


async def validate_agent_sync(agent_id: str, auto_repair: bool = False) -> Dict[str, Any]:
    """
    Convenience function to validate agent contract sync

    Args:
        agent_id: Agent UUID
        auto_repair: If True, repair mismatches automatically

    Returns:
        Validation results
    """
    return await validator.validate_agent_contract(agent_id, auto_repair)


async def validate_all_agents_sync(tenant_id: Optional[str] = None, auto_repair: bool = False) -> Dict[str, Any]:
    """
    Convenience function to validate all agents

    Args:
        tenant_id: Optional tenant filter
        auto_repair: If True, repair mismatches

    Returns:
        Validation summary
    """
    return await validator.validate_all_agents(tenant_id, auto_repair)
