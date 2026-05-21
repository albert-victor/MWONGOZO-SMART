-- Phase 4: users, sessions, student profiles, saved programmes

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    uuid                CHAR(36)        NOT NULL,
    email               VARCHAR(255)    NOT NULL,
    password_hash       VARCHAR(255)    NOT NULL,
    full_name           VARCHAR(255)    NULL,
    role                ENUM('student','staff','admin') NOT NULL DEFAULT 'student',
    preferred_language  ENUM('sw','en','both') NOT NULL DEFAULT 'both',
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_uuid (uuid),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS auth_sessions (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    token_hash          CHAR(64)        NOT NULL,
    user_id             BIGINT UNSIGNED NOT NULL,
    expires_at          DATETIME(3)     NOT NULL,
    created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uq_auth_sessions_token (token_hash),
    KEY idx_auth_sessions_user (user_id),
    KEY idx_auth_sessions_expires (expires_at),
    CONSTRAINT fk_auth_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS student_profiles (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id             BIGINT UNSIGNED NULL,
    session_id          VARCHAR(64)     NOT NULL,
    combination         VARCHAR(16)     NULL,
    exam_number         VARCHAR(32)     NULL,
    exam_year           SMALLINT UNSIGNED NULL,
    source              VARCHAR(64)     NOT NULL DEFAULT 'recommend_form',
    pathway             ENUM('o_level','a_level','equivalent') NOT NULL DEFAULT 'a_level',
    input_snapshot      JSON            NULL,
    last_recommend_at   DATETIME(3)     NULL,
    created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uq_student_profiles_session (session_id),
    UNIQUE KEY uq_student_profiles_user (user_id),
    KEY idx_student_profiles_exam (exam_year, exam_number),
    CONSTRAINT fk_student_profiles_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS saved_programmes (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id             BIGINT UNSIGNED NULL,
    session_id          VARCHAR(64)     NULL,
    programme_code      VARCHAR(64)     NOT NULL,
    snapshot            JSON            NULL,
    saved_at            DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uq_saved_user_programme (user_id, programme_code),
    UNIQUE KEY uq_saved_session_programme (session_id, programme_code),
    KEY idx_saved_session (session_id, saved_at DESC),
    CONSTRAINT fk_saved_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
