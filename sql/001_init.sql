-- PostgreSQL schema for Kitobxon Tavsiya Bot.
-- The application also creates these tables automatically at startup.

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recommendation_status') THEN
        CREATE TYPE recommendation_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'PUBLISHING');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(200) NOT NULL,
    reason TEXT NOT NULL,
    photo_file_id VARCHAR(512),
    status recommendation_status NOT NULL DEFAULT 'PENDING',
    admin_message_id BIGINT,
    channel_message_id BIGINT,
    reviewed_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_recommendations_status ON recommendations(status);
CREATE INDEX IF NOT EXISTS ix_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS ix_recommendations_created_at ON recommendations(created_at);
