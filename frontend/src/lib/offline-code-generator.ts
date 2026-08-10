/**
 * Professional AI - Offline Code Generator
 * Rule-based template engine that generates working code WITHOUT internet.
 * Never shows an error — always produces something useful.
 */

type CodeTemplate = {
  keywords: string[]
  generate: (prompt: string) => string
}

const templates: CodeTemplate[] = [
  {
    keywords: ['html', 'webpage', 'website', 'landing page', 'page'],
    generate: (prompt: string) => {
      const title = prompt.replace(/[^a-zA-Z0-9 ]/g, '').trim() || 'My Page'
      return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      color: #e2e8f0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .container {
      max-width: 800px;
      padding: 40px;
      text-align: center;
    }
    h1 {
      font-size: 3rem;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 20px;
    }
    p {
      font-size: 1.2rem;
      color: #94a3b8;
      margin-bottom: 30px;
    }
    .btn {
      display: inline-block;
      padding: 12px 32px;
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      color: white;
      text-decoration: none;
      border-radius: 12px;
      font-weight: 600;
      transition: transform 0.15s;
    }
    .btn:hover { transform: translateY(-2px); }
    footer {
      margin-top: 40px;
      font-size: 0.85rem;
      color: #475569;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>${title}</h1>
    <p>Welcome to your new webpage. Built offline by Professional AI.</p>
    <a href="#" class="btn">Get Started</a>
    <footer>Professional AI - Generated locally without internet</footer>
  </div>
</body>
</html>`
    }
  },
  {
    keywords: ['python', 'script', 'automation', 'cli', 'file', 'api'],
    generate: (prompt: string) => {
      return `#!/usr/bin/env python3
"""
Professional AI - Generated Python Script
Generated offline by Professional AI rule-based engine.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the generated script."""
    logger.info("Professional AI - Offline Generated Script")
    logger.info("Running: ${prompt.replace(/"/g, '\\"')}")

    # Your custom logic here
    result = process_task()

    logger.info(f"Task completed successfully: {result}")
    return result


def process_task() -> Dict[str, Any]:
    """Process the main task."""
    data = {
        "status": "success",
        "message": "Task completed",
        "generated_by": "Professional AI Offline Engine",
        "timestamp": str(Path(__file__).stat().st_mtime),
    }
    return data


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load and parse a JSON file safely."""
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"File not found: {filepath}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved to: {filepath}")


if __name__ == "__main__":
    sys.exit(main())`
    }
  },
  {
    keywords: ['javascript', 'js', 'node', 'function', 'react', 'api endpoint', 'express', 'server'],
    generate: (prompt: string) => {
      return `// Professional AI - Generated JavaScript
// Generated offline by Professional AI rule-based engine.
// Run: node ${(prompt.match(/[a-z0-9_]+/g) || ['script'])[0]}.js

/**
 * Main application logic
 */
async function main() {
  console.log('Professional AI - Offline Generated Script');
  console.log('Task:', '${prompt.replace(/'/g, "\\'")}');

  try {
    const result = await processRequest();
    console.log('Result:', JSON.stringify(result, null, 2));
    return result;
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}


/**
 * Process the main request
 */
async function processRequest() {
  return {
    status: 'success',
    message: 'Task completed successfully',
    generated_by: 'Professional AI Offline Engine',
    timestamp: new Date().toISOString(),
    data: {
      // Add your data here
    }
  };
}


/**
 * Utility: Make an HTTP request
 */
async function fetchData(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(\`HTTP \${response.status}: \${response.statusText}\`);
  }
  return response.json();
}


/**
 * Utility: Retry a function with exponential backoff
 */
async function retry(fn, maxRetries = 3, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
    }
  }
}


// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { main, processRequest, fetchData, retry };`
    }
  },
  {
    keywords: ['docker', 'container', 'deploy', 'dockerfile'],
    generate: (prompt: string) => {
      const name = (prompt.match(/[a-z0-9][a-z0-9_-]*/i)?.[0] || 'app').toLowerCase()
      return `# Professional AI - Generated Dockerfile
# Generated offline by Professional AI rule-based engine.

FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Build (if needed)
# RUN npm run build

FROM node:20-alpine
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \\
    adduser -S nodejs -u 1001

# Copy from builder
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nodejs:nodejs /app/src ./src
COPY --from=builder --chown=nodejs:nodejs /app/public ./public
COPY --from=builder --chown=nodejs:nodejs /app/next.config.js ./next.config.js 2>/dev/null || true

USER nodejs
EXPOSE 3000

ENV NODE_ENV=production
ENV PORT=3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:3000', (r) => { process.exit(r.statusCode === 200 ? 0 : 1) })"

CMD ["node", "src/server.js"]
# For Next.js: CMD ["npm", "start"]`
    }
  },
  {
    keywords: ['api', 'rest', 'endpoint', 'fastapi', 'flask', 'route'],
    generate: (prompt: string) => {
      return `"""
Professional AI - Generated API Endpoint
Generated offline by Professional AI rule-based engine.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import time
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="Professional AI - Generated API",
    description="API generated offline by Professional AI",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Schemas ==========

class ItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    data: Optional[Dict[str, Any]] = None

class ItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: float
    status: str

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str

# ========== In-memory store (replace with DB) ==========

_store: Dict[str, Dict[str, Any]] = {}

# ========== Endpoints ==========

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
    }

@app.get("/api/items", response_model=List[ItemResponse])
async def list_items(limit: int = 10, offset: int = 0):
    """List all items."""
    items = list(_store.values())
    return [
        ItemResponse(
            id=item["id"],
            name=item["name"],
            description=item.get("description"),
            created_at=item["created_at"],
            status=item.get("status", "active"),
        )
        for item in items[offset:offset + limit]
    ]

@app.get("/api/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Get a single item by ID."""
    item = _store.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse(
        id=item["id"],
        name=item["name"],
        description=item.get("description"),
        created_at=item["created_at"],
        status=item.get("status", "active"),
    )

@app.post("/api/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(request: ItemRequest):
    """Create a new item."""
    item_id = str(uuid.uuid4())
    item = {
        "id": item_id,
        "name": request.name,
        "description": request.description,
        "data": request.data or {},
        "created_at": time.time(),
        "status": "active",
    }
    _store[item_id] = item
    logger.info(f"Created item: {item_id}")
    return ItemResponse(
        id=item["id"],
        name=item["name"],
        description=item["description"],
        created_at=item["created_at"],
        status=item["status"],
    )

@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str):
    """Delete an item."""
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="Item not found")
    del _store[item_id]
    logger.info(f"Deleted item: {item_id}")
    return {"message": "Item deleted successfully"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Professional AI Generated API",
        "docs": "/docs",
        "health": "/health",
        "generated_by": "Professional AI Offline Engine",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)`
    }
  },
  {
    keywords: ['css', 'style', 'tailwind', 'bootstrap', 'framework'],
    generate: (prompt: string) => {
      return `/* Professional AI - Generated CSS Styles */
/* Generated offline by Professional AI rule-based engine. */

/* ========== CSS Variables ========== */
:root {
  --color-primary: #3b82f6;
  --color-primary-dark: #2563eb;
  --color-secondary: #8b5cf6;
  --color-accent: #10b981;
  --color-danger: #ef4444;
  --color-warning: #f59e0b;
  --color-bg: #0f172a;
  --color-surface: #1e293b;
  --color-text: #f1f5f9;
  --color-text-muted: #94a3b8;
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --transition: all 0.2s ease;
}

/* ========== Reset ========== */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

/* ========== Layout ========== */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(255,255,255,0.05);
  transition: var(--transition);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* ========== Typography ========== */
h1, h2, h3, h4, h5, h6 {
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 16px;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }

/* ========== Buttons ========== */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid rgba(255,255,255,0.1);
}

.btn-danger {
  background: var(--color-danger);
  color: white;
}

/* ========== Forms ========== */
input, textarea, select {
  width: 100%;
  padding: 10px 16px;
  background: var(--color-surface);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: 0.95rem;
  transition: var(--transition);
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

/* ========== Animations ========== */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-in {
  animation: fadeIn 0.3s ease-out;
}

/* ========== Responsive ========== */
@media (max-width: 768px) {
  .container { padding: 0 16px; }
  h1 { font-size: 2rem; }
  .card { padding: 16px; }
}`
    }
  },
  {
    keywords: ['sql', 'database', 'query', 'schema', 'table', 'mysql', 'postgres'],
    generate: (prompt: string) => {
      return `-- Professional AI - Generated SQL Schema
-- Generated offline by Professional AI rule-based engine.

-- ========== Users Table ==========
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    is_owner BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- ========== Sessions Table ==========
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- ========== Audit Log ==========
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at);

-- ========== Example Queries ==========

-- Get active users
SELECT id, email, display_name, created_at
FROM users
WHERE is_active = TRUE
ORDER BY created_at DESC
LIMIT 100;

-- User login activity
SELECT u.email, COUNT(s.id) as session_count, MAX(s.created_at) as last_login
FROM users u
LEFT JOIN sessions s ON u.id = s.user_id
GROUP BY u.id, u.email
ORDER BY last_login DESC NULLS LAST;

-- Recent audit trail
SELECT action, resource_type, created_at, ip_address
FROM audit_log
WHERE user_id = \$1
ORDER BY created_at DESC
LIMIT 50;`
    }
  },
]

const genericTemplates: CodeTemplate[] = [
  {
    keywords: ['react', 'component', 'hook', 'jsx', 'tsx'],
    generate: (prompt: string) => {
      const componentName = (prompt.match(/[a-z][a-z0-9_]*/i)?.[0] || 'MyComponent').replace(/[^a-zA-Z0-9_]/g, '')
      return `// Professional AI - Generated React Component
// Generated offline by Professional AI rule-based engine.

import { useState, useEffect, useCallback } from 'react';

interface ${componentName}Props {
  title?: string;
  onAction?: (data: any) => void;
}

export default function ${componentName}({ title = '${componentName}', onAction }: ${componentName}Props) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Load your data here
      const result = await fetch('/api/${componentName.toLowerCase()}').then(r => r.json());
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleAction = useCallback((item: any) => {
    onAction?.(item);
  }, [onAction]);

  if (loading) return <div className="p-4">Loading...</div>;
  if (error) return <div className="p-4 text-red-400">Error: {error}</div>;

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">{title}</h2>
      <div className="grid gap-4">
        {data.map((item, index) => (
          <div key={index} className="p-4 bg-slate-800 rounded-lg">
            {JSON.stringify(item)}
          </div>
        ))}
      </div>
    </div>
  );
}`
    }
  },
  {
    keywords: ['typescript', 'interface', 'type', 'class', 'oop'],
    generate: (prompt: string) => {
      return `// Professional AI - Generated TypeScript
// Generated offline by Professional AI rule-based engine.

// ========== Interfaces ==========
interface BaseEntity {
  id: string;
  createdAt: Date;
  updatedAt: Date;
}

interface User extends BaseEntity {
  email: string;
  displayName: string;
  role: 'user' | 'admin' | 'owner';
  isActive: boolean;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// ========== Utility Types ==========
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

type OptionalKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? K : never;
}[keyof T];

type RequiredKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? never : K;
}[keyof T];

// ========== Generic Repository ==========
class Repository<T extends BaseEntity> {
  private items: Map<string, T> = new Map();

  async findById(id: string): Promise<T | null> {
    return this.items.get(id) || null;
  }

  async findAll(): Promise<T[]> {
    return Array.from(this.items.values());
  }

  async create(data: Omit<T, keyof BaseEntity>): Promise<T> {
    const item = {
      ...data,
      id: crypto.randomUUID(),
      createdAt: new Date(),
      updatedAt: new Date(),
    } as T;
    this.items.set(item.id, item);
    return item;
  }

  async update(id: string, data: Partial<T>): Promise<T | null> {
    const existing = this.items.get(id);
    if (!existing) return null;
    const updated = { ...existing, ...data, updatedAt: new Date() };
    this.items.set(id, updated);
    return updated;
  }

  async delete(id: string): Promise<boolean> {
    return this.items.delete(id);
  }
}

export { BaseEntity, User, ApiResponse, DeepPartial, Repository };`
    }
  },
  {
    keywords: ['regex', 'pattern', 'match', 'validate', 'email', 'phone'],
    generate: (prompt: string) => {
      return `// Professional AI - Generated Validation Patterns
// Generated offline by Professional AI rule-based engine.

/**
 * Validation utilities using regex patterns
 */

const Patterns = {
  email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  phone: /^\+?[1-9]\d{1,14}$/,
  url: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
  uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
  ipv4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  hexColor: /^#?([a-f0-9]{6}|[a-f0-9]{3})$/i,
  date: /^\d{4}-\d{2}-\d{2}$/,
  time: /^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$/,
  creditCard: /^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$/,
  password: {
    min8: /^.{8,}$/,
    strong: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  },
};

type ValidationResult = {
  valid: boolean;
  error?: string;
};

function validate(value: string, pattern: RegExp | { regex: RegExp; message: string }, message?: string): ValidationResult {
  const regex = pattern instanceof RegExp ? pattern : pattern.regex;
  const errorMsg = pattern instanceof RegExp ? message : pattern.message;

  if (!regex.test(value)) {
    return { valid: false, error: errorMsg || 'Invalid format' };
  }
  return { valid: true };
}

// ========== Usage Examples ==========
const examples = {
  email: validate('user@example.com', Patterns.email, 'Invalid email format'),
  phone: validate('+1234567890', Patterns.phone, 'Invalid phone number'),
  password: validate('MyP@ss1', Patterns.password.strong, 'Password must contain uppercase, lowercase, number, and special character'),
};

export { Patterns, validate, type ValidationResult };`
    }
  },
]

const genericFallback = (prompt: string): string => {
  const topic = prompt.slice(0, 50).replace(/[^a-zA-Z0-9 ]/g, '').trim() || 'Custom'
  return `// Professional AI - Generated Code
// Generated offline by Professional AI rule-based engine.
// Topic: ${topic}

/*
  This code was generated automatically when you were offline.
  It provides a complete, working template based on your request:
  "${prompt.slice(0, 200)}"

  To customize: replace the placeholder logic with your specific requirements.
*/

class ${topic.replace(/[^a-zA-Z0-9]/g, '_')}Generator {
  constructor(options = {}) {
    this.options = options;
    this.data = [];
  }

  init() {
    console.log('Professional AI - Offline Generated Code');
    console.log('Initializing with options:', this.options);
    return this;
  }

  process(input) {
    const result = {
      input,
      processed: true,
      timestamp: new Date().toISOString(),
      generated_by: 'Professional AI Offline Engine',
    };
    this.data.push(result);
    return result;
  }

  export() {
    return {
      data: this.data,
      count: this.data.length,
      exported_at: new Date().toISOString(),
    };
  }

  clear() {
    this.data = [];
    return this;
  }
}

// Usage:
// const gen = new ${topic.replace(/[^a-zA-Z0-9]/g, '_')}Generator({ debug: true });
// gen.init();
// const result = gen.process('your data here');
// console.log(result);
// console.log(gen.export());`
}

export function generateOfflineCode(prompt: string, language?: string): string {
  const lower = prompt.toLowerCase()
  const langLower = (language || '').toLowerCase()

  // Check all templates for keyword matches
  for (const template of [...templates, ...genericTemplates]) {
    if (template.keywords.some(kw => lower.includes(kw) || langLower.includes(kw))) {
      try {
        return template.generate(prompt)
      } catch {
        // Fall through to next template
      }
    }
  }

  return genericFallback(prompt)
}

export function detectCodeLanguage(prompt: string): string {
  const lower = prompt.toLowerCase()
  const languageSignals: [string[], string][] = [
    [['python', 'pip', 'django', 'flask', 'fastapi', 'pandas', 'numpy'], 'python'],
    [['javascript', 'js ', 'node', 'react', 'vue', 'angular', 'express'], 'javascript'],
    [['html', 'webpage', 'website', 'landing'], 'html'],
    [['css', 'style', 'tailwind', 'bootstrap'], 'css'],
    [['docker', 'container', 'deploy'], 'dockerfile'],
    [['sql', 'database', 'query', 'postgres', 'mysql'], 'sql'],
    [['typescript', 'interface', 'type ', 'ts '], 'typescript'],
    [['regex', 'pattern', 'match', 'validate'], 'regex'],
    [['api', 'endpoint', 'rest', 'fastapi', 'flask', 'route'], 'api'],
  ]

  for (const [signals, lang] of languageSignals) {
    if (signals.some(s => lower.includes(s))) return lang
  }
  return 'auto'
}
