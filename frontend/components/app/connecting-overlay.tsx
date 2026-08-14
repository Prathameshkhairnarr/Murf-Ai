'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useDataChannel } from '@livekit/components-react';

export function ConnectingOverlay() {
  const [connecting, setConnecting] = useState<string | null>(null);

  useDataChannel('', (msg) => {
    try {
      const data = JSON.parse(new TextDecoder().decode(msg.payload));
      if (data.type === 'agent_transfer') {
        setConnecting(data.to);
      }
    } catch {
      // ignore
    }
  });

  useEffect(() => {
    if (!connecting) return;
    // Automatically hide after 5 seconds
    const t = setTimeout(() => { setConnecting(null); }, 5000);
    return () => clearTimeout(t);
  }, [connecting]);

  if (!connecting) return null;

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
          {/* Connecting rings */}
          <div className="relative flex items-center justify-center mb-8" style={{ width: 100, height: 100 }}>
            {[0, 0.6, 1.2].map((delay) => (
              <motion.div
                key={delay}
                animate={{ scale: [1, 2.5], opacity: [0.5, 0] }}
                transition={{ duration: 2, repeat: Infinity, delay, ease: 'easeOut' }}
                className="absolute rounded-full"
                style={{ width: 64, height: 64, border: '2px solid rgba(59,130,246,0.8)' }}
              />
            ))}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
              className="relative z-10 flex items-center justify-center rounded-full"
              style={{
                width: 64, height: 64,
                background: '#2563eb',
                boxShadow: '0 0 30px rgba(37,99,235,0.5)',
              }}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
              </svg>
            </motion.div>
          </div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-8">
            <p className="text-blue-400 text-lg font-medium tracking-wide">Connecting...</p>
            <p className="text-white/60 text-sm mt-2">Transferring call to {connecting === 'shelter' ? 'Aarav (Shelter Specialist)' : connecting}</p>
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
