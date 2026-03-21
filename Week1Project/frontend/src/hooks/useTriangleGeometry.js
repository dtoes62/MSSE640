import { CANVAS_SIZE, CENTER } from '../constants'

const MAX_DISPLAY = 230  // max triangle dimension in canvas pixels

/**
 * Given three validated side lengths, compute SVG/CSS coordinates
 * for vertices, side midpoints, angles, and lengths within the canvas.
 */
export function computeTriangleGeometry(a, b, c) {
  // Law of cosines: place A at origin, B along positive x-axis
  const cosA = (b * b + c * c - a * a) / (2 * b * c)
  const sinA  = Math.sqrt(Math.max(0, 1 - cosA * cosA))

  const Ax = 0,      Ay = 0
  const Bx = c,      By = 0
  const Cx = b * cosA, Cy = b * sinA

  // Centroid
  const centX = (Ax + Bx + Cx) / 3
  const centY = (Ay + By + Cy) / 3

  // Scale to fit MAX_DISPLAY
  const w = Math.max(Ax, Bx, Cx) - Math.min(Ax, Bx, Cx)
  const h = Math.max(Ay, By, Cy) - Math.min(Ay, By, Cy)
  const scale = MAX_DISPLAY / Math.max(w, h)

  // Transform: center on canvas, flip Y (SVG y increases downward)
  const toCanvas = (x, y) => [
    (x - centX) * scale + CENTER,
    -(y - centY) * scale + CENTER,
  ]

  const [vAx, vAy] = toCanvas(Ax, Ay)
  const [vBx, vBy] = toCanvas(Bx, By)
  const [vCx, vCy] = toCanvas(Cx, Cy)

  // Side 0: A-B (length c) ← top origin
  // Side 1: A-C (length b) ← left origin
  // Side 2: B-C (length a) ← right origin
  const rawSides = [
    [[vAx, vAy], [vBx, vBy]],
    [[vAx, vAy], [vCx, vCy]],
    [[vBx, vBy], [vCx, vCy]],
  ]

  const sides = rawSides.map(([[x1, y1], [x2, y2]]) => {
    const midX     = (x1 + x2) / 2
    const midY     = (y1 + y2) / 2
    const len      = Math.hypot(x2 - x1, y2 - y1)
    const angleDeg = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI)
    return { x1, y1, x2, y2, midX, midY, len, angleDeg }
  })

  return {
    sides,
    centroid:      [(vAx + vBx + vCx) / 3, (vAy + vBy + vCy) / 3],
    polygonPoints: `${vAx},${vAy} ${vBx},${vBy} ${vCx},${vCy}`,
  }
}

/**
 * For invalid triangles we still need proportional display lengths
 * so the sides look right during the collision animation.
 */
export function scaleDisplayLengths(a, b, c) {
  const max   = Math.max(a, b, c)
  const scale = 160 / max
  return [a * scale, b * scale, c * scale]
}
