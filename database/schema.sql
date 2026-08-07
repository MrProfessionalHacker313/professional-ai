-- ===================================================================
-- PROFESSIONAL AI (PRO AI) - Complete Database Schema
-- PostgreSQL with Security Hardening
-- ===================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ===================================================================
-- FUNCTIONS
-- ===================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- USERS TABLE
-- ===================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    display_name VARCHAR(100),
    avatar_url TEXT,
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    preferred_language VARCHAR(10) DEFAULT 'en',
    device_fingerprint TEXT,
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,
    failed_login_attempts BIGINT DEFAULT 0,
    locked_until TIMESTAMPTZ,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255)
);

-- ===================================================================
-- OWNER SETTINGS TABLE
-- ===================================================================
CREATE TABLE owner_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    totp_secret_encrypted TEXT,
    totp_enabled BOOLEAN DEFAULT FALSE,
    setup_completed BOOLEAN DEFAULT FALSE,
    reset_token VARCHAR(255),
    reset_token_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- OAUTH ACCOUNTS TABLE
-- ===================================================================
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_account_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(provider, provider_account_id)
);

-- ===================================================================
-- TWO-FACTOR AUTH TABLE
-- ===================================================================
CREATE TABLE two_factor_auth (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    secret VARCHAR(255) NOT NULL,
    method VARCHAR(20) DEFAULT 'totp',
    phone VARCHAR(20),
    is_enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ===================================================================
-- PASSKEYS (WebAuthn) TABLE
-- ===================================================================
CREATE TABLE passkeys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credential_id TEXT UNIQUE NOT NULL,
    public_key TEXT NOT NULL,
    counter BIGINT DEFAULT 0,
    device_name VARCHAR(255),
    transports TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- ===================================================================
-- SESSIONS TABLE
-- ===================================================================
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    device_fingerprint TEXT,
    ip_address INET,
    user_agent TEXT,
    is_valid BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- LOGIN ATTEMPTS TABLE (Account Lockout & Audit)
-- ===================================================================
CREATE TABLE login_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT FALSE,
    failure_reason VARCHAR(255),
    attempted_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- SUBSCRIPTIONS TABLE
-- ===================================================================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(20) DEFAULT 'free',
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    payment_method VARCHAR(50),
    payment_token_encrypted TEXT,
    card_last4 VARCHAR(4),
    card_brand VARCHAR(40),
    card_expiry_month VARCHAR(2),
    card_expiry_year VARCHAR(4),
    cardholder_name VARCHAR(120),
    trial_start_at TIMESTAMPTZ,
    trial_end_at TIMESTAMPTZ,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    failed_retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ===================================================================
-- USAGE LOGS TABLE
-- ===================================================================
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    tokens_used INT DEFAULT 0,
    prompt_text TEXT,
    response_text TEXT,
    model_used VARCHAR(100),
    execution_time_ms INT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- CODE GENERATION COUNTER (Free tier limit)
-- ===================================================================
CREATE TABLE code_generation_counters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    count INT DEFAULT 0,
    UNIQUE(user_id, date)
);

-- ===================================================================
-- VAULT (Encrypted user projects & data)
-- ===================================================================
CREATE TABLE vault_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    data_encrypted TEXT NOT NULL,
    encryption_key_id VARCHAR(255) NOT NULL,
    iv_hex VARCHAR(64) NOT NULL,
    auth_tag_hex VARCHAR(64) NOT NULL,
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- VAULT ACCESS LOGS (Admin access audit trail)
-- ===================================================================
CREATE TABLE vault_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    accessed_by_admin_id UUID NOT NULL REFERENCES users(id),
    target_user_id UUID NOT NULL REFERENCES users(id),
    vault_entry_id UUID REFERENCES vault_data(id),
    action VARCHAR(50) NOT NULL,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- REVENUE LOGS
-- ===================================================================
CREATE TABLE revenue_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID REFERENCES subscriptions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'completed',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- CREDITS TABLE
-- ===================================================================
CREATE TABLE credits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    balance INT DEFAULT 0,
    total_granted INT DEFAULT 0,
    total_consumed INT DEFAULT 0,
    last_reset_at TIMESTAMPTZ,
    next_reset_at TIMESTAMPTZ,
    rollover_percentage INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ===================================================================
-- CREDIT TRANSACTIONS (Audit Trail)
-- ===================================================================
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    credit_id UUID NOT NULL REFERENCES credits(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    balance_after INT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    action VARCHAR(100),
    reference_id UUID,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- REFUND LOGS
-- ===================================================================
CREATE TABLE refund_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revenue_id UUID NOT NULL REFERENCES revenue_logs(id),
    admin_id UUID NOT NULL REFERENCES users(id),
    amount DECIMAL(10, 2) NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- SUPPORT TICKETS
-- ===================================================================
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(10) DEFAULT 'normal',
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ===================================================================
-- SUPPORT TICKET REPLIES
-- ===================================================================
CREATE TABLE ticket_replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- ADMIN AUDIT LOGS (Security)
-- ===================================================================
CREATE TABLE admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(255),
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- SECURITY EVENTS
-- ===================================================================
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    user_id UUID REFERENCES users(id),
    ip_address VARCHAR(45),
    details TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===================================================================
-- ADVANCED FEATURES TABLES
-- ===================================================================

CREATE TABLE ai_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR(20) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value_encrypted TEXT NOT NULL,
    importance_score INT DEFAULT 5,
    extra_metadata JSONB,
    access_count INT DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, memory_type, key)
);

CREATE TABLE ai_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type VARCHAR(50) NOT NULL,
    system_prompt TEXT NOT NULL,
    tools JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    execution_count INT DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_description TEXT NOT NULL,
    result TEXT,
    steps JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT,
    tokens_used INT DEFAULT 0,
    execution_time_ms INT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_type VARCHAR(20) NOT NULL,
    storage_path TEXT,
    thumbnail_path TEXT,
    prompt TEXT,
    negative_prompt TEXT,
    model_used VARCHAR(100),
    parameters JSONB DEFAULT '{}',
    width INT,
    height INT,
    file_size_bytes BIGINT,
    mime_type VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE voice_recordings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recording_type VARCHAR(20) NOT NULL,
    storage_path TEXT,
    language VARCHAR(10),
    transcription TEXT,
    model_used VARCHAR(100),
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(20) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    extracted_text TEXT,
    summary TEXT,
    word_count INT,
    language_detected VARCHAR(10),
    processing_status VARCHAR(20) DEFAULT 'pending',
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE translations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_language VARCHAR(10) NOT NULL,
    target_language VARCHAR(10) NOT NULL,
    original_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    context_type VARCHAR(20) DEFAULT 'chat',
    context_id UUID,
    model_used VARCHAR(100),
    confidence_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE web_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    search_engine VARCHAR(50) NOT NULL,
    results JSONB DEFAULT '[]',
    result_count INT DEFAULT 0,
    execution_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chatbots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    welcome_message TEXT,
    suggested_prompts JSONB DEFAULT '[]',
    is_public BOOLEAN DEFAULT FALSE,
    conversation_count INT DEFAULT 0,
    rating FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chatbot_id UUID NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    messages JSONB DEFAULT '[]',
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE screenshot_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_id UUID,
    generated_code TEXT NOT NULL,
    framework VARCHAR(50) NOT NULL,
    language VARCHAR(50) DEFAULT 'html',
    model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE code_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_code TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    explanation TEXT,
    line_by_line JSONB DEFAULT '[]',
    concepts JSONB DEFAULT '[]',
    improvements JSONB DEFAULT '[]',
    model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE model_router_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    task_description TEXT,
    selected_model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    reason TEXT,
    execution_time_ms INT,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 1: 40+ Language Brain
CREATE TABLE language_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_language VARCHAR(10) DEFAULT 'en',
    detected_language VARCHAR(10) DEFAULT 'en',
    confidence_score FLOAT DEFAULT 0.0,
    auto_translate BOOLEAN DEFAULT TRUE,
    translation_model VARCHAR(100),
    language_context JSON DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE TABLE multilingual_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID,
    language VARCHAR(10) NOT NULL,
    message_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 2: Live Hacking Lab
CREATE TABLE hacking_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    attack_type VARCHAR(50) NOT NULL,
    target_description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'running',
    current_step INT DEFAULT 0,
    total_steps INT DEFAULT 5,
    steps JSON DEFAULT '[]',
    result TEXT,
    ai_feedback JSON DEFAULT '{}',
    risk_level VARCHAR(20) DEFAULT 'safe',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE hacking_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES hacking_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    attack_step INT NOT NULL,
    payload TEXT,
    result TEXT,
    success BOOLEAN DEFAULT FALSE,
    ai_correction TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 3: AI Project Assistant
CREATE TABLE ai_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    stack JSON NOT NULL,
    files JSON DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'building',
    progress_percent INT DEFAULT 0,
    build_log TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_project_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES ai_projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(50),
    file_size_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_project_setup_guides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES ai_projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    instructions TEXT NOT NULL,
    dependencies JSON DEFAULT '[]',
    run_commands JSON DEFAULT '[]',
    environment_variables JSON DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 4: Screenshot to Full App
CREATE TABLE screenshot_apps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_id UUID,
    platform VARCHAR(50) NOT NULL,
    framework VARCHAR(50) NOT NULL,
    app_name VARCHAR(255),
    files JSON DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'generating',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE app_generation_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_id UUID NOT NULL REFERENCES screenshot_apps(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    component_name VARCHAR(255) NOT NULL,
    component_type VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,
    language VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 5: AI Detective
CREATE TABLE threat_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    analysis_type VARCHAR(20) NOT NULL,
    target TEXT NOT NULL,
    threat_level VARCHAR(20) DEFAULT 'safe',
    verdict TEXT NOT NULL,
    findings JSON DEFAULT '[]',
    score FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE detective_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES threat_analyses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    threat_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    proof TEXT,
    recommendation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 6: Voice Command Mode
CREATE TABLE voice_command_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    total_commands INT DEFAULT 0,
    successful_commands INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE TABLE voice_commands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES voice_command_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    command_text TEXT NOT NULL,
    interpreted_action VARCHAR(255),
    action_type VARCHAR(50),
    success BOOLEAN DEFAULT FALSE,
    result TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 7: AI Memory Vault
CREATE TABLE memory_vault_backups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    backup_name VARCHAR(255) NOT NULL,
    encrypted_data TEXT NOT NULL,
    memory_count INT DEFAULT 0,
    backup_size_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE memory_vault_syncs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(255),
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 8: Multi-Task Master
CREATE TABLE task_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_tasks INT NOT NULL,
    completed_tasks INT DEFAULT 0,
    failed_tasks INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',
    results JSON DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Feature 9: AI Teacher Mode
CREATE TABLE ai_courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(20) DEFAULT 'beginner',
    status VARCHAR(20) DEFAULT 'active',
    progress_percent INT DEFAULT 0,
    total_lessons INT DEFAULT 0,
    completed_lessons INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE teacher_lessons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES ai_courses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_number INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    examples JSON DEFAULT '[]',
    exercises JSON DEFAULT '[]',
    quiz JSON DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE teacher_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES ai_courses(id) ON DELETE CASCADE,
    completed_lessons JSON DEFAULT '[]',
    quiz_scores JSON DEFAULT '{}',
    overall_progress INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, course_id)
);

-- Feature 10: AI Business Advisor
CREATE TABLE business_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    budget DECIMAL(12,2),
    timeline_months INT,
    plan_content TEXT NOT NULL,
    strategies JSON DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE business_strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES business_plans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    action_items JSON DEFAULT '[]',
    expected_roi FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 11: Universal Format Expert
CREATE TABLE generated_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL,
    format VARCHAR(20) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    download_count INT DEFAULT 0,
    metadata JSON DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE file_generation_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    format VARCHAR(20) NOT NULL,
    template_content TEXT NOT NULL,
    variables JSON DEFAULT '[]',
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 12: AI Compatibility Checker
CREATE TABLE compatibility_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_snippet TEXT NOT NULL,
    target_platform VARCHAR(100) NOT NULL,
    compatibility_score FLOAT DEFAULT 0.0,
    issues_found JSON DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE compatibility_fixes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    check_id UUID NOT NULL REFERENCES compatibility_checks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fix_description TEXT NOT NULL,
    code_diff TEXT,
    applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 13: Smart Router Upgrade
CREATE TABLE device_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_type VARCHAR(50) NOT NULL,
    power_score INT DEFAULT 50,
    cpu_cores INT,
    ram_gb INT,
    has_gpu BOOLEAN DEFAULT FALSE,
    preferred_models JSON DEFAULT '[]',
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE TABLE smart_router_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    selected_model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    device_power_score INT,
    reason TEXT,
    execution_time_ms INT,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 14: Voice Cloning
CREATE TABLE voice_clones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    voice_name VARCHAR(255) NOT NULL,
    sample_duration_seconds FLOAT,
    model_used VARCHAR(100),
    status VARCHAR(20) DEFAULT 'processing',
    consent_verified BOOLEAN DEFAULT FALSE,
    storage_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE voice_clone_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clone_id UUID NOT NULL REFERENCES voice_clones(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text_synthesized TEXT,
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature 15: AI News Monitor
CREATE TABLE news_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topics JSON NOT NULL,
    categories JSON DEFAULT '[]',
    frequency VARCHAR(20) DEFAULT 'daily',
    is_active BOOLEAN DEFAULT TRUE,
    last_digest_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE news_digests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    digest_date DATE NOT NULL,
    articles_count INT DEFAULT 0,
    summary TEXT,
    categories JSON DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'generating',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    digest_id UUID REFERENCES news_digests(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    url TEXT,
    source VARCHAR(255),
    category VARCHAR(50),
    relevance_score FLOAT DEFAULT 0.0,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for new tables
CREATE INDEX idx_language_prefs_user ON language_preferences(user_id);
CREATE INDEX idx_hacking_sessions_user ON hacking_sessions(user_id, created_at);
CREATE INDEX idx_hacking_attempts_session ON hacking_attempts(session_id);
CREATE INDEX idx_ai_projects_user ON ai_projects(user_id, created_at);
CREATE INDEX idx_ai_project_files_project ON ai_project_files(project_id);
CREATE INDEX idx_screenshot_apps_user ON screenshot_apps(user_id, created_at);
CREATE INDEX idx_threat_analyses_user ON threat_analyses(user_id, created_at);
CREATE INDEX idx_voice_commands_session ON voice_commands(session_id);
CREATE INDEX idx_memory_vault_backups_user ON memory_vault_backups(user_id, created_at);
CREATE INDEX idx_task_batches_user ON task_batches(user_id, created_at);
CREATE INDEX idx_ai_courses_user ON ai_courses(user_id, created_at);
CREATE INDEX idx_teacher_lessons_course ON teacher_lessons(course_id);
CREATE INDEX idx_business_plans_user ON business_plans(user_id, created_at);
CREATE INDEX idx_generated_files_user ON generated_files(user_id, created_at);
CREATE INDEX idx_compatibility_checks_user ON compatibility_checks(user_id, created_at);
CREATE INDEX idx_device_profiles_user ON device_profiles(user_id);
CREATE INDEX idx_voice_clones_user ON voice_clones(user_id, created_at);
CREATE INDEX idx_news_subscriptions_user ON news_subscriptions(user_id);
CREATE INDEX idx_news_digests_user ON news_digests(user_id, digest_date);
CREATE INDEX idx_news_articles_digest ON news_articles(digest_id);

-- Add RLS for new user-scoped tables
ALTER TABLE language_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE hacking_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hacking_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_project_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_project_setup_guides ENABLE ROW LEVEL SECURITY;
ALTER TABLE screenshot_apps ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_generation_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE threat_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE detective_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_command_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_vault_backups ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_vault_syncs ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_generation_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE compatibility_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE compatibility_fixes ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE smart_router_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_clones ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_clone_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_digests ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;

CREATE POLICY language_pref_isolation ON language_preferences FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY hacking_session_isolation ON hacking_sessions FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY hacking_attempt_isolation ON hacking_attempts FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY ai_project_isolation ON ai_projects FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY ai_project_file_isolation ON ai_project_files FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY ai_project_setup_isolation ON ai_project_setup_guides FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY screenshot_app_isolation ON screenshot_apps FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY app_component_isolation ON app_generation_components FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY threat_analysis_isolation ON threat_analyses FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY detective_finding_isolation ON detective_findings FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY voice_cmd_session_isolation ON voice_command_sessions FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY voice_cmd_isolation ON voice_commands FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY vault_backup_isolation ON memory_vault_backups FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY vault_sync_isolation ON memory_vault_syncs FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY task_batch_isolation ON task_batches FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY ai_course_isolation ON ai_courses FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY teacher_lesson_isolation ON teacher_lessons FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY teacher_progress_isolation ON teacher_progress FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY business_plan_isolation ON business_plans FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY business_strategy_isolation ON business_strategies FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY generated_file_isolation ON generated_files FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
-- file_generation_templates is a global public template table, no user_id column
CREATE POLICY compat_check_isolation ON compatibility_checks FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY compat_fix_isolation ON compatibility_fixes FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY device_profile_isolation ON device_profiles FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY router_decision_isolation ON smart_router_decisions FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY voice_clone_isolation ON voice_clones FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY voice_clone_usage_isolation ON voice_clone_usage FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY news_sub_isolation ON news_subscriptions FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY news_digest_isolation ON news_digests FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY news_article_isolation ON news_articles FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

-- Update triggers for new tables with updated_at
DROP TRIGGER IF EXISTS ai_projects_updated_at ON ai_projects;
CREATE TRIGGER ai_projects_updated_at BEFORE UPDATE ON ai_projects FOR EACH ROW EXECUTE FUNCTION update_updated_at();
DROP TRIGGER IF EXISTS screenshot_apps_updated_at ON screenshot_apps;
CREATE TRIGGER screenshot_apps_updated_at BEFORE UPDATE ON screenshot_apps FOR EACH ROW EXECUTE FUNCTION update_updated_at();
DROP TRIGGER IF EXISTS ai_courses_updated_at ON ai_courses;
CREATE TRIGGER ai_courses_updated_at BEFORE UPDATE ON ai_courses FOR EACH ROW EXECUTE FUNCTION update_updated_at();
DROP TRIGGER IF EXISTS teacher_progress_updated_at ON teacher_progress;
CREATE TRIGGER teacher_progress_updated_at BEFORE UPDATE ON teacher_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at();
DROP TRIGGER IF EXISTS business_plans_updated_at ON business_plans;
CREATE TRIGGER business_plans_updated_at BEFORE UPDATE ON business_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at();
DROP TRIGGER IF EXISTS news_digests_updated_at ON news_digests;
CREATE TRIGGER news_digests_updated_at BEFORE UPDATE ON news_digests FOR EACH ROW EXECUTE FUNCTION update_updated_at();
DROP TRIGGER IF EXISTS language_preferences_updated_at ON language_preferences;
CREATE TRIGGER language_preferences_updated_at BEFORE UPDATE ON language_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ===================================================================
-- INDEXES
-- ===================================================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_admin ON users(is_admin);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_oauth_provider ON oauth_accounts(provider, provider_account_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_valid ON sessions(is_valid, expires_at);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_usage_logs_user ON usage_logs(user_id, created_at);
CREATE INDEX idx_usage_logs_action ON usage_logs(action);
CREATE INDEX idx_code_counters_user ON code_generation_counters(user_id, date);
CREATE INDEX idx_vault_user ON vault_data(user_id);
CREATE INDEX idx_revenue_logs_user ON revenue_logs(user_id);
CREATE INDEX idx_revenue_logs_status ON revenue_logs(status);
CREATE INDEX idx_support_tickets_user ON support_tickets(user_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_ticket_replies_ticket ON ticket_replies(ticket_id);
CREATE INDEX idx_vault_access_logs_admin ON vault_access_logs(accessed_by_admin_id);
CREATE INDEX idx_vault_access_logs_target ON vault_access_logs(target_user_id);
CREATE INDEX idx_credits_user ON credits(user_id);
CREATE INDEX idx_credit_transactions_user ON credit_transactions(user_id, created_at);
CREATE INDEX idx_credit_transactions_type ON credit_transactions(transaction_type);
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_time ON login_attempts(attempted_at);
CREATE INDEX idx_admin_audit_logs_admin ON admin_audit_logs(admin_id);
CREATE INDEX idx_admin_audit_logs_time ON admin_audit_logs(created_at);
CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_resolved ON security_events(resolved);

-- ===================================================================
-- TRIGGERS
-- ===================================================================

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS subscriptions_updated_at ON subscriptions;
CREATE TRIGGER subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS vault_data_updated_at ON vault_data;
CREATE TRIGGER vault_data_updated_at BEFORE UPDATE ON vault_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS support_tickets_updated_at ON support_tickets;
CREATE TRIGGER support_tickets_updated_at BEFORE UPDATE ON support_tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS two_factor_auth_updated_at ON two_factor_auth;
CREATE TRIGGER two_factor_auth_updated_at BEFORE UPDATE ON two_factor_auth
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS credits_updated_at ON credits;
CREATE TRIGGER credits_updated_at BEFORE UPDATE ON credits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS chatbots_updated_at ON chatbots;
CREATE TRIGGER chatbots_updated_at BEFORE UPDATE ON chatbots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ===================================================================
-- MEDIA ENGINE TABLES (videos, pictures, posters, animations)
-- ===================================================================
CREATE TABLE IF NOT EXISTS media_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_type VARCHAR(20) NOT NULL DEFAULT 'video',
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    topic TEXT NOT NULL,
    script TEXT,
    scenes_text TEXT,
    voice_style VARCHAR(30) DEFAULT 'adult_female',
    voice_prompt TEXT,
    language VARCHAR(10) DEFAULT 'en',
    duration_seconds INTEGER DEFAULT 15,
    resolution VARCHAR(10) DEFAULT '8k',
    format VARCHAR(10) DEFAULT 'mp4',
    aspect_ratio VARCHAR(10) DEFAULT '16:9',
    quality_slider VARCHAR(10) DEFAULT '8k',
    model VARCHAR(100),
    negative_prompt TEXT,
    storyboard JSONB,
    scene_count INTEGER DEFAULT 0,
    storyboard_status VARCHAR(30),
    voice_over_path TEXT,
    voice_over_status VARCHAR(30),
    voice_clone_id UUID,
    voice_consent BOOLEAN DEFAULT FALSE,
    subtitles_path TEXT,
    subtitle_verify_status VARCHAR(30),
    verification_report JSONB,
    accuracy_verified BOOLEAN DEFAULT FALSE,
    output_path TEXT,
    output_url TEXT,
    output_resolution VARCHAR(10),
    output_size_bytes INTEGER,
    thumbnail_path TEXT,
    duration_render_seconds FLOAT,
    progress FLOAT DEFAULT 0.0,
    progress_stage VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    queued_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_media_jobs_user_status ON media_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_media_jobs_created ON media_jobs(created_at);

CREATE TABLE IF NOT EXISTS media_scenes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES media_jobs(id) ON DELETE CASCADE,
    scene_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    prompt TEXT NOT NULL,
    duration_seconds FLOAT DEFAULT 5.0,
    status VARCHAR(30) DEFAULT 'pending',
    output_path TEXT,
    output_url TEXT,
    seed INTEGER,
    width INTEGER,
    height INTEGER,
    metadata JSONB DEFAULT '{}',
    generated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_media_scenes_job ON media_scenes(job_id, scene_number);

CREATE TABLE IF NOT EXISTS media_subtitle_tracks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES media_jobs(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'en',
    source_script TEXT NOT NULL,
    subtitle_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, language)
);

CREATE TABLE IF NOT EXISTS media_subtitle_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES media_jobs(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'en',
    script_words INTEGER NOT NULL,
    subtitle_words INTEGER NOT NULL,
    matched_words INTEGER NOT NULL,
    mismatch_words INTEGER NOT NULL,
    match_percentage FLOAT NOT NULL,
    passed BOOLEAN DEFAULT FALSE,
    mismatches JSONB DEFAULT '[]',
    regenerated BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_media_subtitle_verify_job ON media_subtitle_verifications(job_id);

CREATE TABLE IF NOT EXISTS media_voice_clones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    audio_path TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    consent_given BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'ready',
    provider_clone_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_media_voice_clones_user ON media_voice_clones(user_id);

CREATE TABLE IF NOT EXISTS media_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    usage_date TIMESTAMPTZ NOT NULL,
    videos_count INTEGER DEFAULT 0,
    pictures_count INTEGER DEFAULT 0,
    animations_count INTEGER DEFAULT 0,
    total_jobs INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, usage_date)
);
CREATE INDEX IF NOT EXISTS idx_media_usage_date ON media_usage(usage_date);

CREATE TABLE IF NOT EXISTS media_downloads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES media_jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    downloaded_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_media_downloads_job ON media_downloads(job_id);

CREATE TABLE IF NOT EXISTS auto_editor_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'uploading',
    preset VARCHAR(20) NOT NULL DEFAULT 'custom',
    raw_files JSONB,
    raw_file_count INTEGER DEFAULT 0,
    scene_analysis JSONB,
    best_moments JSONB,
    cuts_made INTEGER DEFAULT 0,
    add_transitions BOOLEAN DEFAULT TRUE,
    add_captions BOOLEAN DEFAULT TRUE,
    color_grade BOOLEAN DEFAULT TRUE,
    stabilize BOOLEAN DEFAULT TRUE,
    ken_burns BOOLEAN DEFAULT TRUE,
    add_intro_outro BOOLEAN DEFAULT TRUE,
    adjust_speed BOOLEAN DEFAULT TRUE,
    background_music BOOLEAN DEFAULT TRUE,
    watermark_toggle BOOLEAN DEFAULT TRUE,
    caption_language VARCHAR(10) DEFAULT 'en',
    output_aspect_ratio VARCHAR(10) DEFAULT '16:9',
    output_resolution VARCHAR(10) DEFAULT '1080p',
    trim_start FLOAT,
    trim_end FLOAT,
    speed_factor FLOAT,
    custom_transition VARCHAR(30),
    text_overlays JSONB,
    stickers JSONB,
    voice_over_path TEXT,
    output_path TEXT,
    output_url TEXT,
    output_size_bytes INTEGER,
    thumbnail_path TEXT,
    duration_seconds FLOAT,
    progress FLOAT DEFAULT 0.0,
    progress_stage VARCHAR(50),
    error_message TEXT,
    queued_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_auto_editor_jobs_user_status ON auto_editor_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_auto_editor_jobs_created ON auto_editor_jobs(created_at);

ALTER TABLE media_usage ADD COLUMN IF NOT EXISTS auto_edits_count INTEGER DEFAULT 0;

-- ===================================================================
-- BLOG SYSTEM (public knowledge hub)
-- ===================================================================
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    cover_gradient VARCHAR(255),
    author VARCHAR(255),
    date VARCHAR(255),
    read_time VARCHAR(50),
    category VARCHAR(100),
    tags JSON DEFAULT '[]',
    published BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(published);
CREATE INDEX IF NOT EXISTS idx_blog_posts_category ON blog_posts(category);
CREATE TRIGGER IF NOT EXISTS blog_posts_updated_at BEFORE UPDATE ON blog_posts FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ===================================================================
-- SECURITY: Row Level Security (RLS)
-- ===================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE vault_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE translations ENABLE ROW LEVEL SECURITY;
ALTER TABLE web_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbots ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbot_conversations ENABLE ROW LEVEL SECURITY;

-- Users can only view their own data
CREATE POLICY user_isolation ON users FOR ALL USING (id = current_setting('app.current_user_id')::UUID);
CREATE POLICY subscription_isolation ON subscriptions FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY credit_isolation ON credits FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY vault_isolation ON vault_data FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY memory_isolation ON ai_memories FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY document_isolation ON documents FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY image_isolation ON images FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY voice_isolation ON voice_recordings FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY translation_isolation ON translations FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY search_isolation ON web_searches FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY chatbot_isolation ON chatbots FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY conversation_isolation ON chatbot_conversations FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

-- ===================================================================
-- SECURITY: Least-Privilege Database Users
-- ===================================================================

-- Application user (least privilege - only needed operations)
-- This user is created by docker-compose (POSTGRES_USER=proai)

-- Read-only reporting user (if needed)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pro_ai_readonly') THEN
        CREATE ROLE pro_ai_readonly WITH LOGIN;
    END IF;
END
$$;

-- Grant SELECT-only on all relevant tables to readonly user
GRANT CONNECT ON DATABASE professional_ai TO pro_ai_readonly;
GRANT USAGE ON SCHEMA public TO pro_ai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pro_ai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO pro_ai_readonly;

-- Revoke dangerous permissions from application user (idempotent)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'proai') THEN
        REVOKE ALL ON pg_authid FROM proai;
        REVOKE ALL ON pg_user FROM proai;
        REVOKE ALL ON pg_roles FROM proai;
        REVOKE ALL ON pg_shadow FROM proai;
        ALTER ROLE proai WITH NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END
$$;

-- ===================================================================
-- SECURITY: Encrypted Backup Configuration
-- ===================================================================

-- Create a function for encrypted backups using pg_dump + openssl
CREATE OR REPLACE FUNCTION public.create_encrypted_backup()
RETURNS TEXT AS $$
BEGIN
    -- Script executed by backup cron:
    -- pg_dump -h localhost -U proai professional_ai | openssl enc -aes-256-cbc -salt -pbkdf2 -pass file:/run/secrets/backup_key | gzip > /backups/pro_ai_$(date +%Y%m%d_%H%M%S).sql.gz.enc
    RETURN 'Encrypted backup command configured. Run: pg_dump professional_ai | openssl enc -aes-256-cbc -salt -pbkdf2 | gzip > backup.sql.gz.enc';
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- SECURITY: Row-Level Security Bootstrap
-- ===================================================================

-- Helper to set current user for RLS policies
CREATE OR REPLACE FUNCTION public.set_app_current_user(user_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===================================================================
-- DEFAULT DATA: Create initial admin user (CHANGE PASSWORD AFTER FIRST LOGIN!)
-- WARNING: No default password - set via environment or first login
-- ===================================================================
