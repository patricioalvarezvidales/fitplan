from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Equipment, Exercise, Restriction

EQUIPMENT = [
    ("ninguno", "peso corporal"), ("mancuernas", "fuerza"), ("barra", "fuerza"),
    ("bandas", "resistencia"), ("banco", "fuerza"), ("caminadora", "cardio"),
]
RESTRICTIONS = [
    ("rodilla", "rodillas", "Evitar impacto y flexión profunda si causa dolor."),
    ("espalda_baja", "espalda", "Evitar cargas axiales o flexión lumbar dolorosa."),
    ("hombro", "hombros", "Evitar movimientos por encima de la cabeza con dolor."),
    ("muñeca", "muñecas", "Evitar apoyo prolongado o extensión dolorosa."),
]
EXERCISES = [
    ("Sentadilla al aire", "Piernas y glúteos con peso corporal.", "piernas", "sentadilla", "principiante", "perdida_peso,ganancia_muscular,resistencia", "ninguno", "rodilla", "https://www.youtube.com/watch?v=aclHkVaku9U", "https://images.unsplash.com/photo-1574680096145-d05b474e2155?auto=format&fit=crop&w=900&q=80", "Pies al ancho de hombros, cadera atrás y pecho alto."),
    ("Puente de glúteo", "Fortalece glúteos y cadena posterior.", "gluteos", "bisagra", "principiante", "ganancia_muscular,resistencia", "ninguno", "", "https://www.youtube.com/watch?v=wPM8icPu6H8", "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=900&q=80", "Empuja con los talones y contrae glúteos arriba."),
    ("Flexiones inclinadas", "Empuje de tren superior adaptable.", "pecho", "empuje", "principiante", "ganancia_muscular,resistencia", "ninguno", "hombro,muñeca", "https://www.youtube.com/watch?v=cfns5VDVVvk", "https://images.unsplash.com/photo-1598971639058-a4574a57c94e?auto=format&fit=crop&w=900&q=80", "Mantén el cuerpo alineado y controla el descenso."),
    ("Remo con mancuerna", "Tracción para espalda y bíceps.", "espalda", "traccion", "intermedio", "ganancia_muscular", "mancuernas", "espalda_baja", "https://www.youtube.com/watch?v=pYcpY20QaE8", "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?auto=format&fit=crop&w=900&q=80", "Apoya una mano y lleva el codo hacia la cadera."),
    ("Press de hombro con mancuernas", "Empuje vertical controlado.", "hombros", "empuje", "intermedio", "ganancia_muscular", "mancuernas", "hombro", "https://www.youtube.com/watch?v=qEwKCR5JCog", "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=900&q=80", "No arquees la espalda; controla todo el recorrido."),
    ("Peso muerto rumano con mancuernas", "Bisagra de cadera para femorales.", "femorales", "bisagra", "intermedio", "ganancia_muscular", "mancuernas", "espalda_baja", "https://www.youtube.com/watch?v=JCXUYuzwNrM", "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?auto=format&fit=crop&w=900&q=80", "Cadera atrás, espalda neutra y mancuernas cerca del cuerpo."),
    ("Zancada asistida", "Trabajo unilateral de piernas.", "piernas", "zancada", "intermedio", "ganancia_muscular,resistencia", "ninguno", "rodilla", "https://www.youtube.com/watch?v=QOVaHwm-Q6U", "https://images.unsplash.com/photo-1434682881908-b43d0467b798?auto=format&fit=crop&w=900&q=80", "Da un paso cómodo y mantén la rodilla alineada."),
    ("Plancha de antebrazos", "Estabilidad del tronco.", "core", "estabilidad", "principiante", "perdida_peso,ganancia_muscular,resistencia", "ninguno", "hombro", "https://www.youtube.com/watch?v=pSHjTRCQxIw", "https://images.unsplash.com/photo-1566241142559-40e1dab266c6?auto=format&fit=crop&w=900&q=80", "Aprieta abdomen y glúteos sin hundir la cadera."),
    ("Dead bug", "Control de core con bajo impacto.", "core", "estabilidad", "principiante", "resistencia,perdida_peso", "ninguno", "", "https://www.youtube.com/watch?v=g_BYB0R-4Ws", "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=900&q=80", "Mantén la espalda baja en contacto con el piso."),
    ("Mountain climbers", "Cardio de cuerpo completo.", "cardio", "cardio", "intermedio", "perdida_peso,resistencia", "ninguno", "rodilla,muñeca", "https://www.youtube.com/watch?v=nmwgirgXLYM", "https://images.unsplash.com/photo-1574680096145-d05b474e2155?auto=format&fit=crop&w=900&q=80", "Alterna rodillas con ritmo y tronco estable."),
    ("Marcha rápida", "Cardio sin equipo y bajo impacto.", "cardio", "cardio", "principiante", "perdida_peso,resistencia", "ninguno", "", "", "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=900&q=80", "Mantén ritmo constante y balancea los brazos."),
    ("Caminata en caminadora", "Cardio progresivo y medible.", "cardio", "cardio", "principiante", "perdida_peso,resistencia", "caminadora", "", "", "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?auto=format&fit=crop&w=900&q=80", "Usa una velocidad sostenible y postura erguida."),
    ("Curl de bíceps", "Aislamiento de bíceps.", "biceps", "traccion", "principiante", "ganancia_muscular", "mancuernas", "", "https://www.youtube.com/watch?v=ykJmrZ5v0Oo", "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?auto=format&fit=crop&w=900&q=80", "Codos pegados al cuerpo y sin impulso."),
    ("Remo con banda", "Tracción horizontal con banda.", "espalda", "traccion", "principiante", "ganancia_muscular,resistencia", "bandas", "", "", "https://images.unsplash.com/photo-1598289431512-b97b0917affc?auto=format&fit=crop&w=900&q=80", "Junta escápulas y controla el regreso."),
]


def seed_catalog(db: Session) -> None:
    if db.scalar(select(func.count(Equipment.id))) == 0:
        db.add_all([Equipment(name=n, category=c) for n, c in EQUIPMENT])
    if db.scalar(select(func.count(Restriction.id))) == 0:
        db.add_all([Restriction(name=n, body_area=a, description=d) for n, a, d in RESTRICTIONS])
    if db.scalar(select(func.count(Exercise.id))) == 0:
        db.add_all([
            Exercise(name=n, description=d, primary_muscle=m, movement_pattern=p,
                     difficulty_level=level, goal_tags=g, equipment_name=e, restriction_tags=r,
                     video_url=v, image_url=i, instructions=ins)
            for n, d, m, p, level, g, e, r, v, i, ins in EXERCISES
        ])
    db.commit()
