import { useState, useEffect } from 'react'
import { analyzeTriangle }     from './api'
import { TriangleForm }        from './components/TriangleForm'
import { TriangleAnimation }   from './components/TriangleAnimation'
import { TriangleLegend }      from './components/TriangleLegend'
import './index.css'

export default function App() {
  const [values,    setValues]    = useState({ a: '', b: '', c: '' })
  const [committed, setCommitted] = useState(null)   // last submitted {a,b,c}
  const [result,    setResult]    = useState(null)   // last API response
  const [animKey,   setAnimKey]   = useState(0)      // increment → re-animate
  const [loading,   setLoading]   = useState(false)

  const handleChange = (key, val) => setValues(prev => ({ ...prev, [key]: val }))

  // Auto-fire: debounced 500ms after user stops typing, once all fields filled
  useEffect(() => {
    const { a, b, c } = values
    if (!a || !b || !c) return
    if (isNaN(+a) || isNaN(+b) || isNaN(+c)) return

    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await analyzeTriangle(+a, +b, +c)
        setResult(data)
        setCommitted({ a: +a, b: +b, c: +c })
        setAnimKey(k => k + 1)     // remount TriangleAnimation → replay
      } finally {
        setLoading(false)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [values.a, values.b, values.c])

  return (
    <div className="min-h-screen bg-slate-900 px-4 py-8">
      <div className="mx-auto max-w-lg">

        <TriangleForm values={values} onChange={handleChange} loading={loading} />

        {/* Animation canvas — keyed so it remounts fresh on each new result.
            Shows previous result while the user types (committed stays stable). */}
        {committed && result && (
          <div className="mt-6">
            <TriangleAnimation
              key={animKey}
              a={committed.a}
              b={committed.b}
              c={committed.c}
              result={result}
            />
          </div>
        )}

        <TriangleLegend />
      </div>
    </div>
  )
}
