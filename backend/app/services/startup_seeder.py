"""
Professional AI - Startup Seeder
Auto-runs database migrations and seeds default data on first startup.
"""
import logging
import secrets
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, init_db, check_db_connection
from app.config import settings
from app.models.user import User, TwoFactorAuth
from app.models.credit import Credit
from app.models.blog import BlogPost
from loguru import logger

logger = logging.getLogger(__name__)

DEFAULT_PLANS = {
    "FREE": {"credits": 0, "daily_chat": 50, "daily_code": 3, "vault_mb": 3, "daily_videos": 1, "daily_pictures": 10, "daily_animations": 3},
    "STARTER": {"credits": 100, "daily_chat": -1, "daily_code": -1, "vault_mb": 100, "daily_videos": 5, "daily_pictures": 20, "daily_animations": 5},
    "PRO": {"credits": 2000, "daily_chat": -1, "daily_code": -1, "vault_mb": 1000, "daily_videos": 20, "daily_pictures": 50, "daily_animations": 20},
    "MAX": {"credits": 10000, "daily_chat": -1, "daily_code": -1, "vault_mb": 5000, "daily_videos": -1, "daily_pictures": -1, "daily_animations": -1},
    "BUSINESS": {"credits": 2000, "daily_chat": -1, "daily_code": -1, "vault_mb": 2000, "daily_videos": 20, "daily_pictures": 50, "daily_animations": 20},
}


async def run_startup_tasks():
    """Run database migrations and seed default data."""
    logger.info("Running startup database migrations...")

    max_retries = 5
    retry_delay = 2.0
    for attempt in range(1, max_retries + 1):
        try:
            await init_db()
            logger.info("Database migrations completed")
            break
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Database initialization failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Migration attempt {attempt} failed: {e}. Retrying in {retry_delay}s...")
            import asyncio
            await asyncio.sleep(retry_delay * attempt)

    if not await check_db_connection():
        logger.warning("Database connection check failed after migrations")

    db_gen = get_db()
    db = await db_gen.__anext__()
    try:
        await seed_plans(db)
        await seed_owner(db)
        await seed_blog_posts(db)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Startup seeding failed: {e}")
    finally:
        await db.close()


async def seed_plans(db: AsyncSession):
    """Seed default subscription plans into Redis."""
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)

        for plan_name, plan_config in DEFAULT_PLANS.items():
            await redis_client.hset(f"plan:{plan_name}", mapping={k: str(v) for k, v in plan_config.items()})

        await redis_client.close()
        logger.info(f"Seeded {len(DEFAULT_PLANS)} default plans into Redis")
    except Exception as e:
        logger.warning(f"Failed to seed plans into Redis: {e}")


async def seed_owner(db: AsyncSession):
    """Create owner admin account from .env if it doesn't exist."""
    owner_email = (settings.OWNER_EMAIL or "").strip().lower()
    if not owner_email:
        logger.info("No OWNER_EMAIL configured, skipping owner seeding")
        return

    result = await db.execute(select(User).where(User.email == owner_email))
    existing_owner = result.scalar_one_or_none()

    if existing_owner:
        logger.info(f"Owner account already exists: {owner_email}")
        return

    temp_password = secrets.token_urlsafe(16)
    from app.services.auth_service import AuthService
    password_hash = AuthService.hash_password(temp_password)

    owner = User(
        email=owner_email,
        password_hash=password_hash,
        is_admin=True,
        is_approved=True,
        is_active=True,
        is_banned=False,
        email_verified=True,
    )
    db.add(owner)
    await db.flush()

    credit = Credit(user_id=owner.id, balance=0, total_granted=0, total_consumed=0, rollover_percentage=20)
    db.add(credit)

    logger.warning("=" * 60)
    logger.warning(f"OWNER ACCOUNT CREATED - Email: {owner_email}")
    logger.warning(f"Temporary Password: {temp_password}")
    logger.warning("CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!")
    logger.warning("Complete owner setup at /api/admin/owner/setup")
    logger.warning("=" * 60)


async def seed_blog_posts(db: AsyncSession):
    """Seed default blog posts if none exist."""
    try:
        result = await db.execute(select(BlogPost).limit(1))
        if result.scalar_one_or_none():
            logger.info("Blog posts already exist, skipping seed")
            return

        default_posts = [
            {
                "title": "What is Professional AI — The World’s Most Powerful AI Explained",
                "slug": "what-is-professional-ai",
                "excerpt": "Imagine one AI that can write your code, secure your servers, generate 8K videos, speak your language, and work offline — that is Professional AI.",
                "content": "Professional AI is the world's most powerful all-in-one AI platform. It combines coding, security, media generation, voice AI, multilingual chat, and offline mode into a single engine. Unlike narrow chatbots, it routes your request to the best specialized model — whether you need Python code, an 8K video, or an OWASP security scan. It supports 40+ languages including Urdu, Hindi, Arabic, and Bengali. Free users get daily generations; PRO users unlock unlimited power, priority GPU, and commercial rights. Start Free today with a 3-day PRO trial.",
                "cover_gradient": "from-blue-600 via-indigo-600 to-purple-700",
                "author": "Professional AI Team",
                "date": "2026-08-05",
                "read_time": "9 min read",
                "category": "ai-news",
                "tags": ["professional ai", "all-in-one ai", "multilingual ai"],
                "published": True,
            },
            {
                "title": "How to Build a Complete App with AI in 10 Minutes",
                "slug": "how-to-build-a-complete-app-with-ai-in-10-minutes",
                "excerpt": "Ten minutes from blank screen to working app. Thanks to AI coding engines, you no longer need to write every line yourself — you need a clear idea and the right tool.",
                "content": "Building apps with AI is now faster than ordering pizza. Open Professional AI, switch to Code mode, and prompt: \"Build a task manager web app called TaskFlow with add, edit, complete, and delete. Use HTML, CSS, and JavaScript in one file with a modern dark UI.\" The AI generates the full file with comments. Then ask for localStorage persistence and filters. Refine by pasting errors back into the chat. Finally, ask for a Dockerfile and deploy guide. In 10 minutes you have a live app. No prior experience required.",
                "cover_gradient": "from-cyan-500 via-blue-600 to-indigo-700",
                "author": "Professional AI Team",
                "date": "2026-08-06",
                "read_time": "10 min read",
                "category": "coding-tutorials",
                "tags": ["ai coding tool", "build app with ai", "no-code ai"],
                "published": True,
            },
            {
                "title": "Top 10 Cybersecurity Threats in 2026 and How to Protect Yourself",
                "slug": "top-10-cybersecurity-threats-in-2026",
                "excerpt": "Cyberattacks are no longer just for big corporations. In 2026, phishing, deepfakes, and AI-powered malware target students, freelancers, and small businesses every single day.",
                "content": "The 2026 threat landscape is dominated by AI-generated phishing, deepfake voice/video scams, ransomware-as-a-service, credential stuffing, and AI-powered malware that rewrites itself to avoid detection. Cloud misconfigurations remain the #1 cause of data leaks. To protect yourself: use a password manager with unique passwords, enable 2FA everywhere, verify unusual requests through a second channel, follow the 3-2-1 backup rule, keep software patched, and run Professional AI Security mode to scan emails and code for vulnerabilities. Ten minutes a month with this checklist closes 90% of the gaps attackers exploit.",
                "cover_gradient": "from-rose-600 via-red-700 to-orange-700",
                "author": "Professional AI Team",
                "date": "2026-08-07",
                "read_time": "12 min read",
                "category": "security-guides",
                "tags": ["cybersecurity", "ai security assistant", "phishing protection"],
                "published": True,
            },
            {
                "title": "AI Video Generation: How to Create Professional Videos with Voice-Over",
                "slug": "ai-video-generation-professional-videos-with-voice-over",
                "excerpt": "You no longer need a camera crew, a recording studio, or video editing experience to produce professional videos. With AI video generation, you can write a script and get a narrated, subtitled, high-resolution video in minutes.",
                "content": "AI video generation compresses days of production into minutes. Write a script, choose a narrator voice from 40+ languages including Urdu, Hindi, Arabic, and Bengali, pick a visual style, enable auto-subtitles, and generate. Professional AI renders up to 8K, adds synchronized subtitles, and exports for YouTube, TikTok, and Instagram Reels. The neural voice synthesis understands punctuation and emotion — pauses at commas, raises tone for questions, and can even switch languages mid-sentence. PRO and MAX plans include commercial licenses so you can monetize AI videos. Start Free with daily generations, upgrade to PRO for unlimited renders.",
                "cover_gradient": "from-orange-500 via-rose-600 to-purple-700",
                "author": "Professional AI Team",
                "date": "2026-08-08",
                "read_time": "11 min read",
                "category": "media-ai-videos",
                "tags": ["ai video generator", "voice over ai", "text to video"],
                "published": True,
            },
        ]

        for post_data in default_posts:
            post = BlogPost(**post_data)
            db.add(post)

        await db.flush()
        logger.info(f"Seeded {len(default_posts)} default blog posts")
    except Exception as e:
        logger.warning(f"Failed to seed blog posts: {e}")
