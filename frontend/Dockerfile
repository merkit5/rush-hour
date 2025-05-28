FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Указываем, что контейнер слушает порт 5173 (Vite по умолчанию)
EXPOSE 5173

# Важно: используем host:true для доступа извне контейнера
CMD ["npm", "run", "dev"]