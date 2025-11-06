/**
 * Avatar URL Resolution Utility
 *
 * Handles resolution of avatar URLs from both Supabase Storage and local filesystem
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003'

/**
 * Resolve avatar URL to absolute URL
 *
 * @param avatarUrl - Avatar URL from backend (can be relative or absolute)
 * @returns Resolved absolute URL or null if no avatar
 *
 * @example
 * resolveAvatarUrl('/avatars/tenant-id/avatar.png')
 * // => 'http://localhost:8003/avatars/tenant-id/avatar.png'
 *
 * resolveAvatarUrl('https://supabase.co/storage/avatars/avatar.png')
 * // => 'https://supabase.co/storage/avatars/avatar.png'
 */
export function resolveAvatarUrl(avatarUrl: string | null | undefined): string | null {
  if (!avatarUrl) return null

  // If already absolute URL (http/https), return as-is
  if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
    return avatarUrl
  }

  // If relative URL, prepend API base URL
  if (avatarUrl.startsWith('/')) {
    return `${API_BASE_URL}${avatarUrl}`
  }

  // Return as-is if unclear format
  return avatarUrl
}

/**
 * Get fallback avatar URL
 *
 * @param seed - Seed for generating consistent avatar (e.g., agent ID or name)
 * @returns DiceBear avatar URL
 */
export function getFallbackAvatarUrl(seed: string): string {
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(seed)}`
}
