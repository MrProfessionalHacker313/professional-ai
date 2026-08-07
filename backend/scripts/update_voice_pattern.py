"""Update voice_style pattern in media.py to include all 14 voices."""
import re

with open('backend/app/routes/media.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old pattern with the new one including all 14 voices
old_pattern = r'pattern="^(young_girl\|young_boy\|adult_male\|adult_female\|news_anchor\|robotic\|cartoon\|villain\|hero\|custom\|clone)$"'
new_pattern = r'pattern="^(young_girl|young_boy|adult_male|adult_female|news_anchor|teacher|robot|cartoon|villain|hero|whisper|angry|happy|sad|excited|robotic|custom|clone)$"'

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    with open('backend/app/routes/media.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: voice_style pattern updated with 14 voices')
else:
    print('Pattern already updated or not found')
    # Check if already has the new pattern
    if 'teacher' in content and 'whisper' in content and 'excited' in content:
        print('Pattern already includes new voices')
    else:
        print('WARNING: Could not find pattern to replace')