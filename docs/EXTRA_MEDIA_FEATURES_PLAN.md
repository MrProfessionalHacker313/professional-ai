# EXTRA MEDIA FEATURES — Implementation Plan

## Priority & Build Order

### Phase 1: Quick Wins (Week 1-2)
1. **AI Thumbnail Maker** — Auto-generate 5 clickable thumbnails per video
2. **Meme Maker** — Text to funny meme video/image (5/day free tier)
3. **Watermark & Branding** — Eagle logo + user name/website auto-placement

### Phase 2: Content Enhancement (Week 3-4)
4. **Background Music** — Free library (10 genres) + AI music generator
5. **AI Intro/Outro** — One-click professional branded intro/outro
6. **Video → Blog** — Auto-transcribe video to blog + social captions

### Phase 3: Advanced AI (Week 5-7)
7. **TikTok/Reels Trending Pack** — Country-specific trending hooks/captions/hashtags
8. **Talking Avatar Videos** — Lip-sync avatars (D-ID/SadTalker)
9. **Story-to-Video** — Full story → cinematic video with scenes + voice + music

### Phase 4: Business Tools (Week 8)
10. **Batch Campaign Maker** — 1 product + 10 prompts → 10 videos automatically

---

## Admin Toggle System

All 10 features are **optional toggles** in admin control panel:

```json
{
  "feature_toggles": {
    "thumbnail_maker": true,
    "meme_maker": true,
    "watermark_branding": true,
    "background_music": true,
    "ai_intro_outro": true,
    "video_to_blog": true,
    "trending_pack": true,
    "talking_avatar": true,
    "story_to_video": true,
    "batch_campaign": true
  }
}
```

---

## Feature #1: AI Thumbnail Maker

### What it does:
- For any completed video, AI auto-creates 5 clickable thumbnails
- Bold text overlay in user's language
- Eagle branding watermark
- User picks the best one

### Database Changes:
```sql
-- Add to media_jobs table
ALTER TABLE media_jobs ADD COLUMN thumbnail_options JSON;  -- 5 generated thumbnails
ALTER TABLE media_jobs ADD COLUMN selected_thumbnail_url TEXT;  -- user's choice
```

### API Endpoints:
- `POST /api/media/thumbnails/generate/{job_id}` — Generate 5 thumbnails
- `POST /api/media/thumbnails/select/{job_id}` — User selects best thumbnail
- `GET /api/media/thumbnails/{job_id}` — Get thumbnail options

### Implementation:
- Uses fal.ai FLUX or Replicate SDXL for image generation
- Pillow/PIL for text overlay in user's language
- Eagle logo watermark (semi-transparent)
- Returns 5 URLs for user to choose from

---

## Feature #8: Meme Maker

### What it does:
- User enters text → AI generates funny meme video/image in seconds
- Free tier: 5 memes/day
- Pro/Max: Unlimited
- Supports image memes and video memes (5-second clips)

### Database Changes:
```sql
CREATE TABLE media_memes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meme_text TEXT NOT NULL,
    meme_type VARCHAR(20) DEFAULT 'image',  -- image or video
    output_path TEXT,
    output_url TEXT,
    template_used VARCHAR(100),
    status VARCHAR(30) DEFAULT 'queued',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### API Endpoints:
- `POST /api/media/memes/generate` — Generate meme from text
- `GET /api/media/memes` — List user's memes
- `GET /api/media/memes/{meme_id}` — Get meme details

### Implementation:
- Image memes: PIL/Pillow with popular meme templates
- Video memes: MoviePy with text overlays + background music
- AI humor detection: Use LLM to suggest funny captions
- Free tier limit: 5/day (enforced in limits service)

---

## Remaining Features (High-Level)

### Feature #2: Background Music
- Free music library: 10 genres stored in `./data/media_assets/bg_music/`
- AI generator: Suno API or self-hosted musicgen-lite
- Beat detection: Librosa for auto-sync to video cuts
- Admin toggle: `background_music`

### Feature #3: Story-to-Video
- User writes story → AI generates scenes, voice, music, subtitles
- Uses existing storyboard + voice_over + generation pipeline
- One-click end-to-end automation
- Admin toggle: `story_to_video`

### Feature #4: Talking Avatar Videos
- Avatars: girl/boy/professional (3 pre-made 3D models or images)
- Lip-sync: D-ID API or SadTalker (self-hosted on GPU server)
- Supports any language
- Use cases: PowerPoints, news, greetings
- Admin toggle: `talking_avatar`

### Feature #5: TikTok/Reels Trending Pack
- Trending hooks, captions, hashtags per country (PK/IN/US/UK)
- Weekly updated trend database
- AI matches user's video to hottest style
- Admin toggle: `trending_pack`

### Feature #6: Batch Campaign Maker
- Business uploads 1 product + 10 prompts
- AI generates 10 ready-to-post videos
- Queue system for batch processing
- Admin toggle: `batch_campaign`

### Feature #7: Watermark & Branding
- Eagle logo + user name/website auto-placed
- PRO users only
- Position: bottom-right (customizable)
- Admin toggle: `watermark_branding`

### Feature #9: Video → Blog
- Whisper transcription → LLM blog generation
- SEO-optimized titles, meta descriptions
- Social media captions (Twitter, LinkedIn, Instagram)
- Admin toggle: `video_to_blog`

### Feature #10: AI Intro/Outro
- One-click professional intro + outro
- User's brand name + eagle logo + music
- Pre-made templates (5 styles)
- Admin toggle: `ai_intro_outro`

---

## Implementation Notes

1. **All features are optional** — admin can disable any feature via toggle
2. **No core feature changes** — all new features are additive
3. **Credit system integration** — each feature costs credits (configurable)
4. **Plan-based access** — free/pro/max/enterprise have different limits
5. **Self-hosted优先** — use local models where possible (musicgen, SadTalker)
6. **API fallback** — cloud APIs (Suno, D-ID) as backup

---

## Next Steps

1. ✅ Implement Thumbnail Maker (Feature #1)
2. ✅ Implement Meme Maker (Feature #8)
3. Add admin toggle endpoints
4. Update frontend media page
5. Test all features
6. Deploy to production

---

**Status**: Design complete — ready for implementation