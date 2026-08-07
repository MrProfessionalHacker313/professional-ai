-- Ultra Speed Database Indexes
-- Adds indexes for hot queries to achieve sub-10ms response times

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status) WHERE status = 'active';

-- Subscriptions table indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);

-- Transactions table indexes
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC);

-- Chat messages indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created ON chat_messages(user_id, created_at DESC);

-- Media jobs indexes
CREATE INDEX IF NOT EXISTS idx_media_jobs_user_id ON media_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_media_jobs_status ON media_jobs(status);
CREATE INDEX IF NOT EXISTS idx_media_jobs_created_at ON media_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_jobs_user_status ON media_jobs(user_id, status);

-- AI cache table (for repeated queries)
CREATE TABLE IF NOT EXISTS ai_cache (
    id SERIAL PRIMARY KEY,
    prompt_hash VARCHAR(64) UNIQUE NOT NULL,
    prompt_text TEXT NOT NULL,
    response_json JSONB NOT NULL,
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '1 hour'
);

CREATE INDEX IF NOT EXISTS idx_ai_cache_hash ON ai_cache(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_ai_cache_expires ON ai_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_ai_cache_model ON ai_cache(model);

-- Auto-vacuum for ai_cache
ALTER TABLE ai_cache SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- Sessions index
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Payments index
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at DESC);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_users_email_status ON users(email, status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_user_status_created ON transactions(user_id, status, created_at DESC);

-- Partial indexes for active records only
CREATE INDEX IF NOT EXISTS idx_users_active_email ON users(email) WHERE status = 'active' AND deleted_at IS NULL;

-- Covering indexes to avoid table lookups
CREATE INDEX IF NOT EXISTS idx_users_email_covering ON users(email) INCLUDE (id, name, status);

-- GIN index for JSONB columns (if used)
CREATE INDEX IF NOT EXISTS idx_media_jobs_metadata_gin ON media_jobs USING GIN (metadata);

-- Analyze tables for query planner
ANALYZE users;
ANALYZE subscriptions;
ANALYZE transactions;
ANALYZE chat_messages;
ANALYZE media_jobs;
ANALYZE ai_cache;