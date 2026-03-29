export function TriangleForm({ values, onChange, loading }) {
  const sides = [
    { key: 'a', label: 'Side A' },
    { key: 'b', label: 'Side B' },
    { key: 'c', label: 'Side C' },
  ]

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-800/60 p-6 backdrop-blur">
      <p className="mb-6 text-center text-sm text-slate-400">
        Enter three side lengths — the result animates automatically.
      </p>
      <div className="flex flex-col gap-4 sm:flex-row">
        {sides.map(({ key, label }) => (
          <div key={key} className="flex flex-1 flex-col gap-1">
            <label htmlFor={key} className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              {label}
            </label>
            <input
              id={key}
              type="number"
              min="0"
              step="any"
              value={values[key]}
              onChange={e => onChange(key, e.target.value)}
              placeholder="0"
              className="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-3 text-center text-lg font-bold text-white placeholder-slate-600 outline-none transition focus:border-violet-500 focus:ring-2 focus:ring-violet-500/30"
            />
          </div>
        ))}
      </div>
      {loading && (
        <p className="mt-4 text-center text-sm text-slate-400 animate-pulse">Analyzing…</p>
      )}
    </div>
  )
}
