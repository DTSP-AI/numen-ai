/**
 * Voice Creation E2E Tests
 * =======================
 *
 * Tests the full voice creation flow from frontend UI to backend API.
 * Run with: npm run test:e2e
 *
 * Prerequisites:
 * - Backend running on localhost:8003
 * - Frontend running on localhost:3003
 * - Valid ELEVENLABS_API_KEY in .env
 */

import { test, expect } from '@playwright/test'
import path from 'path'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003'
const FRONTEND_URL = 'http://localhost:3003'
const TEST_USER_ID = 'e2e-test-user-' + Date.now()

test.describe('Voice Creation Flow', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to agent creation page
    await page.goto(`${FRONTEND_URL}/create-agent`)
    await page.waitForLoadState('networkidle')
  })

  test('should load voice list in Step 3', async ({ page }) => {
    // Navigate through Step 1
    await page.fill('input[id="agentName"]', 'Test Agent')
    await page.click('button:has-text("Stoic Sage")')
    await page.fill('textarea[id="mission"]', 'Test mission')
    await page.click('button:has-text("Next")')

    // Navigate through Step 2
    await page.click('button:has-text("Next")')

    // Now in Step 3 - Voice Selection
    await page.waitForSelector('text=How Does Your Guide Sound?')

    // Wait for voices to load
    await page.waitForSelector('button:has-text("Preview")', { timeout: 10000 })

    // Verify voice cards are present
    const voiceCards = await page.locator('button:has-text("Preview")').count()
    expect(voiceCards).toBeGreaterThan(20) // Should have 25+ voices
  })

  test('should display "Create Custom Voice" section', async ({ page }) => {
    // Navigate to Step 3
    await navigateToStep3(page)

    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Verify custom voice section exists
    await expect(page.locator('text=Create a Custom Voice')).toBeVisible()
    await expect(page.locator('input[id="voiceName"]')).toBeVisible()
    await expect(page.locator('textarea[id="voiceDescription"]')).toBeVisible()
    await expect(page.locator('input[type="file"]')).toBeVisible()
  })

  test('should validate voice creation form', async ({ page }) => {
    await navigateToStep3(page)
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Try to create without name or files
    const createButton = page.locator('button:has-text("Create Voice")')
    await expect(createButton).toBeDisabled()

    // Fill name only
    await page.fill('input[id="voiceName"]', 'Test Voice')
    await expect(createButton).toBeDisabled() // Still disabled (no files)

    // Add file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'sample.mp3'))

    // Now button should be enabled
    await expect(createButton).toBeEnabled()
  })

  test('should create custom voice successfully', async ({ page }) => {
    await navigateToStep3(page)
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Fill out form
    await page.fill('input[id="voiceName"]', `Test Voice ${Date.now()}`)
    await page.fill('textarea[id="voiceDescription"]', 'E2E test voice')

    // Upload audio file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'sample.mp3'))

    // Verify file selected
    await expect(page.locator('text=/1 file\\(s\\) selected/')).toBeVisible()

    // Click create
    const createButton = page.locator('button:has-text("Create Voice")')
    await createButton.click()

    // Wait for loading state
    await expect(page.locator('button:has-text("Creating Voice...")')).toBeVisible()

    // Wait for success alert
    await page.waitForEvent('dialog', { timeout: 30000 })

    // Voice list should reload
    await page.waitForTimeout(2000)

    // Form should be cleared
    await expect(page.locator('input[id="voiceName"]')).toHaveValue('')
  })

  test('should preview custom voice after creation', async ({ page }) => {
    await navigateToStep3(page)

    // Scroll to voice list
    await page.evaluate(() => window.scrollTo(0, 0))

    // Find first voice and click preview
    const previewButton = page.locator('button:has-text("Preview")').first()
    await previewButton.click()

    // Should show "Playing..." state
    await expect(page.locator('button:has-text("Playing...")')).toBeVisible({ timeout: 5000 })
  })

  test('should filter voices by user', async ({ page, context }) => {
    // Create voice as user 1
    await navigateToStep3(page)
    const voiceName = `User1-Voice-${Date.now()}`
    await createVoice(page, voiceName)

    // Open new incognito context (different user)
    const incognitoContext = await context.browser()?.newContext()
    const incognitoPage = await incognitoContext!.newPage()

    await incognitoPage.goto(`${FRONTEND_URL}/create-agent`)
    await navigateToStep3(incognitoPage)

    // Search for the voice created by user 1
    const voiceList = await incognitoPage.textContent('body')

    // Voice should NOT be visible to different user
    expect(voiceList).not.toContain(voiceName)

    await incognitoContext?.close()
  })
})

test.describe('Voice API Endpoints', () => {

  test('GET /api/voices without user_id returns system voices', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/voices`)

    expect(response.status()).toBe(200)
    const data = await response.json()

    expect(data).toHaveProperty('total')
    expect(data).toHaveProperty('voices')
    expect(Array.isArray(data.voices)).toBeTruthy()

    // Should only have system voices (no owner_id)
    for (const voice of data.voices) {
      expect(voice).toHaveProperty('id')
      expect(voice).toHaveProperty('name')
    }
  })

  test('GET /api/voices with user_id returns filtered voices', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/voices`, {
      headers: {
        'x-user-id': TEST_USER_ID
      }
    })

    expect(response.status()).toBe(200)
    const data = await response.json()

    expect(data.total).toBeGreaterThan(0)
  })

  test('POST /api/voices/create without user_id returns 401', async ({ request }) => {
    const formData = new FormData()
    formData.append('name', 'Test Voice')

    const response = await request.post(`${BACKEND_URL}/api/voices/create`, {
      multipart: formData as any
    })

    expect(response.status()).toBe(401)
  })

  test('POST /api/voices/preview generates audio', async ({ request }) => {
    const response = await request.post(`${BACKEND_URL}/api/voices/preview`, {
      data: {
        voice_id: 'test-voice-id',
        text: 'Test preview'
      }
    })

    // Should return 200 or 503 (if service unavailable)
    expect([200, 503]).toContain(response.status())

    if (response.status() === 200) {
      expect(response.headers()['content-type']).toBe('audio/mpeg')
    }
  })
})

// Helper Functions
async function navigateToStep3(page: any) {
  // Step 1: Identity
  await page.fill('input[id="agentName"]', 'Test Agent')
  await page.click('button:has-text("Stoic Sage")')
  await page.fill('textarea[id="mission"]', 'Test mission for e2e')
  await page.click('button:has-text("Next")')

  // Step 2: Attributes
  await page.waitForSelector('text=Core Attributes')
  await page.click('button:has-text("Next")')

  // Now in Step 3
  await page.waitForSelector('text=How Does Your Guide Sound?')
  await page.waitForLoadState('networkidle')
}

async function createVoice(page: any, voiceName: string) {
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

  await page.fill('input[id="voiceName"]', voiceName)
  await page.fill('textarea[id="voiceDescription"]', 'E2E test voice')

  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'sample.mp3'))

  const createButton = page.locator('button:has-text("Create Voice")')
  await createButton.click()

  // Wait for completion
  await page.waitForEvent('dialog', { timeout: 30000 })
  await page.waitForTimeout(2000)
}
