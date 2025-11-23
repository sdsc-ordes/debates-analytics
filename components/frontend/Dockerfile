# Stage 1: Build
FROM node:18-slim AS build

# 1. Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# 2. Copy pnpm lockfiles
COPY package.json pnpm-lock.yaml ./

# 3. Install ALL dependencies (including devDeps for building)
RUN pnpm install --frozen-lockfile

# 4. Copy source code
COPY . .

# 5. Build the app (Generates /app/build)
RUN pnpm run build

# Stage 2: Serve
FROM node:18-slim AS serve

WORKDIR /app

# 6. Install pnpm again
RUN npm install -g pnpm

# 7. Copy only package manifests
COPY package.json pnpm-lock.yaml ./

# 8. Install ONLY production dependencies (saves space)
RUN pnpm install --frozen-lockfile --prod

# 9. Copy the build output from the previous stage
# (This requires adapter-node to be configured!)
COPY --from=build /app/build ./build

EXPOSE 3000

CMD ["node", "build"]
