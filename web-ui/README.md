# MDF Cutting Web UI

Современный веб-интерфейс для системы раскроя МДФ с интеграцией AI.

## Технологический стек

### Frontend
- **React 18** - Основной фреймворк
- **Material-UI (MUI)** - UI библиотека
- **Redux Toolkit** - Управление состоянием
- **React Router** - Маршрутизация
- **Axios** - HTTP клиент
- **Framer Motion** - Анимации
- **Vite** - Сборщик

### Backend API
- **FastAPI** - Python веб-фреймворк
- **WebSocket** - Real-time обновления
- **JWT** - Аутентификация

## Установка и запуск

### Требования
- Node.js 18+
- npm или yarn

### Установка зависимостей
```bash
npm install
```

### Запуск в режиме разработки
```bash
npm run dev
```

Приложение будет доступно по адресу: http://localhost:3000

### Сборка для продакшена
```bash
npm run build
```

### Предварительный просмотр сборки
```bash
npm run preview
```

## Структура проекта

```
web-ui/
├── src/
│   ├── components/          # React компоненты
│   │   ├── layout/         # Компоненты макета
│   │   ├── forms/          # Формы ввода
│   │   ├── tables/         # Таблицы данных
│   │   ├── charts/         # Графики и диаграммы
│   │   └── ai/             # AI компоненты
│   ├── pages/              # Страницы приложения
│   ├── services/           # API сервисы
│   ├── store/              # Redux store
│   ├── utils/              # Утилиты
│   └── styles/             # Глобальные стили
├── public/                 # Статические файлы
└── api/                    # FastAPI backend
```

## Основные функции

### 1. Dashboard
- Обзор статистики
- Быстрые действия
- Последняя активность

### 2. Оптимизация раскроя
- Загрузка файлов деталей и материалов
- Настройка параметров оптимизации
- Запуск процесса оптимизации
- Просмотр результатов

### 3. AI Оптимизация
- Настройка AI параметров
- Запуск AI оптимизации
- Просмотр AI предложений
- Применение/отклонение предложений
- Обратная связь

### 4. Управление материалами
- Добавление/редактирование материалов
- Просмотр списка материалов
- Управление остатками

### 5. Проекты
- Создание и управление проектами
- История оптимизаций
- Экспорт результатов

### 6. Отчеты
- Аналитика и статистика
- Графики эффективности
- Экспорт отчетов

## Цветовая схема

Адаптирована из ui_shablon с использованием Material Design:

- **Primary**: `#607D8B` (основной синий)
- **Secondary**: `#90A4AE` (вторичный серый)
- **Success**: `#2e7d32` (зеленый)
- **Error**: `#c62828` (красный)
- **Warning**: `#8C7601` (золотой)
- **Background**: `#f5f5f5` (светло-серый фон)

## API интеграция

### Основные эндпоинты

#### Раскрой
- `POST /api/upload-details` - Загрузка файла деталей
- `POST /api/upload-materials` - Загрузка файла материалов
- `POST /api/optimize-cutting` - Запуск оптимизации
- `GET /api/optimization-history` - История оптимизаций

#### AI
- `POST /api/ai/optimize` - AI оптимизация
- `POST /api/ai/optimize-leftovers` - Оптимизация с остатками
- `POST /api/ai/feedback` - Отправка обратной связи
- `GET /api/ai/suggestions/{id}` - Получение предложений

#### Материалы
- `GET /api/materials` - Список материалов
- `POST /api/materials` - Добавление материала
- `PUT /api/materials/{id}` - Обновление материала
- `DELETE /api/materials/{id}` - Удаление материала

## Разработка

### Добавление новых компонентов

1. Создайте компонент в соответствующей папке
2. Добавьте типы в TypeScript (если используется)
3. Создайте тесты
4. Обновите документацию

### Добавление новых страниц

1. Создайте страницу в `src/pages/`
2. Добавьте маршрут в `src/App.jsx`
3. Добавьте пункт меню в `src/components/layout/Sidebar.jsx`
4. Создайте Redux slice если необходимо

### Стилизация

Используйте Material-UI компоненты и темы:

```jsx
import { Box, Typography, Button } from '@mui/material'

const MyComponent = () => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" color="primary.main">
        Заголовок
      </Typography>
      <Button variant="contained" color="primary">
        Кнопка
      </Button>
    </Box>
  )
}
```

## Тестирование

### Запуск тестов
```bash
npm test
```

### Покрытие кода
```bash
npm run test:coverage
```

## Развертывание

### Docker
```bash
# Сборка образа
docker build -t mdf-cutting-web .

# Запуск контейнера
docker run -p 3000:3000 mdf-cutting-web
```

### Nginx
```bash
# Копирование файлов
cp -r dist/* /var/www/html/

# Настройка nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## Лицензия

MIT License

## Поддержка

Для получения поддержки обращайтесь к команде разработки. 