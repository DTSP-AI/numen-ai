const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Session {
  id: string
  user_id: string
  status: string
  room_name?: string
  created_at: string
  updated_at: string
}

export interface Contract {
  id: string
  session_id: string
  user_id: string
  goals: string[]
  tone: string
  voice_id: string
  session_type: string
  created_at: string
}

export const api = {
  async createSession(userId: string): Promise<Session> {
    const response = await fetch(`${API_URL}/api/sessions/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    })

    if (!response.ok) {
      throw new Error('Failed to create session')
    }

    return response.json()
  },

  async getSession(sessionId: string): Promise<Session> {
    const response = await fetch(`${API_URL}/api/sessions/${sessionId}`)

    if (!response.ok) {
      throw new Error('Failed to get session')
    }

    return response.json()
  },

  async createContract(contract: Omit<Contract, 'id' | 'created_at'>): Promise<Contract> {
    const response = await fetch(`${API_URL}/api/contracts/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(contract)
    })

    if (!response.ok) {
      throw new Error('Failed to create contract')
    }

    return response.json()
  },

  async getTranscripts(sessionId: string) {
    const response = await fetch(`${API_URL}/api/therapy/transcripts/${sessionId}`)

    if (!response.ok) {
      throw new Error('Failed to get transcripts')
    }

    return response.json()
  }
}