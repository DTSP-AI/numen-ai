"""
Avatar Migration Script - Move to Tenant-Isolated Structure

Migrates avatars from flat structure to tenant-isolated:
OLD: /avatars/file.png
NEW: /avatars/tenant_id/user_id/file.png (Supabase) or
     /avatars/tenant_id/file.png (filesystem fallback)
"""
import asyncio
import os
from pathlib import Path
import shutil
from services.supabase_storage import supabase_storage

# Default tenant/user for legacy avatars
DEFAULT_TENANT = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER = "00000000-0000-0000-0000-000000000001"


async def migrate_to_supabase():
    """Migrate local avatars to Supabase Storage"""
    avatars_dir = Path("backend/avatars")

    if not avatars_dir.exists():
        print("No avatars directory found, skipping migration")
        return

    # Find all avatar files (excluding subdirectories)
    avatar_files = [f for f in avatars_dir.glob("*") if f.is_file()]

    print(f"Found {len(avatar_files)} avatar files to migrate")

    if not supabase_storage.available:
        print("Supabase Storage not available - migrating to local tenant directories instead")
        migrate_to_local_tenant_dirs(avatar_files)
        return

    for avatar_file in avatar_files:
        try:
            print(f"Migrating: {avatar_file.name}")

            # Read file
            with open(avatar_file, "rb") as f:
                file_bytes = f.read()

            # Upload to Supabase with tenant isolation
            url = await supabase_storage.upload_avatar(
                file_bytes=file_bytes,
                filename=avatar_file.name,
                tenant_id=DEFAULT_TENANT,
                user_id=DEFAULT_USER,
                content_type=f"image/{avatar_file.suffix[1:]}"  # Remove leading dot
            )

            print(f"  ✓ Migrated to: {url}")

            # Backup original (don't delete yet)
            backup_dir = avatars_dir / "_migrated_backup"
            backup_dir.mkdir(exist_ok=True)
            shutil.move(str(avatar_file), str(backup_dir / avatar_file.name))

        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print("\n✅ Migration complete! Old files backed up to /avatars/_migrated_backup")


def migrate_to_local_tenant_dirs(avatar_files):
    """Migrate to local tenant directory structure (fallback)"""
    avatars_dir = Path("backend/avatars")
    tenant_dir = avatars_dir / DEFAULT_TENANT
    tenant_dir.mkdir(exist_ok=True)

    for avatar_file in avatar_files:
        try:
            dest = tenant_dir / avatar_file.name
            shutil.copy2(avatar_file, dest)
            print(f"  ✓ Copied to: {dest}")

            # Backup original
            backup_dir = avatars_dir / "_migrated_backup"
            backup_dir.mkdir(exist_ok=True)
            shutil.move(str(avatar_file), str(backup_dir / avatar_file.name))

        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print("\n✅ Migration complete! Old files backed up to /avatars/_migrated_backup")


if __name__ == "__main__":
    print("=" * 60)
    print("Avatar Migration Script")
    print("=" * 60)
    asyncio.run(migrate_to_supabase())
