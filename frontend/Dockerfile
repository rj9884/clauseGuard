FROM node:20-slim

WORKDIR /app

# Copy package files first to leverage Docker's layer cache
COPY package.json package-lock.json ./

# Install dependencies (npm ci is faster and cleaner for automated environments)
RUN npm ci

# Copy the rest of the application
COPY . .

# Expose Vite's default dev port
EXPOSE 5173

# Start the Vite development server
CMD ["npm", "run", "dev", "--", "--host"]
