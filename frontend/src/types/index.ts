export type SessionStatus = 'pending' | 'intake' | 'therapy' | 'completed' | 'failed'

export type SessionType = 'manifestation' | 'anxiety_relief' | 'sleep_hypnosis' | 'confidence' | 'habit_change'

export type TonePreference = 'calm' | 'energetic' | 'authoritative' | 'gentle' | 'empowering'

export interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
}

export interface IntakeFormData {
  goals: string[]
  tone: TonePreference
  sessionType: SessionType
}