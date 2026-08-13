-- ===================================================================
-- PROFESSIONAL AI - Extended Schema for Advanced Features
-- Adds support for: Images, Voice, Documents, Memory, Agents, etc.
-- ===================================================================

-- ===================================================================
-- USER MODULE ACCESS
-- ===================================================================
CREATE TABLE user_module_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module_id VARCHAR(50) NOT NULL,
    module_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, module_id)
);

CREATE INDEX idx_user_module_access_user ON user_module_access(user_id);
CREATE INDEX idx_user_module_access_module ON user_module_access(module_id);

-- ===================================================================
-- AI MEMORIES (Long-term user memory)
-- ===================================================================
CREATE TABLE ai_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL, -- preference, project, context, skill
    key VARCHAR(255) NOT NULL,
    value_encrypted TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    importance_score INT DEFAULT 5, -- 1-10
    access_count INT DEFAULT 0,
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, memory_type, key)
);

CREATE INDEX idx_ai_memories_user ON ai_memories(user_id, memory_type);
CREATE INDEX idx_ai_memories_importance ON ai_memories(importance_score DESC);

-- ===================================================================
-- AI AGENTS (Multi-step autonomous agents)
-- ===================================================================
CREATE TABLE ai_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type VARCHAR(50) NOT NULL, -- research, writing, coding, analysis, custom
    system_prompt TEXT NOT NULL,
    tools JSONB DEFAULT '[]', -- available tools for the agent
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    execution_count INT DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_agents_user ON ai_agents(user_id);
CREATE INDEX idx_ai_agents_type ON ai_agents(agent_type);

-- ===================================================================
-- AGENT EXECUTION LOGS
-- ===================================================================
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_description TEXT NOT NULL,
    steps JSONB NOT NULL, -- array of steps executed
    result TEXT,
    status VARCHAR(20) DEFAULT 'running', -- running, completed, failed, cancelled
    tokens_used INT DEFAULT 0,
    execution_time_ms INT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_agent_executions_agent ON agent_executions(agent_id, created_at);
CREATE INDEX idx_agent_executions_user ON agent_executions(user_id, created_at);

-- ===================================================================
-- IMAGES (Generated and analyzed)
-- ===================================================================
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_type VARCHAR(50) NOT NULL, -- generated, uploaded, analyzed
    storage_path TEXT NOT NULL,
    thumbnail_path TEXT,
    prompt TEXT, -- for generated images
    negative_prompt TEXT,
    model_used VARCHAR(100), -- stable-diffusion, flux, etc.
    parameters JSONB DEFAULT '{}',
    width INT,
    height INT,
    file_size_bytes INT,
    mime_type VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_images_user ON images(user_id, created_at);
CREATE INDEX idx_images_type ON images(image_type);

-- ===================================================================
-- VOICE RECORDINGS
-- ===================================================================
CREATE TABLE voice_recordings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recording_type VARCHAR(50) NOT NULL, -- input, output
    storage_path TEXT NOT NULL,
    duration_seconds INT,
    language VARCHAR(10), -- en, ur, hi, ar, etc.
    transcription TEXT,
    model_used VARCHAR(100), -- faster-whisper, piper, edge-tts
    file_size_bytes INT,
    mime_type VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_voice_recordings_user ON voice_recordings(user_id, created_at);

-- ===================================================================
-- DOCUMENTS (Uploaded PDFs, Word docs, etc.)
-- ===================================================================
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- pdf, docx, txt, image
    original_filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size_bytes INT,
    mime_type VARCHAR(50),
    page_count INT,
    word_count INT,
    language_detected VARCHAR(10),
    summary TEXT,
    extracted_text TEXT,
    metadata JSONB DEFAULT '{}',
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_documents_user ON documents(user_id, created_at);
CREATE INDEX idx_documents_status ON documents(processing_status);

-- ===================================================================
-- TRANSLATIONS
-- ===================================================================
CREATE TABLE translations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_language VARCHAR(10) NOT NULL,
    target_language VARCHAR(10) NOT NULL,
    original_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    context_type VARCHAR(50), -- chat, document, image, voice
    context_id UUID, -- references related entity
    model_used VARCHAR(100),
    confidence_score DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_translations_user ON translations(user_id, created_at);
CREATE INDEX idx_translations_languages ON translations(source_language, target_language);

-- ===================================================================
-- WEB SEARCHES
-- ===================================================================
CREATE TABLE web_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    search_engine VARCHAR(50) NOT NULL, -- searxng, serper, google
    results JSONB NOT NULL, -- search results
    result_count INT DEFAULT 0,
    execution_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_web_searches_user ON web_searches(user_id, created_at);

-- ===================================================================
-- CUSTOM CHATBOTS
-- ===================================================================
CREATE TABLE chatbots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    avatar_url TEXT,
    system_prompt TEXT NOT NULL,
    welcome_message TEXT,
    suggested_prompts JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    conversation_count INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.00,
    rating_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chatbots_user ON chatbots(user_id);
CREATE INDEX idx_chatbots_public ON chatbots(is_public, is_featured);

-- ===================================================================
-- CHATBOT CONVERSATIONS
-- ===================================================================
CREATE TABLE chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chatbot_id UUID NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    messages JSONB NOT NULL DEFAULT '[]',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chatbot_conversations_chatbot ON chatbot_conversations(chatbot_id, started_at);
CREATE INDEX idx_chatbot_conversations_user ON chatbot_conversations(user_id, started_at);

-- ===================================================================
-- SCREENSHOT TO CODE
-- ===================================================================
CREATE TABLE screenshot_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_id UUID REFERENCES images(id) ON DELETE CASCADE,
    generated_code TEXT NOT NULL,
    framework VARCHAR(50), -- html, react, vue, flutter
    language VARCHAR(50), -- html, css, javascript, dart
    model_used VARCHAR(100),
    accuracy_score DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_screenshot_codes_user ON screenshot_codes(user_id, created_at);

-- ===================================================================
-- CODE EXPLANATIONS
-- ===================================================================
CREATE TABLE code_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_code TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    line_by_line JSONB, -- detailed line-by-line breakdown
    model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_code_explanations_user ON code_explanations(user_id, created_at);

-- ===================================================================
-- MODEL ROUTER LOGS (Track which model was selected for each task)
-- ===================================================================
CREATE TABLE model_router_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL, -- text, code, image, voice, document, search
    selected_model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    reason VARCHAR(255), -- why this model was selected
    execution_time_ms INT,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_model_router_logs_user ON model_router_logs(user_id, created_at);
CREATE INDEX idx_model_router_logs_model ON model_router_logs(selected_model, created_at);

-- ===================================================================
-- UPDATE TRIGGERS FOR NEW TABLES
-- ===================================================================
CREATE TRIGGER ai_memories_updated_at BEFORE UPDATE ON ai_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER ai_agents_updated_at BEFORE UPDATE ON ai_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER chatbots_updated_at BEFORE UPDATE ON chatbots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ===================================================================
-- FUNCTIONS FOR ANALYTICS
-- ===================================================================

-- Get user's most used features
CREATE OR REPLACE FUNCTION get_user_feature_usage(user_uuid UUID, days_back INT DEFAULT 30)
RETURNS TABLE(feature VARCHAR, usage_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ul.action as feature,
        COUNT(*) as usage_count
    FROM usage_logs ul
    WHERE ul.user_id = user_uuid
        AND ul.created_at >= NOW() - INTERVAL '1 day' * days_back
    GROUP BY ul.action
    ORDER BY usage_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Get AI memory insights
CREATE OR REPLACE FUNCTION get_user_memory_summary(user_uuid UUID)
RETURNS TABLE(
    memory_type VARCHAR,
    memory_count BIGINT,
    avg_importance DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        am.memory_type,
        COUNT(*) as memory_count,
        AVG(am.importance_score) as avg_importance
    FROM ai_memories am
    WHERE am.user_id = user_uuid
    GROUP BY am.memory_type
    ORDER BY memory_count DESC;
END;
$$ LANGUAGE plpgsql;