# Diseño de base de datos — FitPlan

## Objetivo

La base de datos de FitPlan almacenará los perfiles físicos de los usuarios,
sus restricciones, equipo disponible, ejercicios, planes semanales,
entrenamientos completados y retroalimentación.

El modelo permite generar una rutina inicial y adaptarla posteriormente
según el cumplimiento, dificultad percibida, energía y molestias registradas.

## Diagrama entidad-relación

```mermaid
erDiagram
    USERS ||--|| USER_PROFILES : has
    USERS ||--o{ USER_EQUIPMENT : owns
    EQUIPMENT ||--o{ USER_EQUIPMENT : selected
    USERS ||--o{ USER_RESTRICTIONS : reports
    RESTRICTIONS ||--o{ USER_RESTRICTIONS : selected

    EXERCISES ||--o{ EXERCISE_EQUIPMENT : requires
    EQUIPMENT ||--o{ EXERCISE_EQUIPMENT : used_by
    EXERCISES ||--o{ EXERCISE_RESTRICTIONS : contraindicated
    RESTRICTIONS ||--o{ EXERCISE_RESTRICTIONS : affects

    USERS ||--o{ WORKOUT_PLANS : receives
    WORKOUT_PLANS ||--o{ PLAN_SESSIONS : contains
    PLAN_SESSIONS ||--o{ SESSION_EXERCISES : contains
    EXERCISES ||--o{ SESSION_EXERCISES : assigned

    USERS ||--o{ WORKOUT_LOGS : completes
    PLAN_SESSIONS ||--o{ WORKOUT_LOGS : records
    WORKOUT_LOGS ||--o{ EXERCISE_LOGS : contains
    EXERCISES ||--o{ EXERCISE_LOGS : tracks
    WORKOUT_LOGS ||--o| SESSION_FEEDBACK : receives

    USERS {
        uuid id PK
        string email UK
        string password_hash
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    USER_PROFILES {
        uuid id PK
        uuid user_id FK
        integer age
        decimal weight_kg
        decimal height_cm
        string experience_level
        string primary_goal
        string training_location
        integer available_days
        integer session_minutes
        boolean gamification_enabled
        datetime updated_at
    }

    EQUIPMENT {
        uuid id PK
        string name UK
        string category
        boolean is_active
    }

    USER_EQUIPMENT {
        uuid user_id FK
        uuid equipment_id FK
    }

    RESTRICTIONS {
        uuid id PK
        string name UK
        string body_area
        string description
    }

    USER_RESTRICTIONS {
        uuid id PK
        uuid user_id FK
        uuid restriction_id FK
        string severity
        string notes
        boolean is_active
    }

    EXERCISES {
        uuid id PK
        string name
        string description
        string primary_muscle
        string movement_pattern
        string difficulty_level
        string video_url
        string image_url
        string instructions
        boolean is_active
    }

    EXERCISE_EQUIPMENT {
        uuid exercise_id FK
        uuid equipment_id FK
        boolean is_required
    }

    EXERCISE_RESTRICTIONS {
        uuid exercise_id FK
        uuid restriction_id FK
        string risk_level
        string reason
    }

    WORKOUT_PLANS {
        uuid id PK
        uuid user_id FK
        string name
        string goal
        date start_date
        date end_date
        string status
        integer version
        string generation_reason
        datetime created_at
    }

    PLAN_SESSIONS {
        uuid id PK
        uuid plan_id FK
        integer day_number
        string name
        integer estimated_minutes
        string focus
        string status
    }

    SESSION_EXERCISES {
        uuid id PK
        uuid session_id FK
        uuid exercise_id FK
        integer exercise_order
        integer sets
        integer repetitions
        integer rest_seconds
        decimal target_rpe
        string notes
    }

    WORKOUT_LOGS {
        uuid id PK
        uuid user_id FK
        uuid session_id FK
        datetime started_at
        datetime completed_at
        string status
        integer actual_minutes
    }

    EXERCISE_LOGS {
        uuid id PK
        uuid workout_log_id FK
        uuid exercise_id FK
        integer completed_sets
        integer completed_repetitions
        decimal weight_used
        decimal perceived_effort
        boolean completed
        string notes
    }

    SESSION_FEEDBACK {
        uuid id PK
        uuid workout_log_id FK
        integer difficulty
        integer energy_level
        integer satisfaction
        boolean pain_reported
        string pain_area
        string pain_notes
        string comments
        datetime created_at
    }
