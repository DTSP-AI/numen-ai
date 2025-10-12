-- ===================================================================
-- Supabase Storage RLS Policies for Avatar Bucket
-- ===================================================================
--
-- This SQL should be run in your Supabase SQL Editor to enable
-- Row Level Security (RLS) for the avatars bucket.
--
-- Purpose: Enforce tenant isolation at the database level
-- ===================================================================

-- 1. Enable RLS on the storage.objects table
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 2. Policy: Allow users to upload avatars to their own tenant directory
CREATE POLICY "Users can upload to their tenant directory"
ON storage.objects
FOR INSERT
WITH CHECK (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.jwt() ->> 'tenant_id'
);

-- 3. Policy: Allow users to read avatars from their own tenant
CREATE POLICY "Users can read from their tenant directory"
ON storage.objects
FOR SELECT
USING (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.jwt() ->> 'tenant_id'
);

-- 4. Policy: Allow users to delete avatars from their own tenant
CREATE POLICY "Users can delete from their tenant directory"
ON storage.objects
FOR DELETE
USING (
  bucket_id = 'avatars'
  AND (storage.foldername(name))[1] = auth.jwt() ->> 'tenant_id'
);

-- 5. Policy: Allow public read access (for avatar display)
--    Note: This is for PUBLIC avatars. Remove if you want private-only.
CREATE POLICY "Public avatars are publicly readable"
ON storage.objects
FOR SELECT
USING (
  bucket_id = 'avatars'
);

-- ===================================================================
-- Verification Queries
-- ===================================================================

-- Check policies are applied
SELECT * FROM pg_policies WHERE tablename = 'objects';

-- Check bucket configuration
SELECT * FROM storage.buckets WHERE name = 'avatars';

-- ===================================================================
-- Alternative: Service Role Access (for backend API)
-- ===================================================================
--
-- Since our backend uses the service_role key (not user JWT),
-- we don't need these RLS policies for the API.
--
-- Instead, we enforce tenant isolation in application code.
-- RLS policies are extra security if you add direct client uploads.
-- ===================================================================
