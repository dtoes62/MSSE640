import { useState, useEffect } from 'react'
import { analyzeTriangle }     from './api'
import { TriangleForm }        from './components/TriangleForm'
import { TriangleAnimation }   from './components/TriangleAnimation'
import { TriangleLegend }      from './components/TriangleLegend'
import './index.css'

export default function App() {
  const [values,    setValues]    = useState({ a: '', b: '', c: '' })
  const [committed, setCommitted] = useState(null)
  const [result,    setResult]    = useState(null)
  const [animKey,   setAnimKey]   = useState(0)
  const [loading,   setLoading]   = useState(false)

  const handleChange = (key, val) => setValues(prev => ({ ...prev, [key]: val }))

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
        setAnimKey(k => k + 1)
      } finally {
        setLoading(false)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [values.a, values.b, values.c])

  return (
    <div className="min-h-screen bg-slate-900 px-4 py-8 lg:px-10 lg:py-10">
      <div className="mx-auto max-w-6xl">

        {/* Page header */}
        <h1 className="mb-8 text-center text-3xl font-bold tracking-tight text-white lg:text-4xl">
          Triangle Analyzer
        </h1>

        {/* Two-column on desktop, single column on mobile */}
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:gap-10">

          {/* Left panel: form + legend */}
          <div className="flex flex-col gap-6 lg:w-96 lg:flex-shrink-0">
            <TriangleForm values={values} onChange={handleChange} loading={loading} />
            <TriangleLegend />
          </div>

          {/* Right panel: animation canvas — fills remaining width, self-centers */}
          <div className="flex flex-1 self-stretch items-center justify-center">
            {committed && result ? (
              <TriangleAnimation
                key={animKey}
                a={committed.a}
                b={committed.b}
                c={committed.c}
                result={result}
              />
            ) : (
              <div className="flex w-full items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-800/30 py-24 lg:py-0 lg:min-h-[500px]">
                <p className="text-slate-500">Enter side lengths to see the animation</p>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}
