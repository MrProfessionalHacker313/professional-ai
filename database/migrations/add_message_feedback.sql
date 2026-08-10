-- ===================================================================
-- ADD MESSAGE FEEDBACK AND EDIT TRACKING
-- ===================================================================

-- Add columns to messages table for edit tracking and feedback
ALTER TABLE messages ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE messages ADD COLUMN IF NOT EXISTS is_edited BOOLEAN DEFAULT FALSE;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS feedback VARCHAR(10); -- 'thumbs_up', 'thumbs_down', or NULL
ALTER TABLE messages ADD COLUMN IF NOT EXISTS feedback_updated_at TIMESTAMPTZ;

-- Create trigger to auto-update updated_at on message edits
CREATE OR REPLACE FUNCTION update_message_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS messages_updated_at ON messages;
CREATE TRIGGER messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_message_updated_at();

-- Index for faster message lookups
CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_feedback ON messages(feedback) WHERE feedback IS NOT NULL;