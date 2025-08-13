# Multi-stage build for optimized production image
FROM node:20-alpine AS dependencies

# Build arguments
ARG BUILD_DATE
ARG VCS_REF  
ARG VERSION

# Security: Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with exact versions
RUN npm ci --only=production && npm cache clean --force

# Development dependencies stage
FROM node:20-alpine AS builder

# Install build dependencies
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files and install all dependencies
COPY package*.json ./
RUN npm ci --only=production --no-audit --no-fund || npm install --only=production --no-audit --no-fund

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage - minimal alpine image
FROM node:20-alpine AS runner

# Build and security metadata (OCI compatible)
LABEL org.opencontainers.image.title="Dohodometr Frontend"
LABEL org.opencontainers.image.description="Investment portfolio management frontend"
LABEL org.opencontainers.image.version="${VERSION:-1.0.0}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/yourusername/dohodometr"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Dohodometr Team"
LABEL org.opencontainers.image.licenses="MIT"

# Security: Install security updates and dumb-init
RUN apk add --no-cache \
    dumb-init \
    curl \
    && apk upgrade --no-cache

# Security: Create non-root user with specific UID/GID
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs nextjs

# Set working directory
WORKDIR /app

# Security: Set proper environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Copy runtime dependencies
COPY --from=dependencies --chown=nextjs:nodejs /app/node_modules ./node_modules

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Security: Create tmp directory with proper permissions
RUN mkdir -p /tmp/nextjs && chown nextjs:nodejs /tmp/nextjs

# Switch to non-root user
USER nextjs

# Security: Expose non-privileged port
EXPOSE 3000

# Enhanced health check with proper timeouts
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Security: Use dumb-init and exec form
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
