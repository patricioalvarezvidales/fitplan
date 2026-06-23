import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type View = 'landing' | 'auth' | 'profile' | 'dashboard' | 'history'
type AuthMode = 'login' | 'register'
type CatalogItem = { id: string; name: string; category?: string; body_area?: string }
type Me = { id: string; name: string; email: string; email_confirmed: boolean; profile_complete: boolean }
type Profile = {
  age: number; gender: string; weight_kg: number; height_cm: number; experience_level: string;
  primary_goal: string; training_location: string; available_days: number; session_minutes: number;
  equipment_ids: string[]; restriction_ids: string[]; equipment?: CatalogItem[]; restrictions?: CatalogItem[]
}
type Exercise = { id: string; name: string; description: string; primary_muscle: string; movement_pattern: string; difficulty_level: string; video_url: string; image_url: string; instructions: string }
type SessionExercise = { id: string; exercise_order: number; sets: number; repetitions: string; rest_seconds: number; target_rpe: number; notes: string; exercise: Exercise }
type PlanSession = { id: string; day_number: number; scheduled_date: string; name: string; estimated_minutes: number; focus: string; completed: boolean; exercises: SessionExercise[] }
type Plan = { id: string; name: string; goal: string; start_date: string; end_date: string; status: string; version: number; generation_reason: string; sessions: PlanSession[] }
type HistoryItem = { id: string; completed_at: string; actual_minutes: number; difficulty: number; energy_level: number; satisfaction: number; pain_reported: boolean; pain_area: string; comments: string; session_name: string; plan_name: string }

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
const emptyProfile: Profile = { age: 25, gender: '', weight_kg: 70, height_cm: 170, experience_level: 'principiante', primary_goal: 'ganancia_muscular', training_location: 'casa', available_days: 3, session_minutes: 45, equipment_ids: [], restriction_ids: [] }

function App() {
  const [view, setView] = useState<View>('landing')
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [token, setToken] = useState(localStorage.getItem('fitplan_token') ?? '')
  const [me, setMe] = useState<Me | null>(null)
  const [profile, setProfile] = useState<Profile>(emptyProfile)
  const [catalog, setCatalog] = useState<{ equipment: CatalogItem[]; restrictions: CatalogItem[] }>({ equipment: [], restrictions: [] })
  const [plan, setPlan] = useState<Plan | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeSession, setActiveSession] = useState<PlanSession | null>(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const api = async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: 'Error inesperado' }))
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Revisa los datos ingresados')
    }
    return response.status === 204 ? ({} as T) : response.json()
  }

  const loadApp = async () => {
    if (!token) return
    try {
      const user = await api<Me>('/auth/me')
      setMe(user)
      const cat = await api<{ equipment: CatalogItem[]; restrictions: CatalogItem[] }>('/catalog')
      setCatalog(cat)
      if (!user.profile_complete) {
        setView('profile')
        return
      }
      const currentProfile = await api<Profile>('/profile')
      setProfile(currentProfile)
      try {
        setPlan(await api<Plan>('/plans/current'))
      } catch {
        setPlan(null)
      }
      setView('dashboard')
    } catch {
      localStorage.removeItem('fitplan_token')
      setToken('')
      setView('auth')
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => { void loadApp() }, 0)
    return () => window.clearTimeout(timer)
    // loadApp intentionally reruns only when the persisted session changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const todaySession = useMemo(() => {
    if (!plan) return null
    const today = new Date().toISOString().slice(0, 10)
    return plan.sessions.find((session) => session.scheduled_date === today && !session.completed)
      ?? plan.sessions.find((session) => !session.completed)
      ?? plan.sessions[0]
  }, [plan])

  const run = async (action: () => Promise<void>) => {
    setLoading(true); setMessage('')
    try { await action() } catch (error) { setMessage(error instanceof Error ? error.message : 'Ocurrió un error') }
    finally { setLoading(false) }
  }

  const authSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const data = Object.fromEntries(new FormData(event.currentTarget))
    void run(async () => {
      if (authMode === 'register') {
        const registered = await api<{ confirmation_token: string }>('/auth/register', { method: 'POST', body: JSON.stringify(data) })
        await api(`/auth/confirm-email?token=${encodeURIComponent(registered.confirmation_token)}`, { method: 'POST' })
      }
      const logged = await api<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email: data.email, password: data.password }) })
      localStorage.setItem('fitplan_token', logged.access_token)
      setToken(logged.access_token)
    })
  }

  const saveProfile = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void run(async () => {
      await api('/profile', { method: 'PUT', body: JSON.stringify(profile) })
      const user = await api<Me>('/auth/me')
      setMe(user); setView('dashboard'); setMessage('Perfil guardado correctamente.')
    })
  }

  const generate = () => void run(async () => {
    const generated = await api<Plan>('/plans/generate', { method: 'POST' })
    setPlan(generated); setActiveSession(null); setMessage('Tu nueva semana fue generada con tus datos y retroalimentación.')
  })

  const loadHistory = (period = 'all') => void run(async () => {
    setHistory(await api<HistoryItem[]>(`/history?period=${period}`)); setView('history')
  })

  const completeSession = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!activeSession) return
    const form = new FormData(event.currentTarget)
    const payload = {
      actual_minutes: Number(form.get('actual_minutes')),
      difficulty: Number(form.get('difficulty')),
      energy_level: Number(form.get('energy_level')),
      satisfaction: Number(form.get('satisfaction')),
      pain_reported: form.get('pain_reported') === 'on',
      pain_area: String(form.get('pain_area') ?? ''),
      comments: String(form.get('comments') ?? ''),
    }
    void run(async () => {
      await api(`/sessions/${activeSession.id}/complete`, { method: 'POST', body: JSON.stringify(payload) })
      setPlan(await api<Plan>('/plans/current')); setActiveSession(null); setMessage('Entrenamiento completado. La próxima rutina usará esta información.')
    })
  }

  const logout = () => void run(async () => {
    try { await api('/auth/logout', { method: 'POST' }) } finally {
      localStorage.removeItem('fitplan_token'); setToken(''); setMe(null); setPlan(null); setView('landing')
    }
  })

  const toggle = (key: 'equipment_ids' | 'restriction_ids', id: string) => {
    setProfile((current) => ({ ...current, [key]: current[key].includes(id) ? current[key].filter((item) => item !== id) : [...current[key], id] }))
  }

  if (view === 'landing' && !token) return (
    <main className="landing">
      <nav className="navbar"><Brand /><span className="pill">MVP FUNCIONAL · DEVOPS</span></nav>
      <section className="hero"><p className="eyebrow">ENTRENA CON UN PLAN QUE APRENDE DE TI</p><h1>Tu semana de entrenamiento, <span>adaptada de verdad.</span></h1><p>FitPlan genera rutinas según tu objetivo, nivel, tiempo, equipo y restricciones. Después ajusta el volumen con tu dificultad, energía y molestias reales.</p><div className="actions"><button onClick={() => { setAuthMode('register'); setView('auth') }}>Crear mi plan</button><button className="secondary" onClick={() => { setAuthMode('login'); setView('auth') }}>Ya tengo cuenta</button></div></section>
      <section className="feature-grid">{['Perfil físico validado','Rutina semanal automática','Sesión del día guiada','Historial y adaptación'].map((item, index) => <article key={item}><b>0{index + 1}</b><h2>{item}</h2><p>{['Edad, peso, altura, nivel, disponibilidad, equipo y restricciones.','Series, repeticiones, descansos y medios visuales compatibles.','Ejercicios ordenados, técnica, RPE y registro único por sesión.','Filtros semanales o mensuales y progresión explicable.'][index]}</p></article>)}</section>
    </main>
  )

  if (view === 'auth') return (
    <main className="centered"><section className="auth-card"><Brand /><p className="eyebrow">{authMode === 'login' ? 'BIENVENIDO DE NUEVO' : 'CREA TU CUENTA'}</p><h1>{authMode === 'login' ? 'Inicia sesión' : 'Comienza tu evaluación'}</h1><form onSubmit={authSubmit}>{authMode === 'register' && <label>Nombre<input name="name" minLength={2} required /></label>}<label>Correo<input name="email" type="email" required /></label><label>Contraseña<input name="password" type="password" minLength={8} required /></label>{message && <p className="error">{message}</p>}<button disabled={loading}>{loading ? 'Procesando…' : authMode === 'login' ? 'Entrar' : 'Registrarme'}</button></form><button className="text-button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>{authMode === 'login' ? 'Crear una cuenta nueva' : 'Ya tengo una cuenta'}</button></section></main>
  )

  if (view === 'profile') return (
    <main><AppNav me={me} onDashboard={() => setView('dashboard')} onProfile={() => setView('profile')} onHistory={() => loadHistory()} onLogout={logout} /><section className="page-header"><p className="eyebrow">EVALUACIÓN INICIAL</p><h1>Cuéntanos cómo entrenas.</h1><p>Estos datos controlan el filtrado y la puntuación de ejercicios.</p></section><form className="profile-form" onSubmit={saveProfile}><div className="form-grid"><label>Edad<input type="number" min="16" max="90" value={profile.age} onChange={(e) => setProfile({ ...profile, age: +e.target.value })} required /></label><label>Género<select value={profile.gender} onChange={(e) => setProfile({ ...profile, gender: e.target.value })} required><option value="">Selecciona</option><option>mujer</option><option>hombre</option><option>no binario</option><option>prefiero no decir</option></select></label><label>Peso (kg)<input type="number" min="30" max="250" step="0.1" value={profile.weight_kg} onChange={(e) => setProfile({ ...profile, weight_kg: +e.target.value })} required /></label><label>Altura (cm)<input type="number" min="120" max="230" value={profile.height_cm} onChange={(e) => setProfile({ ...profile, height_cm: +e.target.value })} required /></label><label>Nivel<select value={profile.experience_level} onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })}><option value="principiante">Principiante</option><option value="intermedio">Intermedio</option><option value="avanzado">Avanzado</option></select></label><label>Objetivo<select value={profile.primary_goal} onChange={(e) => setProfile({ ...profile, primary_goal: e.target.value })}><option value="perdida_peso">Pérdida de peso</option><option value="ganancia_muscular">Ganancia muscular</option><option value="resistencia">Mejorar resistencia</option></select></label><label>Días por semana<input type="number" min="2" max="7" value={profile.available_days} onChange={(e) => setProfile({ ...profile, available_days: +e.target.value })} /></label><label>Minutos por sesión<input type="number" min="20" max="120" value={profile.session_minutes} onChange={(e) => setProfile({ ...profile, session_minutes: +e.target.value })} /></label></div><ChoiceGroup title="Equipo disponible" items={catalog.equipment} selected={profile.equipment_ids} onToggle={(id) => toggle('equipment_ids', id)} /><ChoiceGroup title="Restricciones o molestias" items={catalog.restrictions} selected={profile.restriction_ids} onToggle={(id) => toggle('restriction_ids', id)} /><p className="notice">FitPlan adapta ejercicios, pero no sustituye atención médica. Detén el entrenamiento ante dolor agudo.</p>{message && <p className="error">{message}</p>}<button disabled={loading}>{loading ? 'Guardando…' : 'Guardar perfil'}</button></form></main>
  )

  if (view === 'history') return (
    <main><AppNav me={me} onDashboard={() => setView('dashboard')} onProfile={() => setView('profile')} onHistory={() => loadHistory()} onLogout={logout} /><section className="page-header inline"><div><p className="eyebrow">PROGRESO</p><h1>Historial de entrenamientos</h1></div><div className="filters"><button onClick={() => loadHistory('week')}>7 días</button><button onClick={() => loadHistory('month')}>30 días</button><button onClick={() => loadHistory('all')}>Todo</button></div></section><section className="history-list">{history.length ? history.map((item) => <article key={item.id}><div><span>{new Date(item.completed_at).toLocaleDateString()}</span><h2>{item.session_name}</h2><p>{item.plan_name}</p></div><div className="metrics"><b>{item.actual_minutes} min</b><span>Dificultad {item.difficulty}/10</span><span>Energía {item.energy_level}/10</span><span>Satisfacción {item.satisfaction}/10</span>{item.pain_reported && <span className="pain">Molestia: {item.pain_area || 'reportada'}</span>}</div></article>) : <Empty title="Aún no hay sesiones completadas" text="Completa tu primera sesión para comenzar a medir tu constancia." />}</section></main>
  )

  return (
    <main><AppNav me={me} onDashboard={() => setView('dashboard')} onProfile={() => setView('profile')} onHistory={() => loadHistory()} onLogout={logout} /><section className="dashboard-head"><div><p className="eyebrow">HOLA, {me?.name.toUpperCase()}</p><h1>{plan ? plan.name : 'Tu plan empieza aquí'}</h1><p>{plan ? `Versión ${plan.version} · ${plan.generation_reason}` : 'Genera una semana completa con tus preferencias.'}</p></div><button onClick={generate} disabled={loading}>{loading ? 'Generando…' : plan ? 'Regenerar y adaptar' : 'Generar rutina semanal'}</button></section>{message && <p className="success">{message}</p>}{plan ? <><section className="today-card"><div><p className="eyebrow">SESIÓN RECOMENDADA</p><h2>{todaySession?.name}</h2><p>{todaySession?.estimated_minutes} min · {todaySession?.focus}</p></div>{todaySession && <button onClick={() => setActiveSession(todaySession)}>{todaySession.completed ? 'Ver sesión' : 'Comenzar sesión'}</button>}</section><section className="week-grid">{plan.sessions.map((session) => <button className={`day-card ${session.completed ? 'done' : ''}`} key={session.id} onClick={() => setActiveSession(session)}><span>{new Date(session.scheduled_date + 'T12:00:00').toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' })}</span><h3>{session.name}</h3><p>{session.exercises.length} ejercicios · {session.estimated_minutes} min</p><b>{session.completed ? '✓ Completado' : 'Ver entrenamiento →'}</b></button>)}</section></> : <Empty title="No tienes una rutina activa" text="Guarda tu perfil y genera tu primera semana personalizada." action="Generar ahora" onAction={generate} />}{activeSession && <SessionModal session={activeSession} onClose={() => setActiveSession(null)} onComplete={completeSession} />}</main>
  )
}

function Brand() { return <button className="brand" onClick={() => location.reload()}><span>ϟ</span>FITPLAN</button> }
function AppNav({ me, onDashboard, onProfile, onHistory, onLogout }: { me: Me | null; onDashboard: () => void; onProfile: () => void; onHistory: () => void; onLogout: () => void }) { return <nav className="navbar"><Brand /><div className="nav-links"><button onClick={onDashboard}>Mi semana</button><button onClick={onProfile}>Perfil</button><button onClick={onHistory}>Historial</button><span>{me?.name}</span><button onClick={onLogout}>Salir</button></div></nav> }
function ChoiceGroup({ title, items, selected, onToggle }: { title: string; items: CatalogItem[]; selected: string[]; onToggle: (id: string) => void }) { return <fieldset><legend>{title}</legend><div className="choice-grid">{items.map((item) => <label className={selected.includes(item.id) ? 'selected' : ''} key={item.id}><input type="checkbox" checked={selected.includes(item.id)} onChange={() => onToggle(item.id)} />{item.name.replace('_', ' ')}</label>)}</div></fieldset> }
function Empty({ title, text, action, onAction }: { title: string; text: string; action?: string; onAction?: () => void }) { return <section className="empty"><div className="empty-mark">ϟ</div><h2>{title}</h2><p>{text}</p>{action && <button onClick={onAction}>{action}</button>}</section> }
function SessionModal({ session, onClose, onComplete }: { session: PlanSession; onClose: () => void; onComplete: (event: FormEvent<HTMLFormElement>) => void }) { return <div className="modal-backdrop"><section className="modal"><button className="close" onClick={onClose}>×</button><p className="eyebrow">{session.completed ? 'SESIÓN COMPLETADA' : 'ENTRENAMIENTO GUIADO'}</p><h1>{session.name}</h1><p>{session.estimated_minutes} min · objetivo RPE {session.exercises[0]?.target_rpe ?? 7}</p><div className="exercise-list">{session.exercises.map((item) => <article key={item.id}><div className="media">{item.exercise.video_url ? <iframe src={item.exercise.video_url.replace('watch?v=', 'embed/')} title={item.exercise.name} allowFullScreen /> : <img src={item.exercise.image_url} alt={item.exercise.name} />}</div><div><span>#{item.exercise_order} · {item.exercise.primary_muscle}</span><h2>{item.exercise.name}</h2><p>{item.exercise.description}</p><b>{item.sets} series · {item.repetitions} · descanso {item.rest_seconds}s</b><small>{item.exercise.instructions}</small></div></article>)}</div>{!session.completed && <form className="feedback" onSubmit={onComplete}><h2>Finalizar y registrar</h2><div className="form-grid"><label>Minutos reales<input name="actual_minutes" type="number" min="5" max="240" defaultValue={session.estimated_minutes} required /></label><label>Dificultad (1-10)<input name="difficulty" type="number" min="1" max="10" defaultValue="7" required /></label><label>Energía (1-10)<input name="energy_level" type="number" min="1" max="10" defaultValue="7" required /></label><label>Satisfacción (1-10)<input name="satisfaction" type="number" min="1" max="10" defaultValue="8" required /></label></div><label className="check"><input name="pain_reported" type="checkbox" /> Sentí dolor o molestia</label><label>Área de molestia<input name="pain_area" placeholder="Ej. rodilla derecha" /></label><label>Comentarios<textarea name="comments" rows={3} placeholder="¿Qué fue fácil, difícil o incómodo?" /></label><button>Marcar entrenamiento como completado</button></form>}</section></div> }

export default App
