# Stage 1: Build
FROM node:20 AS build

# Set working directory
WORKDIR /app

# NEW STEP: Install pnpm globally
RUN npm install -g pnpm

# Copy package.json and pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# Install dependencies using pnpm
RUN pnpm install --frozen-lockfile

# Copy the rest of the application
COPY . .

# Build the SvelteKit application
RUN pnpm run build

# Stage 2: Serve
# Use a smaller, secure Node image for the final stage (e.g., node:20-slim)
FROM node:20-slim AS serve

# Set working directory
WORKDIR /app

# Copy essential files from the build stage
# 1. The built SvelteKit output
COPY --from=build /app/build ./build
# 2. Package files (needed for final server start)
COPY --from=build /app/package.json ./
# 3. Node Modules (pnpm creates a flat, deduplicated node_modules structure)
COPY --from=build /app/node_modules ./node_modules

# Expose the port the app runs on (SvelteKit default is 3000)
EXPOSE 3000

# Start the server (SvelteKit serves the 'build' directory)
CMD ["node", "build"]
