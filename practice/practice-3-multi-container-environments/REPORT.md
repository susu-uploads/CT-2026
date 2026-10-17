# Практическая работа 3. FastAPI и Redis

Автор: Бабушкин Михаил Вадимович. Дата: 17 октября 2026 года.

## Решение

Два контейнера: веб-приложение заметок на Python 3.12/FastAPI/Uvicorn и Redis. Приложение обращается к Redis по Docker DNS-имени `redis`, порт 6379 не публикуется. Заметки хранятся в списке Redis в порядке добавления; AOF и внешний именованный volume сохраняют данные при пересоздании контейнеров. AOF с настройками по умолчанию допускает потерю последних секундных записей при аварийном отключении питания.

`GET /` возвращает страницу, `GET /api/notes` — `{"notes":[...]}`, `POST /api/notes` принимает `{"text":"..."}` и возвращает HTTP 201. Текст обрезается по краям и проверяется на длину 1–500 символов; неверный ввод возвращает 422. Lua-скрипт Redis атомарно проверяет лимит 100 и добавляет заметку, при заполнении возвращается 409. `GET /health` проверяет Redis; при его недоступности маршруты данных и health возвращают 503. Страница выводит заметки через `textContent`.

Приложение учебное: без авторизации, редактирования и удаления. В публичной демонстрации использовать только тестовые записи. Вместо примера Food Trucks из методички по выбору студента используется собственное приложение; принятие замены преподавателем не подтверждено.

## Ручное развертывание на Mac

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

## Переход на Compose

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

## Облачный этап — ожидает доступ

Используется VPS практики 1 с x86_64, Docker Engine и Compose. Не изменять Apache/WordPress на 80 и практику 2 на 8080. Сначала проверить свободный порт 8083 и отсутствие конфликтов имен.

На Mac:

```bash
mkdir -p .cache
docker buildx build --platform linux/amd64 --load -t susu-cloud-practice3:2026-10-17 .
docker save -o .cache/practice3-amd64.tar susu-cloud-practice3:2026-10-17
shasum -a 256 .cache/practice3-amd64.tar
ssh ct-vps 'mkdir -p ~/practice3'
scp .cache/practice3-amd64.tar compose.yaml ct-vps:practice3/
```

Алиас `ct-vps` настраивается локально после получения IP, порта, пользователя с sudo и пути к ключу. На сервере:

```bash
cd ~/practice3
sha256sum practice3-amd64.tar
sudo docker load -i practice3-amd64.tar
sudo docker volume create ct-practice3-notes
sudo env WEB_BIND=0.0.0.0 WEB_PORT=8083 docker compose up -d --no-build --wait
```

Перед `load` сравнить SHA-256. Те же `WEB_BIND` и `WEB_PORT` использовать для последующих команд Compose; локально параметры по умолчанию безопасно ограничены loopback. Образ Redis сервер загрузит из официального registry самостоятельно. Registry для собственного образа не нужен.

Разрешить TCP/8083 у провайдера с учетом сетевых правил Docker; Redis не публиковать. С Mac проверить `python3 test_app.py http://<IP>:8083`, форму, отказ/восстановление Redis и сохранность данных после пересоздания. После перезапуска Docker повторить внешний тест; предварительно убедиться, что перезапуск не затронет чужие контейнеры. Проверить доступность WordPress и практики 2.

Облачные скриншоты, фактические версии и результаты добавить после выполнения. Сдачу выполняет студент; удаление VM и данных согласовать отдельно.

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
| Облако, AMD64 и сдача | Пока не выполнены |

Тестовая DB 1 после проверки очищена только от созданного тестом ключа; основной список DB 0 не очищался. Контейнеры ручного этапа удалены, Compose оставлен запущенным на 127.0.0.1:8003. Практика 2 не изменялась.

Журналы: [ручной запуск](БабушкинМВ-manual-checks.txt), [Compose](БабушкинМВ-compose-checks.txt). Скриншоты показывают реальное приложение на соответствующих этапах; состав контейнеров и сетей зафиксирован в журналах.

![Ручной запуск](БабушкинМВ-manual.png)

![Compose и сохраненные заметки](БабушкинМВ-compose.png)

![Отказ Redis](БабушкинМВ-redis-unavailable.png)
