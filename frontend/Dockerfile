FROM node:18-alpine

WORKDIR /app

COPY package.json ./
RUN apk add --no-cache python3 make g++ && npm install --legacy-peer-deps

COPY . .
RUN npm run build && ls -la dist

EXPOSE 3000

CMD ["npx", "serve", "-s", "dist", "-l", "3000"]
