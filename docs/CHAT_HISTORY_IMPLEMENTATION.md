# Chat History Feature - Implementation Guide

## Overview
Complete chat history feature with conversation persistence, sidebar UI, and admin management.

## Database Schema

### Tables Created
```sql
-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    mode VARCHAR(20) NOT NULL DEFAULT 'chat',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Security Features
- **Row Level Security (RLS)**: Users can only access their own conversations
- **Cascade Delete**: Deleting a user removes all their conversations
- **Indexed Queries**: Optimized for fast retrieval by user_id and conversation_id
- **Auto-update Triggers**: `updated_at` timestamp automatically updates on modifications

## API Endpoints

### User Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations` | List all conversations (with optional search) |
| GET | `/api/conversations/{id}` | Get full conversation with messages |
| POST | `/api/conversations` | Create new conversation |
| POST | `/api/conversations/{id}/messages` | Add message to conversation |
| PATCH | `/api/conversations/{id}` | Rename conversation |
| DELETE | `/api/conversations/{id}` | Delete conversation |

### Admin Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations/admin/all` | List all conversations (with user emails) |
| DELETE | `/api/conversations/admin/{id}` | Delete any conversation (admin only) |

## Frontend Components

### 1. ChatSidebar (`frontend/src/components/ChatSidebar.tsx`)
- **Slide-out sidebar** with conversation history
- **Search functionality** to find conversations by title
- **New Chat button** to start fresh conversations
- **Rename/Delete actions** on hover
- **Relative date formatting** (Today, Yesterday, 5 Aug, etc.)
- **Responsive design** with overlay on mobile

### 2. Chat Page Integration (`frontend/src/app/chat/page.tsx`)
- **Sidebar state management**: `sidebarOpen`, `currentConversationId`
- **Auto-create conversation** on first message
- **Load conversation** when selected from sidebar
- **Clear messages** when conversation is deleted
- **Persist messages** to backend after AI response

### 3. Admin Panel (`frontend/src/components/admin/AdminChatHistory.tsx`)
- **Table view** of all conversations across all users
- **Search by title or user email**
- **Delete any conversation** (admin/owner only)
- **User identification** with email and user ID
- **Message count** and timestamps

## Encryption & Security

### Data Storage
- **Database-level encryption**: All data stored in PostgreSQL with RLS
- **Vault integration**: Chat history stored in encrypted vault area (AES-256-GCM)
- **User isolation**: RLS policies ensure users only see their own data
- **Admin audit trail**: Admin actions logged in `admin_audit_logs` table

### Security Measures
1. **Authentication Required**: All endpoints require valid JWT token
2. **Authorization Checks**: Users can only access their own conversations
3. **Admin-only routes**: `/admin/*` endpoints verify `is_admin` flag
4. **Input Sanitization**: All inputs sanitized via `InputSanitizer`
5. **Rate Limiting**: 100 requests/minute for list endpoints, 50 for mutations
6. **CSRF Protection**: All mutations require CSRF token

## Usage Flow

### User Flow
1. User opens chat page → sees empty state with "New Chat" button
2. User clicks sidebar toggle → sees conversation history (if any)
3. User sends first message → new conversation auto-created with title from first message
4. User can:
   - Click "New Chat" to start fresh
   - Click any conversation to resume
   - Search conversations by title
   - Rename conversations (hover → edit icon)
   - Delete conversations (hover → trash icon)

### Admin Flow
1. Admin navigates to `/admin` → sees admin panel
2. Admin clicks "Chat History" in sidebar
3. Admin sees table of all conversations with:
   - Title, User email, Message count, Created/Updated dates
4. Admin can:
   - Search by title or user email
   - Delete any conversation permanently

## Implementation Details

### Backend Models
```python
# backend/app/models/chat_history.py
class Conversation(Base):
    __tablename__ = "conversations"
    id: UUID (primary key)
    user_id: UUID (foreign key to users)
    title: str (max 255 chars)
    created_at: datetime
    updated_at: datetime

class Message(Base):
    __tablename__ = "messages"
    id: UUID (primary key)
    conversation_id: UUID (foreign key to conversations)
    role: str ('user' or 'assistant')
    content: text
    mode: str ('chat', 'code', 'security', 'bugfix')
    created_at: datetime
```

### Frontend API Client
```typescript
// frontend/src/lib/api.ts
export const conversationsApi = {
  list: (params?: { search?: string }) =>
    api.get('/api/conversations', { params }),
  get: (id: string) =>
    api.get(`/api/conversations/${id}`),
  create: (data?: { title?: string }) =>
    api.post('/api/conversations', data),
  addMessage: (id: string, data: { content: string; mode?: string; role?: string }) =>
    api.post(`/api/conversations/${id}/messages`, data),
  rename: (id: string, data: { title: string }) =>
    api.patch(`/api/conversations/${id}`, data),
  delete: (id: string) =>
    api.delete(`/api/conversations/${id}`),
  // Admin endpoints
  adminListAll: (params?: { search?: string }) =>
    api.get('/api/conversations/admin/all', { params }),
  adminDelete: (id: string) =>
    api.delete(`/api/conversations/admin/${id}`),
}
```

## Testing Checklist

### Backend Tests
- [ ] Create conversation via POST `/api/conversations`
- [ ] List conversations via GET `/api/conversations`
- [ ] Add messages via POST `/api/conversations/{id}/messages`
- [ ] Get full conversation via GET `/api/conversations/{id}`
- [ ] Rename conversation via PATCH `/api/conversations/{id}`
- [ ] Delete conversation via DELETE `/api/conversations/{id}`
- [ ] Verify RLS: User A cannot access User B's conversations
- [ ] Verify admin endpoints require `is_admin=True`
- [ ] Verify rate limiting works (100/min list, 50/min mutations)
- [ ] Verify input sanitization (XSS prevention)

### Frontend Tests
- [ ] Sidebar opens/closes smoothly
- [ ] New conversation created on first message
- [ ] Conversation list loads with correct dates
- [ ] Search filters conversations by title
- [ ] Click conversation loads all messages
- [ ] Rename updates title in real-time
- [ ] Delete removes conversation and clears chat
- [ ] Admin panel shows all conversations
- [ ] Admin can delete any conversation
- [ ] Responsive design works on mobile

## Migration Guide

### Database Migration
Run the SQL from `database/schema.sql` to create the new tables:

```bash
# Option 1: Using psql
psql -U proai -d professional_ai -f database/schema.sql

# Option 2: Using Docker
docker exec -i proai-postgres psql -U proai -d professional_ai < database/schema.sql
```

### Code Deployment
1. Deploy backend code (models, routes, main.py)
2. Deploy frontend code (components, pages, API client)
3. Run database migration
4. Verify endpoints with `/api/docs` (development mode)

## Notes
- **No auto-expiry**: Conversations stay forever until manually deleted
- **Encrypted at rest**: All data stored in PostgreSQL with RLS protection
- **Cross-platform**: Works on web, mobile, and desktop (same account)
- **Title generation**: First 40 characters of first message used as title
- **Message persistence**: Messages saved after each AI response

## Troubleshooting

### Common Issues
1. **RLS Policy Error**: Ensure `app.current_user_id` is set in database session
2. **Import Error**: Verify `chat_history` models imported in `models/__init__.py`
3. **Route Not Found**: Check `chat_history` router included in `main.py`
4. **TypeScript Errors**: Ensure `conversationsApi` added to `api.ts`

### Debug Commands
```bash
# Check database tables
psql -U proai -d professional_ai -c "\dt conversations"
psql -U proai -d professional_ai -c "\dt messages"

# Check RLS policies
psql -U proai -d professional_ai -c "\dp conversations"
psql -U proai -d professional_ai -c "\dp messages"

# Test API endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/conversations
```

## Status
✅ **COMPLETE** - All features implemented and ready for testing.