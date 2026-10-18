# Практическая работа 3. FastAPI и Redis

Автор: Бабушкин Михаил Вадимович. Первичная проверка: 17 октября 2026 года. Облачное развертывание: 18 октября 2026 года.

## Решение

Два контейнера: веб-приложение заметок на Python 3.12/FastAPI/Uvicorn и Redis. Приложение обращается к Redis по Docker DNS-имени `redis`, порт 6379 не публикуется. Заметки хранятся в списке Redis в порядке добавления; AOF и внешний именованный volume сохраняют данные при пересоздании контейнеров. AOF с настройками по умолчанию допускает потерю последних секундных записей при аварийном отключении питания.

`GET /` возвращает страницу, `GET /api/notes` — `{"notes":[...]}`, `POST /api/notes` принимает `{"text":"..."}` и возвращает HTTP 201. Текст обрезается по краям и проверяется на длину 1–500 символов; неверный ввод возвращает 422. Lua-скрипт Redis атомарно проверяет лимит 100 и добавляет заметку, при заполнении возвращается 409. `GET /health` проверяет Redis; при его недоступности маршруты данных и health возвращают 503. Страница выводит заметки через `textContent`.

Приложение учебное: без авторизации, редактирования и удаления. В публичной демонстрации использовать только тестовые записи. Вместо примера Food Trucks из методички по выбору студента используется собственное приложение; принятие замены преподавателем не подтверждено.

## Ручное развертывание на Mac — история 17 октября

Команды выполнять из этой папки при работающем Docker Desktop. Перед созданием убедиться, что имена ресурсов и порт 8003 свободны. Существующие чужие ресурсы не удалять.

```bash
docker build --platform linux/arm64 -t susu-cloud-practice3:2026-10-17 .
docker network create ct-practice3-manual
docker volume create ct-practice3-notes
docker run -d --name ct-practice3-redis --network ct-practice3-manual \
  --network-alias redis -v ct-practice3-notes:/data \
  redis:7.4-alpine redis-server --appendonly yes
docker exec ct-practice3-redis redis-cli ping
docker run -d --name ct-practice3-web --network ct-practice3-manual \
  -e REDIS_URL=redis://redis:6379/0 -p 127.0.0.1:8003:8000 \
  susu-cloud-practice3:2026-10-17
docker exec ct-practice3-web python -c 'import socket; print(socket.gethostbyname("redis"))'
docker network inspect ct-practice3-manual
python3 test_app.py http://127.0.0.1:8003
```

Если Redis еще не готов, повторить `redis-cli ping` до ответа PONG. Открыть http://127.0.0.1:8003, добавить заметку и проверить ее появление. `test_app.py` добавляет две тестовые записи; не запускать его при почти заполненном списке.

## Переход на Compose — история 17 октября

Удаляются только два контейнера ручного этапа и его сеть. Volume сохраняется; никаких `prune` или очистки данных не требуется.

```bash
docker stop ct-practice3-web ct-practice3-redis
docker rm ct-practice3-web ct-practice3-redis
docker network rm ct-practice3-manual
docker compose config --quiet
docker compose up -d --wait
python3 test_app.py http://127.0.0.1:8003
docker compose ps
docker compose exec web python -c 'import socket; print(socket.gethostbyname("redis"))'
```

Compose использует тот же внешний volume `ct-practice3-notes`; если он отсутствует, создать через `docker volume create ct-practice3-notes`. Redis healthcheck и `depends_on: service_healthy` задают готовность хранилища перед запуском web.

Для проверки сохранности записать список, выполнить `docker compose down` и `docker compose up -d --wait`, затем сравнить список. Внешний volume не удалять.

Для проверки отказа выполнить `docker compose stop redis`: health, чтение и добавление должны вернуть 503. Затем `docker compose start redis`; после PONG приложение должно восстановиться без пересоздания web.

Проверку заполнения выполнять только на отдельном временном web-контейнере, подключенном к Redis DB 1, с пустым ключом `practice3:notes`. Команда `python3 test_app.py http://127.0.0.1:8004 --capacity` проверяет конкурирующие добавления на границе 100. Она заполняет тестовую БД; не направлять ее на основную DB 0.

## Облачное развертывание 18 октября 2026 года

Приложение: http://176.222.53.58:8083/. Пользователь `practice3` входит в группы sudo и docker; SSH по ключу работает. Все Docker-команды выполняются без sudo. Docker Engine 29.9.1, Compose 5.6.0, Ubuntu x86_64; доступно 4,7 ГиБ RAM и 108 ГБ диска на момент проверки. Порт 8083 до запуска свободен; на VPS уже работал калькулятор практики 2.

Локальный `compose.yaml` и серверный `compose.cloud.yaml` содержат фиксированные значения без подстановки переменных: ARM64/127.0.0.1:8003 и AMD64/0.0.0.0:8083 соответственно. Compose-проект `ct-2026-practice-3`. Локальный volume `ct-practice3-notes` сохранен; облачный — отдельный `ct-2026-practice-3-notes`. Официальный образ Redis остается `redis:7.4-alpine`.

### Зачем нужен compose.cloud.yaml

`compose.cloud.yaml` описывает запуск тех же двух сервисов на VPS. Отдельный файл выбран, чтобы хранить фиксированные параметры Mac и VPS без подстановок из `.env` и без ручного изменения конфигурации перед каждым запуском.

| Параметр | `compose.yaml` — Mac | `compose.cloud.yaml` — VPS |
|---|---|---|
| Образ приложения | `ct-2026-practice-3-notes:2026-10-18-arm64` | `ct-2026-practice-3-notes:2026-10-18-amd64` |
| Адрес и порт | `127.0.0.1:8003` — только локальный доступ | `0.0.0.0:8083` — доступ через IP сервера |
| Volume заметок | `ct-practice3-notes` | `ct-2026-practice-3-notes` |
| Сборка | Есть `build: .` | Сборки нет: используется образ, переданный с Mac |

Оба файла запускают FastAPI и Redis с одинаковой логикой приложения. Redis доступен только внутри сети Compose, данные сохраняются в volume соответствующей среды.

Без параметра `-f` Docker Compose ищет стандартный `compose.yaml`. Поэтому на VPS серверный файл явно выбирается командой `docker compose -f compose.cloud.yaml …`. Например, `docker compose -f compose.cloud.yaml ps` показывает состояние облачных сервисов. Имя `compose.cloud.yaml` — соглашение проекта, а не требование Docker: на VPS его можно было бы назвать `compose.yaml` и запускать без `-f`. В текущем развертывании сохранено отдельное имя для ясного различия конфигураций.


Команды проверки доступа с Mac:

```bash
ssh practice3@176.222.53.58 'id; docker info --format "{{.ServerVersion}}"; docker compose version; free -h; df -h /; ss -lnt; docker ps --format "{{.Names}} {{.Image}} {{.Ports}}"'
docker ps -a --format '{{.Names}} {{.Image}}'
```

Сборка и перенос локального Compose (из папки практики):

```bash
mkdir -p .cache .report
curl -fsS http://127.0.0.1:8003/api/notes -o .cache/notes-before.json
docker buildx build --platform linux/arm64 --load -t ct-2026-practice-3-notes:2026-10-18-arm64 .
docker compose -p ct-practice3 down
docker compose up -d --no-build --wait
curl -fsS http://127.0.0.1:8003/api/notes -o .cache/notes-after.json
cmp .cache/notes-before.json .cache/notes-after.json
python3 test_app.py http://127.0.0.1:8003
docker buildx build --platform linux/amd64 --load -t ct-2026-practice-3-notes:2026-10-18-amd64 .
docker save -o .cache/ct-2026-practice-3-notes-2026-10-18-amd64.tar ct-2026-practice-3-notes:2026-10-18-amd64
shasum -a 256 .cache/ct-2026-practice-3-notes-2026-10-18-amd64.tar
ssh practice3@176.222.53.58 'mkdir -p ~/ct-2026-practice-3'
scp .cache/ct-2026-practice-3-notes-2026-10-18-amd64.tar compose.cloud.yaml practice3@176.222.53.58:ct-2026-practice-3/
```

SHA-256 архива на Mac и VPS совпал: `dbf68f548de330ece32f66864f66d0667ae4fbe0d39617df12f46c22de946849`.

Команды на VPS:

```bash
cd ~/ct-2026-practice-3
sha256sum ct-2026-practice-3-notes-2026-10-18-amd64.tar
docker load -i ct-2026-practice-3-notes-2026-10-18-amd64.tar
docker volume create ct-2026-practice-3-notes
docker compose -f compose.cloud.yaml up -d --no-build --wait
```

Первый запуск выполнен с параметрами в `.env`; по просьбе студента подстановки убраны, временные `.env` и прежний серверный `compose.yaml` удалены. Повторный запуск использует только `compose.cloud.yaml`. Фиксированный `REDIS_URL=redis://redis:6379/0` передается приложению через окружение контейнера; исходники приложения не изменены.

### Проверки

Полные команды и результаты: [журнал проверок 18 октября](БабушкинМВ-cloud-checks.txt). Обычный HTTP-тест добавляет две записи и не очищает данные. Лимит проверяется отдельным временным web-контейнером в Redis DB 15: перед тестом проверяется пустая БД, после удаляется только тестовый ключ `practice3:notes` и временный контейнер. Основная DB 0 не очищается.

Для проверок на VPS используется `docker compose -f compose.cloud.yaml`; локально — `docker compose`. Проверки включают `down`/`up -d --no-build --wait`, остановку/запуск Redis, `restart`, сравнение списков заметок, DNS и инспекцию политики перезапуска. Временный контейнер тестирования ожидает готовность `/health` перед запуском `test_app.py --capacity`.

Docker daemon не перезапускался, поскольку практика 2 работает на том же сервере. Firewall, Apache, MySQL и настройки WordPress не менялись. Публично опубликован только порт приложения; 6379 остается внутри сети Docker.

## Фактические локальные результаты 17 октября 2026 года

Среда: macOS ARM64, Docker Engine 29.3.1. Приложение собрано для linux/arm64; Python 3.12.15, FastAPI 0.142.2, Redis-клиент 8.1.0. Используется официальный образ redis:7.4-alpine. Web работает под UID 10001 без root.

| Проверка | Результат |
|---|---|
| Сборка ARM64, проверка Compose | Пройдены |
| Ручной запуск, DNS redis и HTTP-тест | Пройдены |
| Ввод, обрезка пробелов, порядок, 422 | Пройдены |
| HTML в заметке | Отображается текстом; элементов img в списке нет |
| Атомарный лимит в изолированной DB 1 | При 99 записях из 16 запросов принят 1, остальные 15 получили 409; итог 100 |
| Переход вручную → Compose | Все 3 исходные заметки сохранены |
| Пересоздание Compose | Все 5 записей на момент проверки сохранены |
| Отказ Redis | Health, чтение и запись вернули 503; страница показывает понятную ошибку |
| Запуск Redis после отказа | Health и полный HTTP-тест прошли без пересоздания web |
| pip check в контейнере | Конфликтов нет |
| Облако, AMD64 и сдача | На 17 октября не выполнены; актуальное состояние — ниже |

Тестовая DB 1 после проверки очищена только от созданного тестом ключа; основной список DB 0 не очищался. Контейнеры ручного этапа удалены, Compose оставлен запущенным на 127.0.0.1:8003. Практика 2 не изменялась.

Журналы: [ручной запуск](БабушкинМВ-manual-checks.txt), [Compose](БабушкинМВ-compose-checks.txt). Скриншоты показывают реальное приложение на соответствующих этапах; состав контейнеров и сетей зафиксирован в журналах.

![Ручной запуск](БабушкинМВ-manual.png)

![Compose и сохраненные заметки](БабушкинМВ-compose.png)

![Отказ Redis](БабушкинМВ-redis-unavailable.png)

## Итоговые результаты 18 октября 2026 года

| Проверка | Mac ARM64 | VPS AMD64 |
|---|---|---|
| HTTP-тест, валидация 422, порядок и обрезка пробелов | Пройдено | Пройдено |
| Форма: добавление заметки | Пройдено | Пройдено |
| HTML как текст | Проверено | В списке есть строка `<img...>`, DOM-элементов img — 0 |
| Пересоздание и перезапуск контейнеров | Список совпал | Список совпал |
| Отказ Redis: health, чтение, запись | 503 без traceback | 503 без traceback |
| Восстановление Redis | Пройдено | Пройдено |
| Атомарный лимит в отдельной DB 15 | 100 записей; 1 успешный и 15 ответов 409 при 99 записях | Аналогично |
| Docker DNS и unless-stopped | Проверено | Проверено |

WordPress на 80 и калькулятор на 8080 вернули HTTP 200. Docker daemon не перезапускался; восстановление после рестарта daemon в этой практике не проверено. Старые локальные контейнеры `ct-practice3-web-1` и `ct-practice3-redis-1` удалены при смене проекта; старый тег `susu-cloud-practice3:2026-10-17` удален после успешных тестов. На VPS старых образов практики 3 не обнаружено. Volumes и другие практики сохранены; общий prune не применялся.

Изменены только Compose и документы практики 3; код, API, зависимости и Dockerfile сохранены. Исторические команды и доказательства 17 октября выше оставлены с прежними именами. Первые попытки запуска тестового контейнера выполнялись до готовности приложения; после добавления ожидания health итоговый тест прошел.

![Локальный запуск с прежними заметками](БабушкинМВ-local-20261018.png)

![Облачное приложение](БабушкинМВ-cloud-notes.png)

![Фактический вывод состояния контейнеров](БабушкинМВ-cloud-containers.png)

Снимок состояния контейнеров создан из HTML-представления фактического SSH-вывода Docker CLI. Сдачу выполняет студент. Изменения практики 3 подготовлены отдельным коммитом для публикации по запросу студента.
