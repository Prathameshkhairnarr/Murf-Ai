'use client';

import { useState, useCallback } from 'react';
import { motion } from 'motion/react';
import { Waves, Activity, ShieldAlert } from 'lucide-react';

type ViewState = 'ready' | 'connecting' | 'mic_error';

// ─── Connecting — High-tech Sci-Fi Animation ────────────────────────────────
function ConnectingView() {
  return (
    <div className="flex flex-col items-center justify-center gap-14">
      <div className="relative flex size-48 items-center justify-center">
        {/* Deep ambient glow */}
        <div className="absolute size-48 rounded-full bg-red-600/20 blur-3xl animate-pulse" />

        {/* Outer counter-rotating dashed ring */}
        <svg className="absolute size-44 animate-spin text-red-500/30" style={{ animationDuration: '8s', animationDirection: 'reverse' }} viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 6" />
        </svg>

        {/* Inner fast-rotating dashed ring */}
        <svg className="absolute size-36 animate-spin text-red-500/60" style={{ animationDuration: '4s' }} viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="48" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="15 15" />
        </svg>

        {/* Middle pulsing ring */}
        <div className="absolute size-24 rounded-full border border-red-500/80 shadow-[0_0_20px_rgba(220,38,38,0.5)] animate-ping" style={{ animationDuration: '2s' }} />

        {/* Central Core */}
        <div className="relative z-10 size-12 rounded-full bg-red-600 shadow-[0_0_30px_10px_rgba(220,38,38,0.6)]">
          <div className="absolute inset-0 rounded-full bg-white/20 animate-pulse" style={{ animationDuration: '0.5s' }} />
        </div>
      </div>

      <div className="space-y-3 text-center">
        <h2 className="text-xl font-bold tracking-widest text-white uppercase drop-shadow-[0_0_10px_rgba(220,38,38,0.8)]">
          Establishing Link
        </h2>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-red-400 animate-pulse">
          Connecting to Rakshika Core
        </p>
      </div>
    </div>
  );
}

// ─── Mic Error ─────────────────────────────────────────────────────────────────
function MicErrorView({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center gap-8 text-center">
      {/* Crossed mic indicator */}
      <div className="flex size-20 items-center justify-center rounded-full border border-red-500/20 bg-red-950/30">
        <svg className="size-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M19 10v2a7 7 0 01-14 0v-2M3 3l18 18" />
        </svg>
      </div>
      <div className="max-w-xs space-y-2">
        <p className="text-base font-semibold text-white">Microphone Access Denied</p>
        <p className="text-sm leading-relaxed text-gray-500">
          Rakshika needs microphone access to hear you. Open your browser settings, allow microphone, and try again.
        </p>
      </div>
      <button
        id="mic-retry-button"
        onClick={onRetry}
        className="rounded-full border border-white/10 px-6 py-2.5 text-sm font-medium text-gray-300 transition-colors hover:border-white/25 hover:text-white"
      >
        Try Again
      </button>
    </div>
  );
}

// ─── Helpline Card ─────────────────────────────────────────────────────────────
function HelplineCard({ label, number, sub }: { label: string; number: string; sub?: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5 rounded-xl border border-white/6 bg-white/[0.03] px-6 py-5 backdrop-blur-sm">
      <span className="font-mono text-2xl font-bold tabular-nums text-white">{number}</span>
      <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</span>
      {sub && <span className="font-mono text-[10px] text-gray-700">{sub}</span>}
    </div>
  );
}

// ─── Main Welcome View ─────────────────────────────────────────────────────────
interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  callEnded?: boolean;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  callEnded = false,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [viewState, setViewState] = useState<ViewState>('ready');

  const handleStart = useCallback(async () => {
    setViewState('connecting');
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      onStartCall();
    } catch {
      setViewState('mic_error');
    }
  }, [onStartCall]);

  return (
    <div
      ref={ref}
      className="relative min-h-dvh overflow-hidden bg-[#060608] flex flex-col items-center justify-center px-6 py-16"
    >
      {/* ── Glowing Glassmorphic Background ── */}
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center overflow-hidden"
        aria-hidden
      >
        {/* Red Glow Blob */}
        <div
          className="absolute size-[600px] -translate-x-1/4 -translate-y-1/4 rounded-full bg-red-600/20 blur-[120px] animate-pulse"
          style={{ animationDuration: '6s' }}
        />
        {/* Blue/Purple Glow Blob */}
        <div
          className="absolute size-[500px] translate-x-1/3 translate-y-1/4 rounded-full bg-blue-600/20 blur-[140px] animate-pulse"
          style={{ animationDuration: '8s' }}
        />
      </div>

      {/* Subtle grid lines */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        aria-hidden
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
          backgroundSize: '72px 72px',
        }}
      />

      {/* ── Non-ready States ── */}
      {viewState === 'connecting' && (
        <div className="relative z-10">
          <ConnectingView />
        </div>
      )}
      {viewState === 'mic_error' && (
        <div className="relative z-10">
          <MicErrorView onRetry={() => setViewState('ready')} />
        </div>
      )}

      {/* ── Ready State ── */}
      {viewState === 'ready' && (
        <motion.div 
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: {
                staggerChildren: 0.15
              }
            }
          }}
          className="relative z-10 flex w-full max-w-3xl flex-col items-center gap-14 text-center"
        >

          {/* Status pill / Powered By */}
          <motion.div 
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: "easeOut" } }
            }}
            className="flex items-center gap-2.5 rounded-full border border-white/10 bg-black/40 px-4 py-1.5 backdrop-blur-md"
          >
            {/* Simple lightning bolt icon for power */}
            <svg className="size-3.5 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-[11px] font-medium tracking-widest uppercase text-gray-400">
              Powered by <strong className="text-white">Murf AI</strong> & <strong className="text-white">LiveKit</strong>
            </span>
          </motion.div>

          {/* Minimalist Hero Section */}
          <div className="space-y-6">
            <motion.h1
              className="text-[96px] font-black leading-none tracking-tight text-white flex justify-center"
              style={{ textShadow: '0 0 80px rgba(220,38,38,0.25)' }}
              variants={{
                hidden: {},
                visible: {
                  transition: { staggerChildren: 0.1 }
                }
              }}
            >
              {"RAKSHIKA".split('').map((char, index) => (
                <motion.span
                  key={index}
                  variants={{
                    hidden: { opacity: 0, y: 40, filter: "blur(10px)", scale: 0.8 },
                    visible: { 
                      opacity: 1, 
                      y: 0, 
                      filter: "blur(0px)", 
                      scale: 1,
                      transition: { duration: 1, ease: [0.16, 1, 0.3, 1] } 
                    }
                  }}
                  className="inline-block"
                >
                  {char}
                </motion.span>
              ))}
            </motion.h1>
            <motion.p 
              variants={{
                hidden: { opacity: 0 },
                visible: { opacity: 1, transition: { duration: 1, delay: 0.3 } }
              }}
              className="font-mono text-sm uppercase tracking-[0.35em] text-gray-500"
            >
              {callEnded ? (
                <span className="text-red-400 font-bold">● Session Ended · Ready for next call</span>
              ) : (
                "Emergency Voice Response"
              )}
            </motion.p>
          </div>

          {/* Interactive Feature Cards */}
          <motion.div 
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.8, delay: 0.4 } }
            }}
            className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-4xl mt-2"
          >
            {[
              { icon: <Waves className="size-6 text-blue-400" />, title: 'Flood Guidance', desc: 'Real-time evacuation routing and safe zone mapping.' },
              { icon: <Activity className="size-6 text-green-400" />, title: 'Medical Aid', desc: 'Instant first-aid voice support for critical injuries.' },
              { icon: <ShieldAlert className="size-6 text-red-500" />, title: 'NDRF Rescue', desc: 'Direct escalation and connection to response teams.' },
            ].map((item, i) => (
              <motion.div
                key={i}
                whileHover={{ y: -5 }}
                className="group flex flex-col items-start gap-4 rounded-2xl border border-white/5 bg-white/[0.03] p-6 text-left backdrop-blur-md transition-colors hover:bg-white/[0.08] hover:border-white/20"
              >
                <div className="flex size-12 items-center justify-center rounded-full bg-white/5 text-xl shadow-inner border border-white/10 group-hover:bg-red-500/20 group-hover:border-red-500/30 transition-colors">
                  {item.icon}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white tracking-wide">{item.title}</h3>
                  <p className="mt-2 text-[13px] text-gray-400 leading-relaxed">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* CTA Button */}
          <motion.div 
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.8, delay: 0.5, ease: "easeOut" } }
            }}
            className="flex flex-col items-center gap-4"
          >
            <button
              id="start-emergency-call"
              onClick={handleStart}
              className="group relative overflow-hidden rounded-full bg-red-600 px-12 py-4 text-base font-bold tracking-wide text-white shadow-2xl shadow-red-900/60 transition-all duration-300 hover:bg-red-500 hover:shadow-red-700/60 hover:scale-105 active:scale-100"
            >
              {/* Button glow on hover */}
              <span className="absolute inset-0 rounded-full bg-white/10 opacity-0 transition-opacity group-hover:opacity-100" />
              <span className="relative">{callEnded ? 'Start New Call' : startButtonText}</span>
            </button>

            <p className="font-mono text-sm uppercase tracking-widest text-gray-500">
              Murf Falcon · LiveKit · Deepgram Nova-3
            </p>
          </motion.div>

        </motion.div>
      )}
    </div>
  );
};
