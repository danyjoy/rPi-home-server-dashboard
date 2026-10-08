# Frontend image: build the Vite app, then serve it with nginx.
# Stage 1 - build. Multi-arch node base.
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies with a clean, reproducible install.
COPY package.json package-lock.json* ./
RUN npm ci

# Build the static assets.
COPY . .
RUN npm run build

# Stage 2 - serve. nginx:alpine already runs worker processes as non-root
# (user "nginx"); only the master needs root to bind port 80 inside the
# container. No host privilege is granted.
FROM nginx:alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
