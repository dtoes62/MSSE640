import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { TriangleSide }   from './TriangleSide'
import { DustParticles }  from './DustParticles'
import { LiquidMetal }    from './LiquidMetal'
import { computeTriangleGeometry, scaleDisplayLengths } from '../hooks/useTriangleGeometry'
import { TYPE_COLORS, CANVAS_SIZE, CENTER } from '../constants'

/**
 * The full animation canvas.  Mount this fresh (via React key) each time
 * a new API result arrives — it always plays from scratch.
 */
export function TriangleAnimation({ a, b, c, result }) {
  const [lockedCount,  setLockedCount]  = useState(0)
  const [showDust,     setShowDust]     = useState(false)
  const [showPolygon,  setShowPolygon]  = useState(false)
  const [rippleKey,    setRippleKey]    = useState(0)
  const lockedRef = useRef(0)   // ref copy so closure inside TriangleSide stays fresh

  // Canvas responsiveness: scale down when parent is narrower than 400px
  const wrapRef  = useRef(null)
  const [scale, setScale] = useState(1)
  useEffect(() => {
    const update = () => {
      if (wrapRef.current) {
        const w = wrapRef.current.parentElement?.offsetWidth ?? CANVAS_SIZE
        setScale((w - 16) / CANVAS_SIZE)
      }
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  const isValid     = result?.valid === true
  const typeColor   = TYPE_COLORS[result?.triangle_type] ?? '#6B7280'
  const geometry    = isValid ? computeTriangleGeometry(a, b, c) : null
  const displayLens = isValid
    ? geometry.sides.map(s => s.len)
    : scaleDisplayLengths(a, b, c)

  // Called by each TriangleSide when it finishes its animation
  const handleSideComplete = () => {
    if (isValid) {
      lockedRef.current += 1
      setLockedCount(lockedRef.current)
    } else {
      // Trigger a ripple in the pool for each side that melts in
      setRippleKey(k => k + 1)
    }
  }

  // When all three valid sides have landed → dust → then polygon
  useEffect(() => {
    if (lockedCount < 3) return
    setShowDust(true)
    const timer = setTimeout(() => setShowPolygon(true), 350)
    return () => clearTimeout(timer)
  }, [lockedCount])

  return (
    // Outer wrapper collapses to the visual height after scaling so no dead
    // space appears below the canvas on small screens.
    <div ref={wrapRef} style={{ width: '100%', display: 'flex', justifyContent: 'center', height: CANVAS_SIZE * scale }}>
      <div
        style={{
          position:        'relative',
          width:           CANVAS_SIZE,
          height:          CANVAS_SIZE,
          transform:       `scale(${scale})`,
          transformOrigin: 'top center',
          flexShrink:      0,
        }}
      >
        {/* ── Liquid metal pool (always visible at bottom) ── */}
        <LiquidMetal rippleKey={rippleKey} />

        {/* ── Three animated sides ── */}
        {[0, 1, 2].map(i => (
          <TriangleSide
            key={i}
            index={i}
            len={displayLens[i]}
            isValid={isValid}
            targetX={isValid ? geometry.sides[i].midX - CENTER : 0}
            targetY={isValid ? geometry.sides[i].midY - CENTER : 0}
            targetAngle={isValid ? geometry.sides[i].angleDeg : 0}
            color={isValid ? typeColor : '#9CA3AF'}
            delay={i * 0.07}
            onComplete={handleSideComplete}
          />
        ))}

        {/* ── Dust particle burst (valid only, fires after sides lock) ── */}
        {showDust && geometry && (
          <DustParticles
            centroidX={geometry.centroid[0]}
            centroidY={geometry.centroid[1]}
            color={typeColor}
          />
        )}

        {/* ── SVG polygon overlay (valid only, fades in after dust) ── */}
        {geometry && (
          <svg
            viewBox={`0 0 ${CANVAS_SIZE} ${CANVAS_SIZE}`}
            style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
            width={CANVAS_SIZE}
            height={CANVAS_SIZE}
          >
            <motion.polygon
              points={geometry.polygonPoints}
              fill={typeColor}
              fillOpacity={0.2}
              stroke={typeColor}
              strokeWidth={2.5}
              strokeLinejoin="round"
              style={{ transformBox: 'fill-box', transformOrigin: 'center' }}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={showPolygon ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.85 }}
              transition={{ duration: 0.45, ease: 'backOut' }}
            />
          </svg>
        )}

        {/* ── Result label ── */}
        {showPolygon && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.3 }}
            style={{
              position:  'absolute',
              bottom:    90,
              left:      0,
              right:     0,
              textAlign: 'center',
              pointerEvents: 'none',
            }}
          >
            <span
              style={{
                background:   `${typeColor}22`,
                border:       `1px solid ${typeColor}88`,
                borderRadius: 12,
                color:        typeColor,
                fontSize:     15,
                fontWeight:   700,
                padding:      '4px 16px',
                textTransform: 'capitalize',
              }}
            >
              {result.triangle_type}
            </span>
          </motion.div>
        )}

        {/* ── Invalid message ── */}
        {!isValid && result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.6 }}
            style={{
              position:  'absolute',
              bottom:    90,
              left:      16,
              right:     16,
              textAlign: 'center',
              color:     '#F87171',
              fontSize:  13,
              fontWeight: 600,
            }}
          >
            {result.message}
          </motion.div>
        )}
      </div>
    </div>
  )
}
