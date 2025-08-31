# Multi-stage build for React
FROM node:16-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Production stage with Nginx
FROM nginx:1.21-alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built React files from build stage
COPY --from=build /app/build /usr/share/nginx/html/

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]