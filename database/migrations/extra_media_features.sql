-- Extra Media Features - Database Migration
-- Adds tables for thumbnails, memes, watermarks, trends, and batch campaigns
-- Run this migration to add support for all 10 extra media features

-- ===================================================================
-- MEDIA THUMBNAILS - Auto-generated thumbnails for videos
-- ===================================================================

CREATE TABLE IF NOT EXISTS media_thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES media_jobs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(30) DEFAULT 'pending' NOT NULL,
    
    -- Thumbnail data
    thumbnail_url TEXT,
    thumbnail_path TEXT,
    thumbnail_text TEXT,
    is_selected BOOLEAN DEFAULT FALSE,
    
    -- Generation details
    generation_prompt TEXT,
    ai_model_used VARCHAR(100),
    
    -- Metadata
    width INTEGER,
    height INTEGER,
    file_size_bytes INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    selected_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_media_thumbnails_job ON media_thumbnails(job_id);
CREATE INDEX IF NOT EXISTS idx_media_thumbnails_user ON media_thumbnails(user_id);
CREATE INDEX IF NOT EXISTS idx_media_thumbnails_status ON media_thumbnails(status);

-- ===================================================================
-- MEDIA MEMES - User-generated memes
-- ===================================================================

CREATE TABLE IF NOT EXISTS media_memes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meme_text TEXT NOT NULL,
    meme_type VARCHAR(20) DEFAULT 'image' NOT NULL,
    template_used VARCHAR(100),
    status VARCHAR(30) DEFAULT 'queued' NOT NULL,
    
    -- Output
    output_path TEXT,
    output_url TEXT,
    output_size_bytes INTEGER,
    
    -- AI suggestions
    suggested_captions JSONB,
    humor_score FLOAT,
    
    -- Progress
    progress FLOAT DEFAULT 0.0,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_media_memes_user_status ON media_memes(user_id, status);
CREATE INDEX IF NOT EXISTS idx_media_memes_created ON media_memes(created_at);

-- ===================================================================
-- MEDIA WATERMARKS - Branding watermarks for PRO users
-- ===================================================================

CREATE TABLE IF NOT EXISTS media_watermarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    
    -- Watermark content
    watermark_text VARCHAR(200),
    logo_path TEXT,
    position VARCHAR(20) DEFAULT 'bottom-right',
    
    -- Settings
    opacity FLOAT DEFAULT 0.7,
    font_size INTEGER DEFAULT 24,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage tracking
    total_applied INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_watermarks_user ON media_watermarks(user_id);

-- ===================================================================
-- MEDIA TRENDS - Trending hooks/captions/hashtags by country
-- ===================================================================

CREATE TABLE IF NOT EXISTS media_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code VARCHAR(2) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    
    -- Trend data
    trend_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    engagement_score FLOAT,
    
    -- Metadata
    category VARCHAR(50),
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    trend_start_date TIMESTAMPTZ,
    trend_end_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_trends_country_platform ON media_trends(country_code, platform);
CREATE INDEX IF NOT EXISTS idx_media_trends_active ON media_trends(is_active);

-- ===================================================================
-- MEDIA BATCH CAMPAIGNS - Business batch video generation
-- ===================================================================

CREATE TABLE IF NOT EXISTS media_batch_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Campaign details
    campaign_name VARCHAR(200) NOT NULL,
    product_description TEXT NOT NULL,
    product_media_path TEXT,
    
    -- Batch settings
    total_prompts INTEGER DEFAULT 10,
    completed_prompts INTEGER DEFAULT 0,
    failed_prompts INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(30) DEFAULT 'queued',
    progress FLOAT DEFAULT 0.0,
    
    -- Output
    output_urls JSONB,
    
    -- Timestamps
    queued_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_batch_campaigns_user ON media_batch_campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_media_batch_campaigns_status ON media_batch_campaigns(status);

-- ===================================================================
-- MEDIA BATCH PROMPTS - Individual prompts in a batch campaign
-- ===================================================================

CREATE TABLE IF NOT EXISTS media_batch_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES media_batch_campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Prompt details
    prompt_text TEXT NOT NULL,
    prompt_number INTEGER NOT NULL,
    
    -- Job reference
    media_job_id UUID REFERENCES media_jobs(id) ON DELETE SET NULL,
    
    -- Status
    status VARCHAR(30) DEFAULT 'pending',
    output_url TEXT,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_media_batch_prompts_campaign ON media_batch_prompts(campaign_id, prompt_number);

-- ===================================================================
-- UPDATE MEDIA_JOBS TABLE - Add thumbnail support
-- ===================================================================

-- Add thumbnail columns to media_jobs if they don't exist
DO $$ 
BEGIN
    -- Add thumbnail_options column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'media_jobs' AND column_name = 'thumbnail_options') THEN
        ALTER TABLE media_jobs ADD COLUMN thumbnail_options JSONB;
    END IF;
    
    -- Add selected_thumbnail_url column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'media_jobs' AND column_name = 'selected_thumbnail_url') THEN
        ALTER TABLE media_jobs ADD COLUMN selected_thumbnail_url TEXT;
    END IF;
    
    -- Add watermark_applied column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'media_jobs' AND column_name = 'watermark_applied') THEN
        ALTER TABLE media_jobs ADD COLUMN watermark_applied BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- ===================================================================
-- SAMPLE DATA - Initial trends for Pakistan, India, US, UK
-- ===================================================================

-- Pakistan Trends
INSERT INTO media_trends (country_code, platform, trend_type, content, engagement_score, category, language) VALUES
('PK', 'tiktok', 'hook', 'Aaj ka amazing trick aapko bhi chahiye! 🔥', 95.0, 'comedy', 'ur'),
('PK', 'tiktok', 'hashtag', '#PakistanTrends2024', 88.0, 'general', 'ur'),
('PK', 'reels', 'caption', 'Yeh video dekh kar apni life change karlein! 💫', 92.0, 'lifestyle', 'ur'),
('PK', 'youtube', 'hook', 'Top 10 secrets aapne kabhi nahi suna honge!', 90.0, 'education', 'ur'),
('IN', 'tiktok', 'hook', 'Aaj ka viral challenge! Kya aap kar sakte hain?', 96.0, 'challenge', 'hi'),
('IN', 'reels', 'hashtag', '#ViralReels2024', 94.0, 'general', 'hi'),
('IN', 'youtube', 'caption', 'Dekh kar apne aapko badal jaoge! 🌟', 91.0, 'motivation', 'hi'),
('US', 'tiktok', 'hook', 'This hack will blow your mind! 🤯', 97.0, 'lifestyle', 'en'),
('US', 'reels', 'hashtag', '#Viral2024 #TrendingNow', 95.0, 'general', 'en'),
('UK', 'tiktok', 'caption', 'You won''t believe what happened next! 😱', 93.0, 'comedy', 'en'),
('UK', 'youtube', 'hook', 'The truth they don''t want you to know!', 89.0, 'education', 'en')
ON CONFLICT DO NOTHING;

-- ===================================================================
-- GRANTS - Ensure proper permissions
-- ===================================================================

GRANT ALL ON media_thumbnails TO proai_user;
GRANT ALL ON media_memes TO proai_user;
GRANT ALL ON media_watermarks TO proai_user;
GRANT ALL ON media_trends TO proai_user;
GRANT ALL ON media_batch_campaigns TO proai_user;
GRANT ALL ON media_batch_prompts TO proai_user;

GRANT USAGE, SELECT ON SEQUENCE media_thumbnails_id_seq TO proai_user;
GRANT USAGE, SELECT ON SEQUENCE media_memes_id_seq TO proai_user;
GRANT USAGE, SELECT ON SEQUENCE media_watermarks_id_seq TO proai_user;
GRANT USAGE, SELECT ON SEQUENCE media_trends_id_seq TO proai_user;
GRANT USAGE, SELECT ON SEQUENCE media_batch_campaigns_id_seq TO proai_user;
GRANT USAGE, SELECT ON SEQUENCE media_batch_prompts_id_seq TO proai_user;

-- ===================================================================
-- MIGRATION COMPLETE
-- ===================================================================

-- All 10 extra media features are now supported:
-- 1. AI Thumbnail Maker (media_thumbnails)
-- 2. Background Music (uses existing media_jobs)
-- 3. Story-to-Video (uses existing media_jobs)
-- 4. Talking Avatar Videos (uses existing media_jobs)
-- 5. TikTok/Reels Trending Pack (media_trends)
-- 6. Batch Campaign Maker (media_batch_campaigns, media_batch_prompts)
-- 7. Watermark & Branding (media_watermarks)
-- 8. Meme Maker (media_memes)
-- 9. Video → Blog (uses existing media_jobs)
-- 10. AI Intro/Outro (uses existing media_jobs)

-- Admin can toggle all features via: PUT /api/admin/owner/control-state