"use client"

import { useState, useRef, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

export default function VoiceLabPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const userId = searchParams.get("userId") || "00000000-0000-0000-0000-000000000001"

  // Recording state
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [recordedChunks, setRecordedChunks] = useState<Blob[]>([])
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Upload state
  const [voiceFiles, setVoiceFiles] = useState<FileList | null>(null)
  const [voiceName, setVoiceName] = useState("")
  const [voiceDescription, setVoiceDescription] = useState("")
  const [isCreatingVoice, setIsCreatingVoice] = useState(false)
  const [creationStatus, setCreationStatus] = useState<string>("")

  // Synthesis state
  const [synthesisText, setSynthesisText] = useState("Hello, this is a test of your custom voice.")
  const [isSynthesizing, setIsSynthesizing] = useState(false)
  const [synthesizedAudioUrl, setSynthesizedAudioUrl] = useState<string | null>(null)
  const [createdVoiceId, setCreatedVoiceId] = useState<string | null>(null)

  // Cleanup audio URLs on unmount
  useEffect(() => {
    return () => {
      if (recordedAudioUrl) URL.revokeObjectURL(recordedAudioUrl)
      if (synthesizedAudioUrl) URL.revokeObjectURL(synthesizedAudioUrl)
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current)
      stopRecordingCleanup()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Stop recording cleanup
  const stopRecordingCleanup = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current)
      timerIntervalRef.current = null
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/ogg"
      })
      mediaRecorderRef.current = mediaRecorder

      const chunks: Blob[] = []
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" })
        const url = URL.createObjectURL(blob)
        setRecordedAudioUrl(url)
        setRecordedChunks([blob])
        stopRecordingCleanup()
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      // Start timer
      timerIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

    } catch (err) {
      console.error("Failed to start recording:", err)
      setCreationStatus("Microphone access denied or unavailable")
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current)
        timerIntervalRef.current = null
      }
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleCreateVoice = async () => {
    // Validate inputs
    if (!voiceName.trim()) {
      setCreationStatus("Please provide a voice name")
      return
    }

    // Must have either recorded audio or uploaded files
    const hasRecording = recordedChunks.length > 0
    const hasUploads = voiceFiles && voiceFiles.length > 0

    if (!hasRecording && !hasUploads) {
      setCreationStatus("Please record audio or upload voice samples")
      return
    }

    setIsCreatingVoice(true)
    setCreationStatus("Creating voice...")

    try {
      const formData = new FormData()
      formData.append("name", voiceName)
      formData.append("description", voiceDescription)

      // Add recorded audio if available
      if (hasRecording) {
        const recordedFile = new File(recordedChunks, "recorded-sample.webm", {
          type: "audio/webm"
        })
        formData.append("files", recordedFile)
      }

      // Add uploaded files if available
      if (hasUploads) {
        Array.from(voiceFiles).forEach(file => {
          formData.append("files", file)
        })
      }

      const response = await fetch("http://localhost:8003/api/voices/create", {
        method: "POST",
        headers: {
          "x-user-id": userId
        },
        body: formData
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Voice creation failed:", errorText)
        setCreationStatus(`Voice creation failed: ${response.status}`)
        return
      }

      const data = await response.json()
      if (data.status === "success") {
        setCreationStatus(`Voice "${data.voice.name}" created successfully`)
        setCreatedVoiceId(data.voice.voice_id)

        // Clear form
        setVoiceName("")
        setVoiceDescription("")
        setVoiceFiles(null)
        setRecordedChunks([])
        if (recordedAudioUrl) {
          URL.revokeObjectURL(recordedAudioUrl)
          setRecordedAudioUrl(null)
        }
      } else {
        setCreationStatus("Voice creation failed. Please try again.")
      }
    } catch (err) {
      console.error("Voice creation error:", err)
      setCreationStatus("Error creating voice. Please check your network connection.")
    } finally {
      setIsCreatingVoice(false)
    }
  }

  const handleSynthesizeVoice = async () => {
    if (!createdVoiceId) {
      setCreationStatus("Please create a voice first before synthesizing")
      return
    }

    if (!synthesisText.trim()) {
      setCreationStatus("Please enter text to synthesize")
      return
    }

    setIsSynthesizing(true)
    try {
      const response = await fetch("http://localhost:8003/api/voices/preview", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          voice_id: createdVoiceId,
          text: synthesisText
        })
      })

      if (response.ok) {
        const audioBlob = await response.blob()
        const url = URL.createObjectURL(audioBlob)

        // Revoke old URL if exists
        if (synthesizedAudioUrl) {
          URL.revokeObjectURL(synthesizedAudioUrl)
        }

        setSynthesizedAudioUrl(url)

        // Auto-play
        const audio = new Audio(url)
        audio.play().catch(err => console.error("Playback failed:", err))
      } else {
        setCreationStatus("Synthesis failed. Please try again.")
      }
    } catch (err) {
      console.error("Synthesis error:", err)
      setCreationStatus("Error synthesizing voice. Please check your network connection.")
    } finally {
      setIsSynthesizing(false)
    }
  }

  const handleReturnToAgentBuilder = () => {
    router.push(`/create-agent?voiceCreated=true&userId=${userId}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-kurzgesagt-navy via-kurzgesagt-purple to-kurzgesagt-pink p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <h1 className="text-5xl font-bold text-white mb-3">Voice Lab</h1>
          <p className="text-white/80 text-lg">Record, upload, and design your own AI voice</p>
        </motion.div>

        {/* Status Message */}
        {creationStatus && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/20 backdrop-blur-lg rounded-xl p-4 mb-6 text-white text-center border border-white/30"
          >
            {creationStatus}
          </motion.div>
        )}

        {/* Main Content Grid */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, staggerChildren: 0.1 }}
          className="grid gap-6"
        >
          {/* Recording Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20"
          >
            <h2 className="text-2xl font-bold text-white mb-2">Record Voice Sample</h2>
            <p className="text-white/70 text-sm mb-6">
              Record 10-30 seconds of clear speech in a quiet environment
            </p>

            <div className="flex gap-4 items-center mb-6">
              {!isRecording ? (
                <Button
                  onClick={startRecording}
                  disabled={isRecording}
                  className="bg-red-500 hover:bg-red-600 text-white font-bold px-8 py-3"
                >
                  Start Recording
                </Button>
              ) : (
                <Button
                  onClick={stopRecording}
                  className="bg-gray-600 hover:bg-gray-700 text-white font-bold px-8 py-3"
                >
                  Stop Recording
                </Button>
              )}

              {isRecording && (
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-white/90 font-semibold text-lg">
                    {formatTime(recordingTime)}
                  </span>
                </div>
              )}
            </div>

            {recordedAudioUrl && (
              <div className="mt-6 bg-white/5 rounded-xl p-4 border border-white/10">
                <Label className="text-white font-semibold mb-3 block">Recorded Audio</Label>
                <audio src={recordedAudioUrl} controls className="w-full" />
              </div>
            )}
          </motion.div>

          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20"
          >
            <h2 className="text-2xl font-bold text-white mb-2">Upload Voice Files</h2>
            <p className="text-white/70 text-sm mb-6">
              Upload 1-3 audio files (WAV/MP3) for better voice cloning quality
            </p>

            <div>
              <Label htmlFor="fileUpload" className="text-white font-semibold mb-2 block">Audio Files</Label>
              <Input
                id="fileUpload"
                type="file"
                accept="audio/wav,audio/mp3,audio/mpeg"
                multiple
                onChange={(e) => setVoiceFiles(e.target.files)}
                className="mt-2 text-white bg-white/5 border-white/20 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-white file:text-kurzgesagt-purple hover:file:bg-white/90"
              />
              <p className="text-white/60 text-sm mt-2">
                {voiceFiles?.length ? `${voiceFiles.length} file(s) selected` : "No files selected"}
              </p>
            </div>
          </motion.div>

          {/* Voice Creation Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20"
          >
            <h2 className="text-2xl font-bold text-white mb-6">Create Voice</h2>

            <div className="space-y-5">
              <div>
                <Label htmlFor="voiceName" className="text-white font-semibold mb-2 block">Voice Name *</Label>
                <Input
                  id="voiceName"
                  type="text"
                  placeholder="My Custom Voice"
                  value={voiceName}
                  onChange={(e) => setVoiceName(e.target.value)}
                  className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>

              <div>
                <Label htmlFor="voiceDescription" className="text-white font-semibold mb-2 block">Description (Optional)</Label>
                <Textarea
                  id="voiceDescription"
                  placeholder="Describe the voice characteristics..."
                  value={voiceDescription}
                  onChange={(e) => setVoiceDescription(e.target.value)}
                  rows={3}
                  className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                />
              </div>

              <Button
                onClick={handleCreateVoice}
                disabled={isCreatingVoice || !voiceName.trim()}
                className="w-full bg-kurzgesagt-yellow text-kurzgesagt-navy font-bold hover:bg-kurzgesagt-yellow/90 disabled:opacity-50 disabled:cursor-not-allowed py-6 text-lg"
              >
                {isCreatingVoice ? "Creating Voice..." : "Create Voice"}
              </Button>
            </div>
          </motion.div>

          {/* Synthesis Section */}
          {createdVoiceId && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20"
            >
              <h2 className="text-2xl font-bold text-white mb-2">Generate Sample</h2>
              <p className="text-white/70 text-sm mb-6">
                Test your new voice by synthesizing text
              </p>

              <div className="space-y-5">
                <div>
                  <Label htmlFor="synthesisText" className="text-white font-semibold mb-2 block">Text to Synthesize</Label>
                  <Textarea
                    id="synthesisText"
                    value={synthesisText}
                    onChange={(e) => setSynthesisText(e.target.value)}
                    rows={4}
                    className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                  />
                </div>

                <Button
                  onClick={handleSynthesizeVoice}
                  disabled={isSynthesizing}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-6 text-lg"
                >
                  {isSynthesizing ? "Synthesizing..." : "Synthesize & Play"}
                </Button>

                {synthesizedAudioUrl && (
                  <div className="mt-6 bg-white/5 rounded-xl p-4 border border-white/10">
                    <Label className="text-white font-semibold mb-3 block">Synthesized Audio</Label>
                    <audio src={synthesizedAudioUrl} controls className="w-full" />
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Navigation */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="flex justify-center mt-8"
          >
            <Button
              onClick={handleReturnToAgentBuilder}
              variant="outline"
              className="bg-white/10 hover:bg-white/20 text-white font-semibold border border-white/30 px-8 py-6 text-lg"
            >
              Back to Guide Creation
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}
