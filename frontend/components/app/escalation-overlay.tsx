'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useDataChannel } from '@livekit/components-react';

interface EscalationData {
  type: string;
  reference_id: string;
  caller_name: string;
  urgency: string;
  summary: string;
}

export function EscalationOverlay() {
  const [escalation, setEscalation] = useState<EscalationData | null>(null);
  const [phase, setPhase] = useState<'ringing' | 'sent' | null>('ringing');

  useDataChannel('', (msg) => {
    try {
      const data = JSON.parse(new TextDecoder().decode(msg.payload));
      if (data.type === 'escalation_alert') {
        setEscalation(data);
        setPhase('ringing');
      }
    } catch {
      // ignore
    }
  });

  useEffect(() => {
    if (!escalation) return;
    const t1 = setTimeout(() => setPhase('sent'), 4500);
    const t2 = setTimeout(() => { setEscalation(null); setPhase('ringing'); }, 9000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [escalation]);

  if (!escalation) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] flex items-center justify-center"
        style={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(20px)' }}
      >
        <motion.div
          initial={{ y: 40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col items-center w-[380px] max-w-[92vw]"
        >
          {/* Phone icon with ripple */}
          <div className="relative flex items-center justify-center mb-8" style={{ width: 100, height: 100 }}>
            {phase === 'ringing' && (
              <>
                {[0, 0.6, 1.2].map((delay) => (
                  <motion.div
                    key={delay}
                    animate={{ scale: [1, 2.8], opacity: [0.35, 0] }}
                    transition={{ duration: 2, repeat: Infinity, delay, ease: 'easeOut' }}
                    className="absolute rounded-full"
                    style={{ width: 64, height: 64, border: '2px solid rgba(239,68,68,0.5)' }}
                  />
                ))}
              </>
            )}
            {phase === 'sent' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: [0, 1.3, 1] }}
                transition={{ duration: 0.5 }}
                className="absolute rounded-full"
                style={{ width: 90, height: 90, background: 'rgba(34,197,94,0.15)' }}
              />
            )}
            <motion.div
              animate={phase === 'ringing' ? { rotate: [0, 12, -12, 8, -8, 0] } : {}}
              transition={{ duration: 0.6, repeat: phase === 'ringing' ? Infinity : 0, repeatDelay: 0.8 }}
              className="relative z-10 flex items-center justify-center rounded-full"
              style={{
                width: 64, height: 64,
                background: phase === 'sent' ? '#16a34a' : '#dc2626',
                boxShadow: phase === 'sent' ? '0 0 40px rgba(34,197,94,0.4)' : '0 0 40px rgba(220,38,38,0.4)',
                transition: 'background 0.4s, box-shadow 0.4s',
              }}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                {phase === 'sent' ? (
                  <motion.path
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                    d="M20 6L9 17l-5-5"
                  />
                ) : (
                  <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z" />
                )}
              </svg>
            </motion.div>
          </div>

          {/* Status text */}
          <AnimatePresence mode="wait">
            {phase === 'ringing' ? (
              <motion.div key="ringing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center mb-8">
                <p className="text-white text-lg font-medium tracking-wide">Calling Rescue Team</p>
                <motion.div className="flex items-center justify-center gap-1 mt-2">
                  {[0, 0.2, 0.4].map((d) => (
                    <motion.span
                      key={d}
                      animate={{ opacity: [0.2, 1, 0.2] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay: d }}
                      className="w-1.5 h-1.5 rounded-full bg-white/60"
                    />
                  ))}
                </motion.div>
              </motion.div>
            ) : (
              <motion.div key="sent" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
                <p className="text-green-400 text-lg font-medium">Request Dispatched</p>
                <p className="text-white/40 text-sm mt-1">Team has been alerted</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Info card */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="w-full rounded-2xl overflow-hidden"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <span className="text-white/30 text-xs uppercase tracking-widest">Reference</span>
              <span className="text-white font-mono text-sm font-semibold">{escalation.reference_id}</span>
            </div>
            <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <span className="text-white/30 text-xs uppercase tracking-widest">Urgency</span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full" style={{
                background: escalation.urgency === 'emergency' ? 'rgba(239,68,68,0.15)' : escalation.urgency === 'high' ? 'rgba(249,115,22,0.15)' : 'rgba(234,179,8,0.15)',
                color: escalation.urgency === 'emergency' ? '#fca5a5' : escalation.urgency === 'high' ? '#fdba74' : '#fde047',
              }}>
                {escalation.urgency.toUpperCase()}
              </span>
            </div>
            <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <span className="text-white/30 text-xs uppercase tracking-widest">Caller</span>
              <span className="text-white/80 text-sm">{escalation.caller_name}</span>
            </div>
            <div className="px-5 py-4">
              <span className="text-white/30 text-xs uppercase tracking-widest">Situation</span>
              <p className="text-white/60 text-sm mt-1.5 leading-relaxed">{escalation.summary}</p>
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
