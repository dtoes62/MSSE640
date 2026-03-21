import { useEffect } from 'react'
import { motion, useAnimate } from 'framer-motion'
import { CENTER, ORIGINS, BOUNCE_OFFSETS } from '../constants'

/**
 * One animated triangle side (rendered as a thin div / rotated bar).
 *
 * Coordinate system: Framer Motion x/y are offsets from the canvas center
 * (CENTER, CENTER).  The div is base-positioned at center via CSS, so
 * x=0,y=0 places the midpoint of the side exactly at the canvas center.
 *
 * Props:
 *   index       - 0 (top), 1 (left), 2 (right) — controls origin & bounce
 *   len         - pixel length of this side
 *   isValid     - true → spring fly-in to target; false → collision sequence
 *   targetX/Y   - midpoint offset from center (valid only)
 *   targetAngle - final rotation in degrees (valid only)
 *   color       - side color
 *   delay       - stagger delay in seconds
 *   onComplete  - called when animation finishes
 */
export function TriangleSide({
  index,
  len,
  isValid,
  targetX = 0,
  targetY = 0,
  targetAngle = 0,
  color,
  delay = 0,
  onComplete,
}) {
  const [scope, animate] = useAnimate()
  const origin = ORIGINS[index]
  const bounce = BOUNCE_OFFSETS[index]

  // Initial offset from canvas center to this side's origin
  const initX = origin.x - CENTER
  const initY = origin.y - CENTER

  useEffect(() => {
    if (!scope.current) return

    const run = async () => {
      // Snap to starting position instantly (no transition)
      await animate(
        scope.current,
        { x: initX, y: initY, rotate: targetAngle + 720, opacity: 1 },
        { duration: 0 },
      )

      if (isValid) {
        // Spring fly-in — rotation decelerates naturally with the spring
        await animate(
          scope.current,
          { x: targetX, y: targetY, rotate: targetAngle },
          { type: 'spring', stiffness: 55, damping: 13, delay },
        )
        onComplete?.()
      } else {
        // ── Phase 1: fly toward center ──────────────────────────────────
        await animate(
          scope.current,
          { x: 0, y: 0, rotate: 0 },
          { duration: 0.45, ease: 'easeIn', delay },
        )

        // ── Phase 2: bounce outward ──────────────────────────────────────
        await animate(
          scope.current,
          { x: bounce.x, y: bounce.y, rotate: bounce.x > 0 ? 35 : -35 },
          { duration: 0.28, ease: 'easeOut' },
        )

        // ── Phase 3: fall into liquid metal pool (T2 style) ─────────────
        // Color shifts orange-white-hot as it sinks; opacity fades to 0
        await animate(
          scope.current,
          {
            y:      185,
            rotate: bounce.x >= 0 ? 90 : -90,
            filter: 'brightness(4) saturate(3)',
            opacity: 0,
          },
          { duration: 0.75, ease: 'easeIn' },
        )

        onComplete?.()
      }
    }

    run()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Beam dimensions ───────────────────────────────────────────────────────
  const BEAM_H    = 40   // total height
  const FLANGE_H  = 9    // each flange
  const OVERHANG  = 18   // how far each flange extends past the web on each side
  const GAP_W     = 18   // rectangular hole width
  const SOLID_W   = 28   // solid web section between holes

  // ── Steel gradients ───────────────────────────────────────────────────────
  // Flange: bright specular band at 50% simulates light catching the flat face
  const flangeGrad = `linear-gradient(to bottom,
    #1a2530 0%,
    #38566a 12%,
    #7aaabb 30%,
    #c0d8ea 46%,
    #e6f4ff 50%,
    #c0d8ea 54%,
    #7aaabb 70%,
    #38566a 88%,
    #1a2530 100%)`

  // Web: darker, recessed — punched out by the mask below
  const webGrad = `linear-gradient(to bottom,
    #0a1018 0%,
    #1e3040 25%,
    #2e4858 50%,
    #1e3040 75%,
    #0a1018 100%)`

  // CSS mask punches rectangular holes through the web
  const webMask = `repeating-linear-gradient(
    to right,
    black     0px,
    black     ${SOLID_W}px,
    transparent ${SOLID_W}px,
    transparent ${SOLID_W + GAP_W}px
  )`

  // Coloured glow hints at triangle type for both valid and invalid beams
  const glow = `0 4px 14px rgba(0,0,0,0.8), 0 0 18px ${color}66`

  return (
    <motion.div
      ref={scope}
      style={{
        position:        'absolute',
        width:           len,
        height:          BEAM_H,
        display:         'flex',
        flexDirection:   'column',
        top:             CENTER,
        left:            CENTER,
        marginLeft:      -len / 2,
        marginTop:       -BEAM_H / 2,
        transformOrigin: 'center',
        willChange:      'transform',
        opacity:         0,
        boxShadow:       glow,
        borderRadius:    3,
        overflow:        'hidden',
      }}
    >
      {/* Top flange — full width */}
      <div style={{ height: FLANGE_H, background: flangeGrad, flexShrink: 0 }} />

      {/* Web — indented so flanges visibly overhang; rectangular gaps via mask */}
      <div style={{
        flex:                 1,
        margin:               `0 ${OVERHANG}px`,
        background:           webGrad,
        WebkitMaskImage:      webMask,
        maskImage:            webMask,
      }} />

      {/* Bottom flange — full width */}
      <div style={{ height: FLANGE_H, background: flangeGrad, flexShrink: 0 }} />
    </motion.div>
  )
}
