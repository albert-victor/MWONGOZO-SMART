-- Saved recommendation runs for logged-in students (analysis history)

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS saved_recommendations (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id             BIGINT UNSIGNED NOT NULL,
    session_id          VARCHAR(64)     NULL,
    title               VARCHAR(255)    NULL,
    input_snapshot      JSON            NULL,
    results_snapshot    JSON            NULL,
    recommend_count     INT UNSIGNED    NOT NULL DEFAULT 0,
    direct_count        INT UNSIGNED    NOT NULL DEFAULT 0,
    review_count        INT UNSIGNED    NOT NULL DEFAULT 0,
    saved_at            DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    KEY idx_saved_reco_user (user_id, saved_at DESC),
    CONSTRAINT fk_saved_reco_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
