## 🚀 Запуск приложения

### 🖥️ Вариант 1: Локальный запуск

#### ✅ Необходимые компоненты:
- [Node.js](https://nodejs.org/) версии **16+**
- **npm** или **yarn**

#### 📦 Установка зависимостей:
```bash
cd frontend
npm install
bash```

#### ▶️ Запуск фронтенда:

```bash
npm run dev


#### 🔗 Фронтенд будет доступен по адресу: http://localhost:5173

### 🐳 Вариант 2: Запуск через Docker

#### ✅ Необходимые компоненты:
- Docker Desktop
- Docker Compose

#### 🔧 Сборка и запуск контейнеров:
```bash
docker-compose up --build

#### 🟢 После сборки приложение будет доступно:

- Фронтенд: http://localhost:5173

#### 🛑 Остановка контейнеров:

```bash
docker-compose down
