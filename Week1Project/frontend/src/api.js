const BASE = 'http://localhost:8000'

export async function analyzeTriangle(a, b, c) {
  const res = await fetch(`${BASE}/triangle`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ a, b, c }),
  })
  return res.json()
}
