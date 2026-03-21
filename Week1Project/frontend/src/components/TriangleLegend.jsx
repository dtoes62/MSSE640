import { TYPE_COLORS } from '../constants'

const TYPES = [
  { type: 'equilateral', description: 'All 3 sides equal',        points: '20,5 5,30 35,30' },
  { type: 'isosceles',   description: 'Exactly 2 sides equal',    points: '20,5 2,30 38,30' },
  { type: 'scalene',     description: 'All 3 sides different',    points: '5,30 18,5 40,30' },
]

export function TriangleLegend() {
  return (
    <div className="mt-8 rounded-2xl border border-slate-700 bg-slate-800/60 p-5 backdrop-blur">
      <h3 className="mb-4 text-center text-sm font-semibold uppercase tracking-widest text-slate-400">
        Triangle Types
      </h3>
      <div className="flex flex-col gap-3 sm:flex-row sm:justify-around">
        {TYPES.map(({ type, description, points }) => (
          <div key={type} className="flex items-center gap-3">
            <svg width="42" height="36" viewBox="0 0 42 36">
              <polygon
                points={points}
                fill={TYPE_COLORS[type]}
                fillOpacity={0.25}
                stroke={TYPE_COLORS[type]}
                strokeWidth={2}
                strokeLinejoin="round"
              />
            </svg>
            <div>
              <p className="font-semibold capitalize" style={{ color: TYPE_COLORS[type] }}>
                {type}
              </p>
              <p className="text-xs text-slate-400">{description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
