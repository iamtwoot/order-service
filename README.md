# Order Service

Сервис заказов на FastAPI, построенный по принципам чистой архитектуры. Интегрируется с сервисами Capashino: проверяет наличие товара в **Catalog**, создаёт платёж в **Payments**, передаёт оплаченные заказы в **Shipping** через Kafka и отправляет пользователю уведомления через **Notifications**.

## Жизненный цикл заказа

```
POST /api/orders
  │  Catalog: товар есть и его хватает?  ── нет ──→ 400
  │  заказ NEW + уведомление [NEW]  (одна транзакция)
  │  Payments: создать платёж  ── ошибка ──→ заказ CANCELLED + уведомление
  ▼
POST /api/orders/payment-callback          (асинхронно, от Payments)
  │  succeeded → PAID + событие order.paid + уведомление [PAID]  (одна транзакция)
  │  failed    → CANCELLED + уведомление [CANCELLED]
  ▼
outbox-воркер → Kafka: student_system-order.events → Shipping
  ▼
Kafka: student_system-shipment.events → консьюмер + inbox
     order.shipped   → SHIPPED + уведомление [SHIPPED]
     order.cancelled → CANCELLED + уведомление [CANCELLED]
```

Статусы и допустимые переходы (проверяются в доменной сущности `Order`):

```
NEW ──→ PAID ──→ SHIPPED
 │        │
 └──→ CANCELLED ←┘
```

## API

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/orders` | Создать заказ. Повторный запрос с тем же `idempotency_key` возвращает уже созданный заказ |
| `GET` | `/api/orders/{order_id}` | Получить заказ |
| `POST` | `/api/orders/payment-callback` | Результат платежа от Payments |
| `GET` | `/health` | Проверка, что сервис запущен |
| `GET` | `/health/db` | Проверка подключения к базе |

Коды ошибок:

| Код | Когда |
|---|---|
| `400` | Товар не найден в каталоге или его недостаточно |
| `404` | Заказ не найден |
| `409` | Callback противоречит текущему статусу (например, `succeeded` для отменённого заказа) |
| `422` | Невалидные входные данные |
| `503` | Catalog недоступен |

Документация Swagger доступна по `/docs`.

## Архитектура

Структура соответствует каноничному layout чистой архитектуры: импорты направлены внутрь, к `domain`; порты (ABC) лежат в `application/ports/`, их реализации — в `infrastructure/`.

```
src/
├── domain/
│   ├── entities.py            # Order (dataclass), OrderStatus, машина состояний
│   └── exceptions.py          # доменные исключения
├── application/
│   ├── ports/                 # контракты: репозитории, UoW, клиенты, publisher, use case'ы
│   ├── usecases/              # по файлу на сценарий
│   │   ├── create_order.py
│   │   ├── get_order.py
│   │   ├── handle_payment_callback.py
│   │   ├── handle_shipment_event.py
│   │   └── publish_outbox_messages.py
│   └── services/
│       └── notifications.py   # формирование уведомлений, общее для трёх use case'ов
├── infrastructure/
│   ├── persistence/           # SQLAlchemy-модели, репозитории, Unit of Work
│   ├── http/                  # клиенты Catalog, Payments, Notifications (httpx)
│   └── messaging/kafka.py     # Kafka producer (aiokafka)
├── presentation/
│   ├── api/
│   │   ├── routes/            # эндпоинты
│   │   ├── schemas.py         # Pydantic-схемы запросов и ответов
│   │   └── dependencies.py    # связывание use case'ов с эндпоинтами через Depends
│   └── workers/
│       ├── lifecycle.py       # корректная остановка процессов по SIGTERM
│       ├── outbox.py          # цикл outbox-воркера
│       └── shipment_events.py # Kafka consumer событий Shipping
├── container.py               # DI-контейнер (dependency-injector): сборка всех зависимостей
├── fastapi.py                 # фабрика create_app()
├── log_config.py              # общая настройка логирования для всех процессов
└── settings.py                # конфигурация из переменных окружения
bin/                           # точки запуска, каждая — отдельный процесс
├── run.sh                     # запуск всех процессов в одном контейнере
├── api.py                     # HTTP API
├── outbox.py                  # outbox-воркеры: order_events и notifications
└── consumer.py                # консьюмер событий Shipping
```

## Ключевые решения

**Идемпотентность создания заказа.** Уникальный индекс на `idempotency_key`. Обычный повтор запроса отсекается проверкой в начале use case'а, а гонку двух одновременных запросов разрешает база: второй получает `IntegrityError`, и сервис возвращает заказ, созданный первым.

**Идемпотентность callback'ов через машину состояний.** Методы `Order.mark_paid()`, `mark_shipped()`, `cancel()` возвращают `bool`: изменился ли статус. Повторный callback не меняет статус, поэтому ничего не пишется в базу и не создаются повторные события. Строка заказа блокируется `SELECT ... FOR UPDATE`, чтобы одновременные callback'и не перезаписали друг друга.

**Transactional Outbox.** Смена статуса и событие для внешней системы записываются в одной транзакции в таблицу `outbox`. Отдельный воркер отправляет события и помечает их отправленными. Это решает проблему двойной записи: событие не потеряется, даже если сервис упадёт сразу после коммита. Гарантия доставки — at-least-once.

Outbox используется для двух каналов (колонка `destination`):
- `order_events` — событие `order.paid` в Kafka;
- `notifications` — уведомления в Notifications по HTTP.

На каждый канал работает свой воркер, поэтому недоступность Notifications не задерживает события для Shipping. Воркеры в разных подах забирают события через `FOR UPDATE SKIP LOCKED` и не отправляют одно событие дважды.

**Inbox.** Консьюмер записывает id каждого обработанного сообщения в таблицу `inbox` в одной транзакции со сменой статуса. Id сообщения — его координаты в Kafka (`топик:партиция:offset`), поэтому повторная доставка того же сообщения распознаётся как дубль. Offset коммитится только после коммита в базе.

**Обработка ошибок внешних сервисов.**
- Catalog: `404` → 400 клиенту, `5xx` и сетевые ошибки → 503.
- Payments: любая ошибка создания платежа → заказ отменяется.
- Kafka producer: при сбое отправка останавливается, чтобы не нарушить порядок событий; неотправленные события повторяются.
- Kafka consumer: битые сообщения пропускаются, при временном сбое (например, база недоступна) сообщение повторяется через `seek()`.
- Notifications: `5xx` и сетевые ошибки повторяются, `4xx` логируются и не блокируют очередь.

**API, outbox-воркер и консьюмер — отдельные процессы** с общим кодом и одним Docker-образом. У каждого процесса свой event loop, поэтому работа воркеров не замедляет обработку HTTP-запросов, а API не зависит от Kafka. По SIGTERM каждый процесс корректно завершается: продюсер и консьюмер закрывают соединения, консьюмер выходит из consumer group. Сейчас все три процесса работают в одном контейнере (см. «Деплой»), поэтому делят его лимиты CPU и памяти и перезапускаются вместе; для независимого масштабирования их нужно запускать отдельными деплойментами.

**DI-контейнер лежит в `src/container.py`**, рядом с `fastapi.py` и `settings.py`: это общая точка сборки зависимостей для всех трёх процессов. В `presentation/api/dependencies.py` остались только привязки use case'ов к эндпоинтам через `Depends`.

**Фабрика приложения лежит в `src/fastapi.py`**, как требует структура проекта. Чтобы `import fastapi` находил библиотеку, а не этот файл, импорты в проекте идут с префиксом `src.`, а в настройках ruff `fastapi` явно помечен как сторонний пакет.

## Переменные окружения

| Переменная | Обязательна | Описание |
|---|---|---|
| `POSTGRES_CONNECTION_STRING` | да | Строка подключения к Postgres (`postgresql://...`) |
| `CAPASHINO_URL` | да | Базовый URL сервисов Capashino |
| `CAPASHINO_API_TOKEN` | да | API-токен для заголовка `X-API-Key` |
| `PAYMENTS_CALLBACK_URL` | да | Внутренний адрес callback'а в кластере |
| `KAFKA_BOOTSTRAP_SERVERS` | да | Адрес брокера Kafka |
| `KAFKA_ORDER_EVENTS_TOPIC` | нет | По умолчанию `student_system-order.events` |
| `KAFKA_SHIPMENT_EVENTS_TOPIC` | нет | По умолчанию `student_system-shipment.events` |
| `KAFKA_CONSUMER_GROUP` | нет | По умолчанию `iamtwoot-order-service` |

Значения в кластере:

```
CAPASHINO_URL=http://student-system-capashino-web.student-system-capashino.svc:8000
PAYMENTS_CALLBACK_URL=http://student-iamtwoot-order-service-web.student-iamtwoot-order-service.svc:8000/api/orders/payment-callback
KAFKA_BOOTSTRAP_SERVERS=kafka.kafka.svc.cluster.local:9092
```

## Локальный запуск

Требуются Python 3.13, [uv](https://docs.astral.sh/uv/) и Docker.

1. Поднять Postgres и Kafka:

   ```bash
   docker run -d --name orders-db -e POSTGRES_USER=dev -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=orders -p 5432:5432 postgres:16
   docker run -d --name kafka -p 9092:9092 apache/kafka:latest
   ```

2. Создать `.env` в корне проекта:

   ```
   POSTGRES_CONNECTION_STRING=postgresql://dev:dev@localhost:5432/orders
   CAPASHINO_URL=https://capashino.dev-2.python-labs.ru
   CAPASHINO_API_TOKEN=<токен>
   PAYMENTS_CALLBACK_URL=http://localhost:8000/api/orders/payment-callback
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   ```

3. Установить зависимости, применить миграции и запустить:

   ```bash
   uv sync
   uv run alembic upgrade head
   uv run python -m bin.api        # HTTP API
   uv run python -m bin.outbox     # в отдельном терминале
   uv run python -m bin.consumer   # в отдельном терминале
   ```

Сервис будет доступен на `http://localhost:8000`, Swagger — на `http://localhost:8000/docs`. Локально Payments не может отправить callback на `localhost`, поэтому оплату можно проверить, вызвав `POST /api/orders/payment-callback` вручную через Swagger.

## Проверки кода

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Все три проверки выполняются в pre-commit (`uv run pre-commit install`), проверки ruff — также в CI перед сборкой образа.

## Деплой

При пуше в `main` GitHub Actions проверяет код линтерами, собирает Docker-образ, публикует его в GitHub Container Registry и отправляет запрос на деплой в LMS.

LMS запускает один контейнер на сервис, поэтому все три процесса стартуют из `bin/run.sh`:

1. применяются миграции (`alembic upgrade head`);
2. в фоне запускаются `bin.api`, `bin.outbox` и `bin.consumer`;
3. SIGTERM пересылается всем процессам, чтобы они корректно завершились;
4. если любой процесс падает, скрипт останавливает остальные и выходит с ошибкой, и Kubernetes перезапускает контейнер.

Образ один для всех процессов, поэтому при возможности отдельных деплойментов достаточно задать каждому свою команду: `python -m bin.api`, `python -m bin.outbox`, `python -m bin.consumer`. Миграции в этом случае нужно запускать только вместе с API.

## Текущие ограничения

- Таблицы `outbox` и `inbox` не очищаются. В продакшене нужна периодическая очистка старых записей.
- Для выборки неотправленных событий пригодился бы частичный индекс `ON outbox (destination, created_at) WHERE sent_at IS NULL`.
- Если сервис упадёт между коммитом заказа и запросом в Payments, заказ останется в статусе `NEW` без платежа. Надёжное решение — создавать платёж тоже через outbox.
- Повторный запрос с тем же `idempotency_key`, но другими данными возвращает исходный заказ, а не ошибку.
