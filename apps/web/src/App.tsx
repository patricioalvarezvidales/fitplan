import { useEffect, useState } from 'react'
import './App.css'

type ApiState = 'checking' | 'online' | 'offline'

const features = [
  {
    title: 'Plan semanal personalizado',
    text: 'Genera sesiones según tu objetivo, nivel, disponibilidad y equipo.',
    accent: 'lime',
  },
  {
    title: 'Adaptación por progreso',
    text: 'Ajusta las próximas sesiones usando esfuerzo, cumplimiento y sensaciones.',
    accent: 'orange',
  },
  {
    title: 'Videos con respaldo visual',
    text: 'Cada ejercicio acepta video y utiliza una imagen cuando el video no está disponible.',
    accent: 'cyan',
  },
  {
    title: 'Historial útil',
    text: 'Registra entrenamientos y convierte la retroalimentación en decisiones explicables.',
    accent: 'violet',
  },
]

function App() {
  const [apiState, setApiState] = useState<ApiState>('checking')
  const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

  useEffect(() => {
    const controller = new AbortController()

    fetch(`${apiUrl}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error('API unavailable')
        setApiState('online')
      })
      .catch(() => setApiState('offline'))

    return () => controller.abort()
  }, [apiUrl])

  return (
    <main>
      <nav className="navbar">
        <a className="brand" href="#top" aria-label="FitPlan inicio">
          <span className="brand-mark">ϟ</span>
          <span>FITPLAN</span>
        </a>
        <span className={`api-status ${apiState}`}>
          <span className="status-dot" />
          API {apiState === 'checking' ? 'verificando' : apiState === 'online' ? 'conectada' : 'sin conexión'}
        </span>
      </nav>

      <section className="hero" id="top">
        <p className="eyebrow">PROTOTIPO DEVOPS · 2026</p>
        <h1>
          Un plan de entrenamiento que <span>evoluciona contigo.</span>
        </h1>
        <p className="hero-copy">
          FitPlan crea una semana inicial y adapta cada sesión al tiempo, equipo, progreso y
          sensaciones del usuario, con reglas claras y verificables.
        </p>
        <div className="actions">
          <button type="button">Comenzar evaluación</button>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            Ver API
          </a>
        </div>
      </section>

      <section className="feature-grid" aria-label="Funciones principales">
        {features.map((feature) => (
          <article className={`feature-card ${feature.accent}`} key={feature.title}>
            <div className="feature-line" />
            <h2>{feature.title}</h2>
            <p>{feature.text}</p>
          </article>
        ))}
      </section>

      <section className="method">
        <div>
          <p className="eyebrow">MOTOR RECOMENDADO</p>
          <h2>Reglas + restricciones + puntuación</h2>
        </div>
        <ol>
          <li>Filtrar ejercicios incompatibles con equipo o restricciones.</li>
          <li>Puntuar alternativas por objetivo, nivel y preferencia.</li>
          <li>Construir la sesión dentro del tiempo disponible.</li>
          <li>Adaptar la siguiente semana con retroalimentación real.</li>
        </ol>
      </section>
    </main>
  )
}

export default App
