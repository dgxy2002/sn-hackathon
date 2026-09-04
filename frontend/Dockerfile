# syntax=docker/dockerfile:1
FROM node:22-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=secret,id=corporate_ca,required=false \
	if [ -s /run/secrets/corporate_ca ]; then \
		export NODE_EXTRA_CA_CERTS=/run/secrets/corporate_ca; \
	fi; \
	npm ci --no-audit --no-fund

COPY frontend/index.html ./index.html
COPY frontend/public ./public
COPY frontend/src ./src

ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080