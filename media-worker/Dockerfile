FROM node:20-alpine

WORKDIR /app/media-worker

# Install dependencies
COPY media-worker/package*.json ./
RUN npm install --production

# Copy worker code
COPY media-worker/ ./

# Create output directory
RUN mkdir -p /app/media_output

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('ioredis').createClient(process.env.REDIS_URL || 'redis://localhost:6379').ping().then(()=>process.exit(0)).catch(()=>process.exit(1))"

CMD ["npm", "start"]
