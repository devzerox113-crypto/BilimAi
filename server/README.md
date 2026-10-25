# BilimAi server

Один файл на стандартной библиотеке Python: аккаунты (email + Google), тарифы Free/Pro, лимиты, оплата (Stripe или вручную), админка.

## Запуск
```
ANTHROPIC_API_KEY=sk-ant-... ADMIN_KEY=длинный-случайный-пароль PUBLIC_URL=https://ваш-домен python server.py
```
Нужен **HTTPS** и **постоянный диск** для базы (`DB_PATH`, по умолчанию `bilimai.db`). Подходят Fly.io / Railway с volume или свой VPS
(на бесплатном Render диск стирается при перезапуске - пользователи пропадут). Docker: `server/Dockerfile`, том `/data`.

После запуска впишите адрес в приложении: файл `config.py` -> `SERVER_URL = "https://ваш-домен"` и пересоберите APK.

## Переменные окружения
| Имя | Зачем | По умолчанию |
|---|---|---|
| ANTHROPIC_API_KEY | ваш ключ (обязательно) | - |
| ADMIN_KEY | пароль админки (обязательно) | - |
| PUBLIC_URL | https-адрес сервера (для Google/Stripe) | - |
| FREE_LIMIT / PRO_LIMIT | запросов в день | 10 / 300 |
| FREE_MAX_TOKENS / PRO_MAX_TOKENS | длина ответа | 1024 / 4096 |
| FREE_WEB | веб-поиск для Free (1 = да) | 0 |
| ALLOWED_MODELS | список моделей через запятую | любые |
| GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET | вход через Google | - |
| STRIPE_SECRET_KEY / STRIPE_PRICE_ID / STRIPE_WEBHOOK_SECRET | подписка Stripe | - |
| PAY_URL | своя страница оплаты (Kaspi, Telegram-бот), если без Stripe | - |
| WEBHOOK_SECRET | пароль для `POST /billing/webhook` | - |
| CONTACT_EMAIL, APP_NAME | для страниц /privacy и /terms | - |

## Вход через Google
1. console.cloud.google.com -> новый проект -> **APIs & Services -> OAuth consent screen** (External). Privacy policy: `PUBLIC_URL/privacy`.
2. **Credentials -> Create credentials -> OAuth client ID -> Web application**. Authorized redirect URI: `PUBLIC_URL/auth/google/callback`.
3. Client ID и secret -> в `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Пока приложение в режиме Testing, войти могут только добавленные тестовые пользователи (до 100); для всех нужна верификация Google.

## Подписка через Stripe
1. Product + Price (monthly) -> `STRIPE_PRICE_ID`, секретный ключ -> `STRIPE_SECRET_KEY`.
2. Webhook endpoint: `PUBLIC_URL/billing/stripe`, события `checkout.session.completed` и `invoice.paid` -> signing secret в `STRIPE_WEBHOOK_SECRET`.
3. Кнопка «Перейти на Pro» в приложении открывает оплату; Pro включается по событию `invoice.paid` (+2 дня запаса).

## Оплата вручную (Kaspi, перевод)
Выдавайте Pro в админке кнопкой «+30d», либо шлите `POST /billing/webhook` с заголовком `x-webhook-secret` и телом `{"email":"...","days":30}`.

## Админка
`PUBLIC_URL/admin` -> вход по `ADMIN_KEY`: пользователи, поиск, выдать/снять Pro, свой лимит, бан, удаление, статистика запросов и токенов.

## Что не сделано
Подтверждение email и сброс пароля (нужна почта SMTP), шифрование базы, автоматическая отмена по `customer.subscription.deleted` (Pro просто истекает по дате).
