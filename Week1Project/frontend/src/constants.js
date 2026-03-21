export const TYPE_COLORS = {
  equilateral: '#F59E0B',
  isosceles:   '#14B8A6',
  scalene:     '#8B5CF6',
}

export const CANVAS_SIZE = 400
export const CENTER      = CANVAS_SIZE / 2  // 200

// Where each side originates before flying in
// index 0 = top-center, 1 = left-center, 2 = right-center
export const ORIGINS = [
  { x: CENTER,                y: 30           },  // top
  { x: 30,                    y: CENTER        },  // left
  { x: CANVAS_SIZE - 30,      y: CENTER        },  // right
]

// Bounce targets after collision (offsets from canvas center)
export const BOUNCE_OFFSETS = [
  { x:  20,  y: -90 },   // top side bounces upward
  { x: -110, y:  70 },   // left side bounces left-down
  { x:  110, y:  70 },   // right side bounces right-down
]
