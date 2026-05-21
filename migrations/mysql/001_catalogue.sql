-- Phase 1: catalogue tables (institutions, programmes, programme_requirements)
-- Target: MySQL 8.0+ / MariaDB 10.5+

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS institutions (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code                VARCHAR(32)     NOT NULL,
    name                VARCHAR(255)    NOT NULL,
    city                VARCHAR(128)    NOT NULL DEFAULT '',
    region              VARCHAR(128)    NOT NULL DEFAULT '',
    website             VARCHAR(512)    NULL,
    apply_url           VARCHAR(512)    NULL,
    cta_label           VARCHAR(64)     NOT NULL DEFAULT 'Apply Now',
    ownership           ENUM('public','private','unknown') NOT NULL DEFAULT 'unknown',
    kind                ENUM('university','college','institute','other') NOT NULL DEFAULT 'university',
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    metadata            JSON            NULL,
    created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at          DATETIME(3)     NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_institutions_code (code),
    KEY idx_institutions_region (region),
    KEY idx_institutions_active (is_active, deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS programmes (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code                VARCHAR(64)     NOT NULL,
    name                VARCHAR(512)    NOT NULL,
    institution_id      BIGINT UNSIGNED NOT NULL,
    city                VARCHAR(128)    NOT NULL DEFAULT '',
    region              VARCHAR(128)    NOT NULL DEFAULT '',
    category            ENUM(
                            'health','engineering','education','business',
                            'accounting_finance','agriculture','law','arts',
                            'science','tech','computing','other'
                        ) NOT NULL DEFAULT 'other',
    award_level         ENUM('certificate','diploma','bachelor','postgraduate') NOT NULL DEFAULT 'bachelor',
    duration_years      TINYINT UNSIGNED NULL,
    capacity            INT UNSIGNED    NULL,
    competition_tier    TINYINT UNSIGNED NOT NULL DEFAULT 3,
    tags                JSON            NOT NULL,
    source_reference    VARCHAR(255)    NOT NULL DEFAULT '',
    guidebook_year      VARCHAR(16)     NULL,
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at          DATETIME(3)     NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_programmes_code (code),
    KEY idx_programmes_institution (institution_id),
    KEY idx_programmes_category (category, award_level),
    KEY idx_programmes_region (region),
    CONSTRAINT fk_programmes_institution
        FOREIGN KEY (institution_id) REFERENCES institutions(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS programme_requirements (
    id                              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    programme_id                    BIGINT UNSIGNED NOT NULL,
    minimum_principal_passes        TINYINT UNSIGNED NOT NULL DEFAULT 2,
    minimum_total_points            DECIMAL(5,2)    NOT NULL DEFAULT 4.00,
    minimum_o_level_passes          TINYINT UNSIGNED NOT NULL DEFAULT 0,
    principal_pool_min_count        TINYINT UNSIGNED NOT NULL DEFAULT 0,
    strict                          TINYINT(1)      NOT NULL DEFAULT 0,
    principal_subject_pool          JSON            NOT NULL,
    required_principal_subjects     JSON            NOT NULL,
    minimum_a_level_subject_grades  JSON            NOT NULL,
    minimum_o_level_subject_grades  JSON            NOT NULL,
    preferred_o_level_subjects      JSON            NOT NULL,
    conditional_requirements        JSON            NOT NULL,
    notes                           JSON            NOT NULL,
    created_at                      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at                      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uq_programme_requirements_programme (programme_id),
    CONSTRAINT fk_programme_requirements_programme
        FOREIGN KEY (programme_id) REFERENCES programmes(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
