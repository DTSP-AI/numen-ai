"use client"

import { motion } from "framer-motion"

interface ScheduledSession {
  id: string
  scheduled_at: string
  recurrence: string | null
  notification_sent: boolean
}

interface Props {
  schedule: ScheduledSession[]
}

export function ScheduleCalendar({ schedule }: Props) {
  const groupedSchedule = schedule.reduce((acc, session) => {
    const date = new Date(session.scheduled_at).toLocaleDateString()
    if (!acc[date]) acc[date] = []
    acc[date].push(session)
    return acc
  }, {} as Record<string, ScheduledSession[]>)

  return (
    <div className="space-y-6">
      {/* Add New Session Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full px-6 py-4 rounded-2xl bg-gradient-to-r from-kurzgesagt-purple to-kurzgesagt-coral text-white font-bold text-lg hover:opacity-90 transition-all"
      >
        + Schedule New Session
      </motion.button>

      {/* Upcoming Sessions */}
      <div className="glass-card rounded-2xl p-6">
        <h3 className="text-2xl font-bold text-white mb-6">Upcoming Sessions</h3>

        {Object.keys(groupedSchedule).length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📅</div>
            <p className="text-white/60 text-lg">No scheduled sessions yet</p>
            <p className="text-white/40 text-sm mt-2">Create your first schedule to get daily reminders</p>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedSchedule).map(([date, sessions]) => (
              <div key={date} className="bg-white/5 rounded-xl p-4">
                <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <span>📅</span>
                  <span>{date}</span>
                </h4>

                <div className="space-y-2">
                  {sessions.map((session) => (
                    <motion.div
                      key={session.id}
                      whileHover={{ x: 4 }}
                      className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-all"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">⏰</div>
                        <div>
                          <div className="text-white font-medium">
                            {new Date(session.scheduled_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </div>
                          {session.recurrence && (
                            <div className="text-white/60 text-sm">
                              {session.recurrence.includes("DAILY")
                                ? "Daily"
                                : session.recurrence.includes("WEEKLY")
                                ? "Weekly"
                                : "Repeating"}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {session.notification_sent && (
                          <span className="text-kurzgesagt-aqua text-sm">✓ Notified</span>
                        )}
                        <button className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm transition-all">
                          Edit
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Schedule Types */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="glass-card rounded-xl p-4 cursor-pointer"
        >
          <div className="text-3xl mb-2">🌅</div>
          <div className="text-white font-semibold mb-1">Morning Routine</div>
          <div className="text-white/60 text-sm">Start your day with affirmations</div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.05 }}
          className="glass-card rounded-xl p-4 cursor-pointer"
        >
          <div className="text-3xl mb-2">🌙</div>
          <div className="text-white font-semibold mb-1">Evening Reflection</div>
          <div className="text-white/60 text-sm">End your day with gratitude</div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.05 }}
          className="glass-card rounded-xl p-4 cursor-pointer"
        >
          <div className="text-3xl mb-2">🎯</div>
          <div className="text-white font-semibold mb-1">Weekly Deep Dive</div>
          <div className="text-white/60 text-sm">Hypnosis session</div>
        </motion.div>
      </div>
    </div>
  )
}
