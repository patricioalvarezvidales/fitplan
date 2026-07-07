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
type Exercise = { id: string; name: string; description: string; primary_muscle: string; movement_pattern: string; difficulty_level: string; video_url: string; image_url: string; instructions: string; load_type: string }
type SessionExercise = { id: string; exercise_order: number; sets: number; repetitions: string; rest_seconds: number; target_rpe: number; recommended_weight_kg: number; notes: string; exercise: Exercise }
type PlanSession = { id: string; day_number: number; scheduled_date: string; name: string; estimated_minutes: number; focus: string; completed: boolean; exercises: SessionExercise[] }
type Plan = { id: string; name: string; goal: string; start_date: string; end_date: string; status: string; version: number; generation_reason: string; sessions: PlanSession[] }
type ExerciseHistory = { exercise_name: string; recommended_weight_kg: number; actual_weight_kg: number; completed_sets: number; completed_repetitions: string }
type HistoryItem = { id: string; completed_at: string; actual_minutes: number; difficulty: number; energy_level: number; satisfaction: number; pain_reported: boolean; pain_area: string; comments: string; session_name: string; plan_name: string; exercises: ExerciseHistory[] }

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
const emptyProfile: Profile = { age: 25, gender: '', weight_kg: 70, height_cm: 170, experience_level: 'principiante', primary_goal: 'ganancia_muscular', training_location: 'casa', available_days: 3, session_minutes: 45, equipment_ids: [], restriction_ids: [] }

type WeightUnit = 'kg' | 'lb'
const KG_TO_LB = 2.2046226218
const toDisplayWeight = (kg: number, unit: WeightUnit) => unit === 'lb' ? Number((kg * KG_TO_LB).toFixed(1)) : Number(kg.toFixed(1))
const toKilograms = (value: number, unit: WeightUnit) => unit === 'lb' ? Number((value / KG_TO_LB).toFixed(2)) : value

function App() {
  const [view, setView] = useState<View>('landing')
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [token, setToken] = useState(localStorage.getItem('fitplan_token') ?? '')
  const [me, setMe] = useState<Me | null>(null)
  const [profile, setProfile] = useState<Profile>(emptyProfile)
  const [catalog, setCatalog] = useState<{ equipment: CatalogItem[]; restrictions: CatalogItem[] }>({ equipment: [], restrictions: [] })
  const [plans, setPlans] = useState<Plan[]>([])
  const [selectedPlanId, setSelectedPlanId] = useState('')
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

  const selectedPlan = useMemo(
    () => plans.find((item) => item.id === selectedPlanId) ?? plans.at(-1) ?? null,
    [plans, selectedPlanId],
  )

  const selectedPlanIndex = selectedPlan ? plans.findIndex((item) => item.id === selectedPlan.id) : -1

  const todaySession = useMemo(() => {
    if (!selectedPlan) return null
    const today = new Date().toISOString().slice(0, 10)
    return selectedPlan.sessions.find((session) => session.scheduled_date === today && !session.completed)
      ?? selectedPlan.sessions.find((session) => !session.completed)
      ?? selectedPlan.sessions[0]
      ?? null
  }, [selectedPlan])

  const loadPlans = async () => {
    const all = await api<Plan[]>('/plans')
    setPlans(all)
    if (all.length) {
      const current = all.find((item) => item.status === 'active') ?? all.at(-1)!
      setSelectedPlanId((existing) => existing && all.some((item) => item.id === existing) ? existing : current.id)
    }
  }

  const loadApp = async () => {
    if (!token) return
    try {
      const user = await api<Me>('/auth/me')
      setMe(user)
      setCatalog(await api('/catalog'))
      if (!user.profile_complete) {
        setView('profile')
        return
      }
      setProfile(await api('/profile'))
      await loadPlans()
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const authSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setLoading(true); setMessage('')
    const form = new FormData(event.currentTarget)
    try {
      if (authMode === 'register') {
        const registered = await api<{ confirmation_token: string }>('/auth/register', { method: 'POST', body: JSON.stringify({ name: form.get('name'), email: form.get('email'), password: form.get('password') }) })
        await api(`/auth/confirm-email?token=${encodeURIComponent(registered.confirmation_token)}`, { method: 'POST' })
      }
      const logged = await api<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email: form.get('email'), password: form.get('password') }) })
      localStorage.setItem('fitplan_token', logged.access_token); setToken(logged.access_token)
    } catch (error) { setMessage((error as Error).message) } finally { setLoading(false) }
  }

  const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setLoading(true); setMessage('')
    try {
      await api('/profile', { method: 'PUT', body: JSON.stringify(profile) })
      const user = await api<Me>('/auth/me'); setMe(user); setView('dashboard'); setMessage('Perfil guardado correctamente.')
      await loadPlans()
    } catch (error) { setMessage((error as Error).message) } finally { setLoading(false) }
  }

  const generate = async () => {
    setLoading(true); setMessage('')
    try {
      const created = await api<Plan>('/plans/generate', { method: 'POST' })
      await loadPlans(); setSelectedPlanId(created.id); setMessage('Nueva semana creada. Las semanas anteriores siguen disponibles.')
    } catch (error) { setMessage((error as Error).message) } finally { setLoading(false) }
  }

  const loadHistory = async (period = 'all') => {
    setHistory(await api<HistoryItem[]>(`/history?period=${period}`)); setView('history')
  }

  const completeSession = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!activeSession) return
    setLoading(true); setMessage('')
    const form = new FormData(event.currentTarget)
    const payload = {
      actual_minutes: Number(form.get('actual_minutes')),
      difficulty: Number(form.get('difficulty')),
      energy_level: Number(form.get('energy_level')),
      satisfaction: Number(form.get('satisfaction')),
      pain_reported: form.get('pain_reported') === 'on',
      pain_area: String(form.get('pain_area') ?? ''),
      comments: String(form.get('comments') ?? ''),
      exercises: activeSession.exercises.map((item) => {
        const unit = String(form.get('weight_unit') ?? 'kg') as WeightUnit
        return {
          session_exercise_id: item.id,
          actual_weight_kg: toKilograms(Number(form.get(`weight_${item.id}`) ?? 0), unit),
          completed_sets: Number(form.get(`sets_${item.id}`) ?? item.sets),
          completed_repetitions: String(form.get(`reps_${item.id}`) ?? item.repetitions),
        }
      }),
    }
    try {
      await api(`/sessions/${activeSession.id}/complete`, { method: 'POST', body: JSON.stringify(payload) })
      setActiveSession(null); await loadPlans(); setMessage('Entrenamiento registrado. La próxima recomendación usará este resultado.')
    } catch (error) { setMessage((error as Error).message) } finally { setLoading(false) }
  }

  const logout = async () => {
    try { await api('/auth/logout', { method: 'POST' }) } catch { /* sesión local se elimina igualmente */ }
    localStorage.removeItem('fitplan_token'); setToken(''); setMe(null); setPlans([]); setView('landing')
  }

  const toggle = (key: 'equipment_ids' | 'restriction_ids', id: string) => {
    setProfile((current) => ({ ...current, [key]: current[key].includes(id) ? current[key].filter((item) => item !== id) : [...current[key], id] }))
  }

  if (view === 'landing' && !token) return (
    <main className="landing"><nav className="navbar"><Brand /><button onClick={() => setView('auth')}>Iniciar sesión</button></nav><section className="hero"><p className="eyebrow">PLANES QUE EVOLUCIONAN CONTIGO</p><h1>Entrena con estructura.<br />Progresa con intención.</h1><p>FitPlan crea una semana personalizada y adapta volumen, ejercicios y cargas con base en tu desempeño.</p><button className="primary-action" onClick={() => { setAuthMode('register'); setView('auth') }}>Crear mi plan</button></section></main>
  )

  if (view === 'auth') return (
    <main className="auth-page"><nav className="navbar"><Brand /></nav><section className="auth-card"><p className="eyebrow">{authMode === 'login' ? 'BIENVENIDO DE NUEVO' : 'CREA TU CUENTA'}</p><h1>{authMode === 'login' ? 'Inicia sesión' : 'Comienza tu evaluación'}</h1><form onSubmit={authSubmit}>{authMode === 'register' && <label>Nombre<input name="name" minLength={2} required /></label>}<label>Correo<input name="email" type="email" required /></label><label>Contraseña<input name="password" type="password" minLength={8} required /></label>{message && <p className="error">{message}</p>}<button className="primary-action" disabled={loading}>{loading ? 'Procesando…' : authMode === 'login' ? 'Entrar' : 'Registrarme'}</button></form><button className="text-button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>{authMode === 'login' ? 'Crear una cuenta nueva' : 'Ya tengo una cuenta'}</button></section></main>
  )

  if (view === 'profile') return (
    <main><AppNav me={me} onDashboard={() => setView('dashboard')} onProfile={() => setView('profile')} onHistory={() => loadHistory()} onLogout={logout} /><section className="page-header"><p className="eyebrow">EVALUACIÓN INICIAL</p><h1>Cuéntanos cómo entrenas.</h1><p>Estos datos controlan el filtrado y la puntuación de ejercicios.</p></section><form className="profile-form" onSubmit={saveProfile}><div className="form-grid"><label>Edad<input type="number" min="16" max="90" value={profile.age} onChange={(e) => setProfile({ ...profile, age: +e.target.value })} required /></label><label>Género<select value={profile.gender} onChange={(e) => setProfile({ ...profile, gender: e.target.value })} required><option value="">Selecciona</option><option>mujer</option><option>hombre</option><option>no binario</option><option>prefiero no decir</option></select></label><label>Peso (kg)<input type="number" min="30" max="250" step="0.1" value={profile.weight_kg} onChange={(e) => setProfile({ ...profile, weight_kg: +e.target.value })} required /></label><label>Altura (cm)<input type="number" min="120" max="230" value={profile.height_cm} onChange={(e) => setProfile({ ...profile, height_cm: +e.target.value })} required /></label><label>Nivel<select value={profile.experience_level} onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })}><option value="principiante">Principiante</option><option value="intermedio">Intermedio</option><option value="avanzado">Avanzado</option></select></label><label>Objetivo<select value={profile.primary_goal} onChange={(e) => setProfile({ ...profile, primary_goal: e.target.value })}><option value="perdida_peso">Pérdida de peso</option><option value="ganancia_muscular">Ganancia muscular</option><option value="resistencia">Mejorar resistencia</option></select></label><label>Días por semana<input type="number" min="2" max="7" value={profile.available_days} onChange={(e) => setProfile({ ...profile, available_days: +e.target.value })} /></label><label>Minutos por sesión<input type="number" min="20" max="120" value={profile.session_minutes} onChange={(e) => setProfile({ ...profile, session_minutes: +e.target.value })} /></label></div><ChoiceGroup title="Equipo disponible" items={catalog.equipment} selected={profile.equipment_ids} onToggle={(id) => toggle('equipment_ids', id)} /><ChoiceGroup title="Restricciones o molestias" items={catalog.restrictions} selected={profile.restriction_ids} onToggle={(id) => toggle('restriction_ids', id)} /><p className="notice">FitPlan adapta ejercicios, pero no sustituye atención médica. Detén el entrenamiento ante dolor agudo.</p>{message && <p className="error">{message}</p>}<button className="primary-action" disabled={loading}>{loading ? 'Guardando…' : 'Guardar perfil'}</button></form></main>
  )

  if (view === 'history') return (
    <main><AppNav me={me} onDashboard={() => setView('dashboard')} onProfile={() => setView('profile')} onHistory={() => loadHistory()} onLogout={logout} /><section className="page-header inline"><div><p className="eyebrow">PROGRESO</p><h1>Historial de entrenamientos</h1></div><div className="filters"><button onClick={() => loadHistory('week')}>7 días</button><button onClick={() => loadHistory('month')}>30 días</button><button onClick={() => loadHistory('all')}>Todo</button></div></section><HistoryCalendar history={history} /></main>
  )

  return (
    <main><AppNav me={me} onDashboard={() => setView('dashboard')} onProfile={() => setView('profile')} onHistory={() => loadHistory()} onLogout={logout} /><section className="dashboard-head"><div><p className="eyebrow">HOLA, {me?.name.toUpperCase()}</p><h1>{selectedPlan ? selectedPlan.name : 'Tu plan empieza aquí'}</h1><p>{selectedPlan ? `Versión ${selectedPlan.version} · ${selectedPlan.generation_reason}` : 'Genera una semana completa con tus preferencias.'}</p></div><button className="primary-action" onClick={generate} disabled={loading}>{loading ? 'Generando…' : selectedPlan ? 'Regenerar y adaptar' : 'Generar rutina semanal'}</button></section>{message && <p className="success">{message}</p>}{selectedPlan ? <><WeekNavigator plans={plans} currentIndex={selectedPlanIndex} onSelect={setSelectedPlanId} /><section className="today-card"><div><p className="eyebrow">SESIÓN RECOMENDADA</p><h2>{todaySession?.name}</h2><p>{todaySession?.estimated_minutes} min · {todaySession?.focus}</p></div>{todaySession && <button className="primary-action" onClick={() => setActiveSession(todaySession)}>{todaySession.completed ? 'Ver sesión' : 'Comenzar sesión'}</button>}</section><section className="week-grid">{selectedPlan.sessions.map((session) => <button className={`day-card ${session.completed ? 'done' : ''}`} key={session.id} onClick={() => setActiveSession(session)}><span>{new Date(session.scheduled_date + 'T12:00:00').toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' })}</span><h3>{session.name}</h3><p>{session.exercises.length} ejercicios · {session.estimated_minutes} min</p><b>{session.completed ? '✓ Completado' : 'Ver entrenamiento →'}</b></button>)}</section></> : <Empty title="No tienes una rutina activa" text="Guarda tu perfil y genera tu primera semana personalizada." action="Generar ahora" onAction={generate} />}{activeSession && <SessionModal session={activeSession} onClose={() => setActiveSession(null)} onComplete={completeSession} />}</main>
  )
}

function Brand() { return <button className="brand" onClick={() => location.reload()} aria-label="Ir al inicio de FitPlan"><img src="/favicon.svg" alt="" /><span>FitPlan</span></button> }
function AppNav({ me, onDashboard, onProfile, onHistory, onLogout }: { me: Me | null; onDashboard: () => void; onProfile: () => void; onHistory: () => void; onLogout: () => void }) { return <nav className="navbar"><Brand /><div className="nav-links"><button onClick={onDashboard}>Mi semana</button><button onClick={onProfile}>Perfil</button><button onClick={onHistory}>Historial</button><span>{me?.name}</span><button onClick={onLogout}>Salir</button></div></nav> }
function ChoiceGroup({ title, items, selected, onToggle }: { title: string; items: CatalogItem[]; selected: string[]; onToggle: (id: string) => void }) { return <fieldset><legend>{title}</legend><div className="choice-grid">{items.map((item) => <label className={selected.includes(item.id) ? 'selected' : ''} key={item.id}><input type="checkbox" checked={selected.includes(item.id)} onChange={() => onToggle(item.id)} />{item.name.replace('_', ' ')}</label>)}</div></fieldset> }
function Empty({ title, text, action, onAction }: { title: string; text: string; action?: string; onAction?: () => void }) { return <section className="empty"><div className="empty-mark">ϟ</div><h2>{title}</h2><p>{text}</p>{action && <button className="primary-action" onClick={onAction}>{action}</button>}</section> }

function WeekNavigator({ plans, currentIndex, onSelect }: { plans: Plan[]; currentIndex: number; onSelect: (id: string) => void }) {
  const previous = currentIndex > 0 ? plans[currentIndex - 1] : null
  const next = currentIndex >= 0 && currentIndex < plans.length - 1 ? plans[currentIndex + 1] : null
  return <section className="week-navigator"><button disabled={!previous} onClick={() => previous && onSelect(previous.id)}>← Semana anterior</button><select value={plans[currentIndex]?.id ?? ''} onChange={(event) => onSelect(event.target.value)}>{plans.map((item) => <option key={item.id} value={item.id}>{item.name}{item.status === 'active' ? ' · actual' : ''}</option>)}</select><button disabled={!next} onClick={() => next && onSelect(next.id)}>Semana siguiente →</button></section>
}

function SessionModal({ session, onClose, onComplete }: { session: PlanSession; onClose: () => void; onComplete: (event: FormEvent<HTMLFormElement>) => void }) {
  const [weightUnit, setWeightUnit] = useState<WeightUnit>('kg')
  const [weights, setWeights] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      session.exercises
        .filter((item) => item.exercise.load_type === 'external')
        .map((item) => [
          item.id,
          String(toDisplayWeight(item.recommended_weight_kg, 'kg')),
        ]),
    ),
  )

  const changeWeightUnit = (nextUnit: WeightUnit) => {
    if (nextUnit === weightUnit) return

    setWeights((current) =>
      Object.fromEntries(
        Object.entries(current).map(([id, value]) => {
          if (value.trim() === '') return [id, value]

          const numericValue = Number(value)
          if (!Number.isFinite(numericValue)) return [id, value]

          const kilograms = toKilograms(numericValue, weightUnit)
          return [
            id,
            String(toDisplayWeight(kilograms, nextUnit)),
          ]
        }),
      ),
    )

    setWeightUnit(nextUnit)
  }

  const updateWeight = (id: string, value: string) => {
    setWeights((current) => ({
      ...current,
      [id]: value,
    }))
  }

  return (
    <div className="modal-backdrop">
      <section className="modal">
        <button className="close" type="button" onClick={onClose}>×</button>

        <div className="session-modal-head">
          <div>
            <p className="eyebrow">
              {session.completed ? 'SESIÓN COMPLETADA' : 'ENTRENAMIENTO GUIADO'}
            </p>
            <h1>{session.name}</h1>
            <p>
              {session.estimated_minutes} min · objetivo RPE{' '}
              {session.exercises[0]?.target_rpe ?? 7}
            </p>
          </div>

          <label className="unit-switch">
            Unidad
            <select
              value={weightUnit}
              onChange={(event) =>
                changeWeightUnit(event.target.value as WeightUnit)
              }
              disabled={session.completed}
            >
              <option value="kg">kg</option>
              <option value="lb">lb</option>
            </select>
          </label>
        </div>

        <form onSubmit={onComplete}>
          <input type="hidden" name="weight_unit" value={weightUnit} />

          <div className="exercise-list">
            {session.exercises.map((item) => (
              <article key={item.id}>
                <div className="media">
                  {item.exercise.video_url ? (
                    <iframe
                      src={item.exercise.video_url.replace('watch?v=', 'embed/')}
                      title={item.exercise.name}
                      allowFullScreen
                    />
                  ) : (
                    <img
                      src={item.exercise.image_url}
                      alt={item.exercise.name}
                    />
                  )}
                </div>

                <div className="exercise-content">
                  <span>
                    #{item.exercise_order} · {item.exercise.primary_muscle}
                  </span>
                  <h2>{item.exercise.name}</h2>
                  <p>{item.exercise.description}</p>
                  <b>
                    {item.sets} series · {item.repetitions} · descanso{' '}
                    {item.rest_seconds}s
                  </b>

                  {item.exercise.load_type === 'external' && (
                    <div className="load-box">
                      <span>
                        Recomendado:{' '}
                        <strong>
                          {toDisplayWeight(
                            item.recommended_weight_kg,
                            weightUnit,
                          )}{' '}
                          {weightUnit}
                        </strong>
                      </span>

                      <label>
                        Peso usado ({weightUnit})
                        <input
                          name={`weight_${item.id}`}
                          type="number"
                          min="0"
                          max={weightUnit === 'kg' ? 1000 : 2205}
                          step={weightUnit === 'kg' ? '0.5' : '0.1'}
                          value={weights[item.id] ?? ''}
                          onChange={(event) =>
                            updateWeight(item.id, event.target.value)
                          }
                          disabled={session.completed}
                        />
                      </label>
                    </div>
                  )}

                  <div className="set-log">
                    <label>
                      Series realizadas
                      <input
                        name={`sets_${item.id}`}
                        type="number"
                        min="0"
                        max="20"
                        defaultValue={item.sets}
                        disabled={session.completed}
                      />
                    </label>

                    <label>
                      Repeticiones
                      <input
                        name={`reps_${item.id}`}
                        defaultValue={item.repetitions}
                        disabled={session.completed}
                      />
                    </label>
                  </div>

                  <small>{item.exercise.instructions}</small>
                </div>
              </article>
            ))}
          </div>

          {!session.completed && (
            <section className="feedback">
              <h2>Finalizar y registrar</h2>

              <div className="form-grid">
                <label>
                  Minutos reales
                  <input
                    name="actual_minutes"
                    type="number"
                    min="5"
                    max="240"
                    defaultValue={session.estimated_minutes}
                    required
                  />
                </label>

                <label>
                  Dificultad (1-10)
                  <input
                    name="difficulty"
                    type="number"
                    min="1"
                    max="10"
                    defaultValue="7"
                    required
                  />
                </label>

                <label>
                  Energía (1-10)
                  <input
                    name="energy_level"
                    type="number"
                    min="1"
                    max="10"
                    defaultValue="7"
                    required
                  />
                </label>

                <label>
                  Satisfacción (1-10)
                  <input
                    name="satisfaction"
                    type="number"
                    min="1"
                    max="10"
                    defaultValue="8"
                    required
                  />
                </label>
              </div>

              <label className="check">
                <input name="pain_reported" type="checkbox" />
                Sentí dolor o molestia
              </label>

              <label>
                Área de molestia
                <input
                  name="pain_area"
                  placeholder="Ej. rodilla derecha"
                />
              </label>

              <label>
                Comentarios
                <textarea
                  name="comments"
                  rows={3}
                  placeholder="¿Qué fue fácil, difícil o incómodo?"
                />
              </label>

              <button className="primary-action">
                Marcar entrenamiento como completado
              </button>
            </section>
          )}
        </form>
      </section>
    </div>
  )
}

function HistoryCalendar({ history }: { history: HistoryItem[] }) {
  const [weightUnit, setWeightUnit] = useState<WeightUnit>('kg')
  const [cursor, setCursor] = useState(() => { const now = new Date(); return new Date(now.getFullYear(), now.getMonth(), 1) })
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10))
  const byDay = useMemo(() => {
    const map = new Map<string, HistoryItem[]>()
    history.forEach((item) => {
      const key = new Date(item.completed_at).toLocaleDateString('en-CA')
      map.set(key, [...(map.get(key) ?? []), item])
    })
    return map
  }, [history])
  const year = cursor.getFullYear(); const month = cursor.getMonth()
  const firstWeekday = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells = Array.from({ length: 42 }, (_, index) => {
    const day = index - firstWeekday + 1
    return day >= 1 && day <= daysInMonth ? day : null
  })
  const selectedItems = byDay.get(selectedDate) ?? []
  return <section className="history-layout"><article className="calendar-card"><div className="calendar-head"><button onClick={() => setCursor(new Date(year, month - 1, 1))}>←</button><h2>{cursor.toLocaleDateString('es-MX', { month: 'long', year: 'numeric' })}</h2><button onClick={() => setCursor(new Date(year, month + 1, 1))}>→</button></div><div className="calendar-weekdays">{['D', 'L', 'M', 'M', 'J', 'V', 'S'].map((day, index) => <span key={`${day}-${index}`}>{day}</span>)}</div><div className="calendar-grid">{cells.map((day, index) => {
    if (!day) return <span key={`empty-${index}`} />
    const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const trained = byDay.has(key)
    return <button key={key} className={`${trained ? 'trained' : ''} ${selectedDate === key ? 'selected-day' : ''}`} onClick={() => setSelectedDate(key)}><span>{day}</span>{trained && <i />}</button>
  })}</div></article><section className="history-list calendar-detail"><div className="history-toolbar"><span>Cargas registradas</span><label className="unit-switch compact">Unidad<select value={weightUnit} onChange={(event) => setWeightUnit(event.target.value as WeightUnit)}><option value="kg">kg</option><option value="lb">lb</option></select></label></div>{selectedItems.length ? selectedItems.map((item) => <article key={item.id}><div className="history-main"><span>{new Date(item.completed_at).toLocaleDateString('es-MX')}</span><h2>{item.session_name}</h2><p>{item.plan_name}</p><details className="load-history"><summary><span>Ver cargas registradas</span><span aria-hidden="true">⌄</span></summary><div className="load-history-grid">{item.exercises.map((exercise) => <div className="load-history-row" key={exercise.exercise_name}><div><strong>{exercise.exercise_name}</strong><small>{exercise.completed_sets} series · {exercise.completed_repetitions} reps</small></div><b>{toDisplayWeight(exercise.actual_weight_kg, weightUnit)} {weightUnit}</b></div>)}</div></details></div><div className="metrics"><b>{item.actual_minutes} min</b><span>Dificultad {item.difficulty}/10</span><span>Energía {item.energy_level}/10</span><span>Satisfacción {item.satisfaction}/10</span>{item.pain_reported && <span className="pain">Molestia: {item.pain_area || 'reportada'}</span>}</div></article>) : <Empty title="Sin entrenamiento ese día" text="Selecciona un día marcado para revisar la sesión y las cargas utilizadas." />}</section></section>
}

export default App
