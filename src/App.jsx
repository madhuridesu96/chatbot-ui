import { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState('loading...')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('error connecting to backend'))
  }, [])

  return (
    <div>
      <h1>Backend status: {status}</h1>
    </div>
  )
}

export default App