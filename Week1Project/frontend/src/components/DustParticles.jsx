import { motion } from 'framer-motion'

const COUNT = 18

export function DustParticles({ centroidX, centroidY, color }) {
  const particles = Array.from({ length: COUNT }, (_, i) => {
    const angle    = (i / COUNT) * Math.PI * 2
    const distance = 45 + (i % 3) * 20          // varied distances
    const size     = 3 + (i % 4)                 // varied sizes
    return {
      id:      i,
      targetX: Math.cos(angle) * distance,
      targetY: Math.sin(angle) * distance,
      size,
      delay:   (i % 3) * 0.04,
    }
  })

  return (
    <>
      {particles.map(p => (
        <motion.div
          key={p.id}
          style={{
            position:     'absolute',
            width:        p.size,
            height:       p.size,
            borderRadius: '50%',
            background:   color,
            boxShadow:    `0 0 6px 1px ${color}`,
            top:          centroidY,
            left:         centroidX,
            marginLeft:   -p.size / 2,
            marginTop:    -p.size / 2,
          }}
          initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
          animate={{ x: p.targetX, y: p.targetY, opacity: 0, scale: 0 }}
          transition={{ duration: 0.65, ease: 'easeOut', delay: p.delay }}
        />
      ))}
    </>
  )
}
