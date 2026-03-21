import { motion } from 'framer-motion'

// rippleKey: increment this to fire a new ripple each time a side melts in
export function LiquidMetal({ rippleKey = 0 }) {
  return (
    <svg
      viewBox="0 0 400 80"
      style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 80, overflow: 'visible' }}
    >
      <defs>
        <linearGradient id="poolGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#FEF3C7" />
          <stop offset="15%"  stopColor="#FBBF24" />
          <stop offset="45%"  stopColor="#F97316" />
          <stop offset="75%"  stopColor="#B91C1C" />
          <stop offset="100%" stopColor="#3B0000" />
        </linearGradient>
        <radialGradient id="poolHot" cx="50%" cy="0%" r="60%">
          <stop offset="0%"   stopColor="#FFFBEB" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#F59E0B" stopOpacity="0"   />
        </radialGradient>
        <filter id="poolGlow" x="-20%" y="-60%" width="140%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Main pool body — wave animation via Framer Motion path morphing */}
      <motion.path
        fill="url(#poolGrad)"
        filter="url(#poolGlow)"
        animate={{
          d: [
            'M 0 18 Q 100 8  200 18 Q 300 28 400 18 L 400 80 L 0 80 Z',
            'M 0 18 Q 100 28 200 18 Q 300 8  400 18 L 400 80 L 0 80 Z',
          ],
        }}
        transition={{ duration: 2.4, repeat: Infinity, repeatType: 'reverse', ease: 'easeInOut' }}
      />

      {/* Hot-spot shimmer */}
      <rect x={0} y={0} width={400} height={80} fill="url(#poolHot)" />

      {/* Ripple each time a side melts in */}
      {rippleKey > 0 && (
        <motion.ellipse
          key={rippleKey}
          cx={200} cy={18}
          fill="none"
          stroke="#FEF3C7"
          strokeWidth={2}
          initial={{ rx: 6,  ry: 3,  opacity: 0.9 }}
          animate={{ rx: 90, ry: 22, opacity: 0   }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />
      )}
    </svg>
  )
}
