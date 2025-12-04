# ---- deps base ----
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- dev runner ----
FROM node:20-alpine AS dev
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
# monta node_modules desde la capa deps para evitar reinstalar todo en cada arranque
COPY --from=deps /app/node_modules /app/node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-p", "3000", "--hostname", "0.0.0.0"]
# ---- build ----
