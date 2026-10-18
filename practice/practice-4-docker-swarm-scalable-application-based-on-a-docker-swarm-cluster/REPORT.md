# Практика 4. Docker Swarm и асинхронный CSV TOP-N

## Что сделано

Автор: Бабушкин Михаил Вадимович. Подготовка: 17 октября 2026 года. Облако: 18 октября 2026 года.

### Реализация и границы результата

Один образ Python 3.12 используется API FastAPI/Uvicorn и процессами RQ. Redis хранит очередь, исходные CSV внутри аргументов заданий и результаты; AOF и volume сохраняют состояние при пересоздании контейнеров. Общая файловая система между узлами не нужна.

В задании указан Flask. По выбору студента используется FastAPI; принятие замены преподавателем не подтверждено. Локальный Compose не заменяет требуемый Swarm из трех облачных узлов. Облачное развертывание выполнено 18 октября 2026 года; фактические проверки приведены ниже.

### API и обработка

| Метод | Назначение |
|---|---|
| GET / | HTML-форма загрузки CSV и таблица результата |
| GET /instance | Имя контейнера для демонстрации нескольких реплик |
| GET /health | Проверка Redis, 200 или 503 |
| POST /jobs | Multipart: file, column, n; 202 и job_id |
| GET /jobs/{job_id} | queued/started/finished/failed; результат или безопасное сообщение об ошибке |

CSV: UTF-8, допускается BOM, разделитель запятая, уникальные непустые заголовки, до 5 МиБ и 50 000 строк. Имя столбца задается текстом; N от 1 до 100. До очереди проверяются размер, пустой файл и параметры: 413/422. Содержимое проверяется worker: неверные поля, заголовки, отсутствующий столбец, NaN/Infinity и нечисловые значения дают состояние failed.

Числа сравниваются как Decimal. TOP-N упорядочен по убыванию; равные значения сохраняют исходный порядок. Если записей меньше N, возвращаются все. Пустая таблица с корректным заголовком дает пустой результат. Данные выводятся через textContent.

Максимум 10 ожидающих/выполняющихся заданий. Redis-lock сериализует прием, запись RQ-задания и учет активного ID выполняются одной транзакцией. Завершенные/потерянные ID убираются при следующем приеме. Переполнение возвращает 429; недоступность Redis — 503. Эти ограничения действуют совместно для всех API-реплик.

Таймаут выполнения — 120 секунд. RQ хранит результат и job с исходным CSV 3600 секунд после завершения/ошибки. До обработки ожидающее задание не истекает: оно занимает одно из десяти мест. Неизвестное/истекшее задание дает 404. Потерянное задание помечается failed после истечения heartbeat RQ, не мгновенно; повторное выполнение не настроено. Корректные ошибки CSV возвращаются как безопасный результат и отображаются failed, без traceback. Неожиданные ошибки RQ могут иметь traceback в серверном журнале, но API его не возвращает. Описание задания содержит только ID, без CSV.

Сервис учебный, без пользовательской авторизации. Использовать только тестовые данные. Один manager и один Redis не обеспечивают отказоустойчивость; AOF с настройками по умолчанию допускает потерю последних секундных записей при аварии питания.

### Локальная подготовка на Mac

Выполнять из этой папки при запущенном Docker Desktop:

```bash
docker compose config --quiet
docker compose build
docker compose up -d --scale worker=2 --wait
PYTHONDONTWRITEBYTECODE=1 python3 test_tasks.py
python3 test_app.py http://127.0.0.1:8005
```

Открыть http://127.0.0.1:8005. Пример данных — БабушкинМВ-example.csv, столбец price, N=3. Ожидаются Keyboard, Headphones, Mouse.

Для проверки общей емкости остановить worker и убедиться, что все предыдущие задания закончены:

```bash
docker compose stop worker
python3 test_app.py --capacity
docker compose up -d --scale worker=1 --wait
docker compose up -d --scale worker=2 --wait
```

Тест создает 10 коротких заданий и проверяет 6 отказов при 16 конкурентных запросах. После запуска worker дождаться завершения всех принятых ID. Чистить пользовательские данные не требуется. HTTP-тесты создают тестовые задания, которые истекут через час.

Для проверки Redis выполнить `docker compose stop redis`: health, прием задания и чтение результата должны дать 503. Затем `docker compose start redis` и повторить тест. Для пересоздания использовать `docker compose down` без `-v`, затем `up`; volume не удалять.

### Облачное развертывание 18 октября 2026 года

| Узел | Публичный IP | wg0 | Роль |
|---|---|---|---|
| nl-vmmini | 176.222.53.58 | 10.77.4.1 | manager |
| nl-vmnano-1 | 176.222.55.104 | 10.77.4.2 | worker |
| nl-vmnano-2 | 176.222.55.129 | 10.77.4.3 | worker |

Доступ — SSH `practice4@<IP>` по ключу. Все узлы x86_64; Docker Engine 29.9.1. На nano Docker и Compose установлены из официального репозитория Docker; на manager существующая установка сохранена. Пользователь practice4 входит в docker. Docker-команды выполняются без sudo; административные — через предоставленный временный sudo. Существующий sudo-файл не удалялся. Manager и Docker daemon не перезапускались.

#### Резервные копии и установка

До изменений на каждом узле созданы `/root/20261018-practice4/baseline.txt` (адреса, маршруты, порты, службы, IPv4/IPv6 firewall) и копия `/etc/netplan`. На manager список контейнеров сохранен в `~/practice4-before-containers.txt`. Установочные команды:

```bash
sudo apt-get update -qq
sudo apt-get install -y wireguard ca-certificates curl openssl
```

Только на nano:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update -qq
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker practice4
```

Hostname nano изменены через `hostnamectl set-hostname nl-vmnano-1` и `nl-vmnano-2`; соответствующее имя добавлено к 127.0.1.1 в `/etc/hosts`. Общее обновление пакетов manager не выполнялось.

#### WireGuard и фильтрация

На каждом узле `wg genkey` создал ключ в `/etc/wireguard/private.key`, `wg pubkey` — публичный ключ. Ключи и `/etc/wireguard/wg0.conf` доступны только root. В конфигурации: адрес из таблицы `/24`, UDP/51820, MTU 1420, два peer с публичными Endpoint и `AllowedIPs` только соответствующего адреса `/32`, `PersistentKeepalive=25`. Приватные ключи при настройке подставлялись на сервере, не передавались на Mac и не включались в журнал.

```bash
sudo systemctl enable --now wg-quick@wg0
sudo wg show wg0 latest-handshakes
sudo ping -c 2 -W 3 10.77.4.1
sudo ping -c 2 -W 3 10.77.4.2
sudo ping -c 2 -W 3 10.77.4.3
```

Все пары узлов проверены; [журнал сети](БабушкинМВ-network-checks.txt). Маршрут по умолчанию и SSH сохранены. На nano ping требует sudo из-за отсутствия capability у системного ping.

UFW не включался. Установлен `/usr/local/sbin/ct-practice4-network-guard`, вызываемый systemd-unit `ct-practice4-network-guard.service`. Unit включен в multi-user.target и docker.service, имеет `After=docker.service wg-quick@wg0.service`, `PartOf=docker.service`. Применены IPv4 и IPv6 правила: цепочка CT4-IN отбрасывает TCP/2377,7946,5000 и UDP/7946,4789; для остальных портов RETURN. Переходы добавлены только для публичного интерфейса `enp1s0` в INPUT, FORWARD и существующую DOCKER-USER. Трафик wg0 этими правилами не ограничивается. Публичные SSH и веб-порты сохранены. Внешние TCP-пробы не подключились; UDP-пробы увеличили счетчик DROP. После reboot автозапуск настроен, но сам reboot не выполнялся.

#### Swarm и MTU

На manager:

```bash
docker swarm init --advertise-addr 10.77.4.1 --listen-addr 10.77.4.1:2377 --data-path-addr 10.77.4.1 --default-addr-pool 10.78.0.0/16 --default-addr-pool-mask-length 24
```

Оба worker присоединены с приватными advertise/data-path адресами и токеном, полученным через `docker swarm join-token -q worker`. Значение токена в отчете не сохраняется. После присоединения:

```bash
printf 'y\n' | docker network rm ingress
# Дождаться удаления исходной ingress-сети.
docker network create --driver overlay --ingress --subnet 10.79.4.0/24 --opt com.docker.network.driver.mtu=1350 ingress
docker node ls
```

Для сети приложения в stack задан MTU 1350. Все три узла Ready/Active, manager Leader. Исходные bridge-сети предыдущих практик не удалялись.

#### Registry с TLS

Файлы CA и сертификата созданы на manager в `~/ct-2026-practice-4/tls` с umask 077. CA: RSA 3072, CN `CT 2026 Practice 4 CA`, срок 365 дней; серверный сертификат: RSA 3072, CN и IP SAN `10.77.4.1`, serverAuth, срок 365 дней. Приватные ключи остались на manager. Только публичный CA-сертификат установлен на всех узлах в `/etc/docker/certs.d/10.77.4.1:5000/ca.crt`.

```bash
docker secret create ct-registry-cert tls/registry.crt
docker secret create ct-registry-key tls/registry.key
docker stack deploy -c registry-stack.yaml ct-2026-practice-4-registry
curl --cacert /etc/docker/certs.d/10.77.4.1:5000/ca.crt https://10.77.4.1:5000/v2/
```

Каждый узел получил `{}` от HTTPS registry. Registry закреплен на manager, использует постоянный volume и Swarm secrets, публикует 5000 в host mode; публичный доступ блокируется правилами выше. Проверка TLS не отключалась, insecure-registries не использовался. Доверие Docker заработало без рестарта daemon.

#### Сборка и запуск

На Mac из папки практики:

```bash
docker buildx build --platform linux/arm64 --load -t ct-2026-practice-4-csv-topn:2026-10-18-arm64 .
docker buildx build --platform linux/amd64 --load -t ct-2026-practice-4-csv-topn:2026-10-18-amd64 .
docker save -o .cache/ct-2026-practice-4-csv-topn-amd64.tar ct-2026-practice-4-csv-topn:2026-10-18-amd64
shasum -a 256 .cache/ct-2026-practice-4-csv-topn-amd64.tar
ssh practice4@176.222.53.58 'mkdir -p ~/ct-2026-practice-4'
scp .cache/ct-2026-practice-4-csv-topn-amd64.tar stack.yaml registry-stack.yaml practice4@176.222.53.58:ct-2026-practice-4/
```

SHA-256 на Mac и manager совпал: `ea7ef30809d5496761c417749082bd8e40305a687c070f8b40f42053ecdaaca7`.

На manager из `~/ct-2026-practice-4`:

```bash
docker load -i ct-2026-practice-4-csv-topn-amd64.tar
docker tag ct-2026-practice-4-csv-topn:2026-10-18-amd64 10.77.4.1:5000/ct-2026-practice-4-csv-topn:2026-10-18-amd64
docker push 10.77.4.1:5000/ct-2026-practice-4-csv-topn:2026-10-18-amd64
```

На каждом worker выполнен `docker pull 10.77.4.1:5000/ct-2026-practice-4-csv-topn:2026-10-18-amd64`. Digest совпал на трех узлах: `sha256:85fa5aa2310296626bf37dd61bfc84d73f4742970f16981b03fca45a073f98ad`. Затем на manager:

```bash
docker stack deploy -c stack.yaml ct-2026-practice-4
docker service ls
docker service ps ct-2026-practice-4_nginx
```

Nginx работает на 8084 с двумя репликами на разных nano, API — на 8085 с двумя репликами. Два фоновых worker обрабатывают общую очередь. Redis закреплен на manager с AOF и отдельным volume, порт 6379 не публикуется. Stack и локальный Compose используют фиксированные значения без .env и подстановок. Код и API не менялись.

#### Проверки и демонстрация

[Полный журнал облачных проверок](БабушкинМВ-cloud-checks.txt), [журнал работы двух worker](БабушкинМВ-worker-scaling.txt).

```bash
python3 test_tasks.py
python3 test_app.py http://127.0.0.1:8005
python3 test_app.py http://176.222.53.58:8085
```

Все 5 unit-тестов и HTTP-тесты прошли. Проверены обычный CSV, BOM, стабильный порядок равных значений, N больше количества строк, неверные заголовки, столбцы, числа, UTF-8, строки, превышение 5 МиБ, 422 и отсутствующие задания 404. Через браузер загружен БабушкинМВ-example.csv, получены Keyboard/350, Headphones/350, Mouse/200.

На manager последовательно выполнялись:

```bash
docker service scale ct-2026-practice-4_api=1
docker service scale ct-2026-practice-4_api=2
docker service scale ct-2026-practice-4_api=4
docker service scale ct-2026-practice-4_api=2
```

На каждом шаге `/instance` показал соответствующее число разных контейнеров. Running task еще не гарантирует готовность Uvicorn: один запрос при старте реплики получил connection refused; проверка повторена с ожиданием фактического ответа.

Для очереди worker масштабировались в 0, затем `test_app.py --capacity` принял 10 из 16 конкурентных запросов, остальные получили 429. Принятые задания обработаны одним worker. Проверка повторена с двумя worker; журнал подтверждает успешные задания на обоих nano. Ускорение не измерялось.

Redis масштабирован в 0: health, прием задания и чтение результата вернули 503 с короткой ошибкой. После возврата в 1 результат сохранился и совпал. После `docker service update --force --detach=true ct-2026-practice-4_api` результат также сохранился.

Порты 8084 и 8085 проверены с Mac на каждом публичном IP. Порты 80, 8080, 8083 manager вернули HTTP 200. Службы предыдущих практик не перенастраивались.

### Связь с дополнительным заданием

Этот же код выполняет CSV TOP-N для карточки practice-7-docker-swarm-scalable-application-based-on-a-docker-swarm-cluster-advanced. Отдельный код не требуется; ссылка и статус размещены в README.md соответствующей практики.

### Фактические локальные результаты 17 октября 2026 года

Mac ARM64, Docker Engine 29.3.1; Python контейнера 3.12.15, FastAPI 0.142.2, RQ 2.12.0, redis-клиент 8.1.0. Собран один ARM64-образ API/worker. Исходники предыдущих практик не изменялись.

| Проверка | Результат |
|---|---|
| 5 unit-тестов CSV | Пройдены |
| HTTP API, обычный CSV и BOM | Пройдены |
| Равные значения и N больше числа строк | Порядок стабилен, возвращены все доступные строки |
| Ошибочные заголовки, строки, числа, UTF-8 | API показывает failed без содержимого CSV |
| Пустой файл, N=0/101, размер >5 МиБ | 422/413 |
| CSV >50 000 строк | failed |
| 16 конкурентных запросов при остановленных worker | 10 приняты, 6 получили 429 |
| Локальные worker 1 → 2 | Контейнеры масштабированы, задания выполнялись обоими worker |
| Принудительная потеря worker | Синтетическое задание time.sleep перешло started → failed после heartbeat; повторения нет |
| Отказ Redis | Health, POST /jobs и GET результата вернули 503 |
| Пересоздание Redis, API и worker с тем же volume | Результат сохранен и совпадает полностью |
| Хранение CSV/job и результата | Проверены TTL 3572 секунды после пересоздания; исходно задано 3600 |
| Неизвестный результат | 404 |
| HTML-форма | Загрузка примера и TOP-3: Keyboard, Headphones, Mouse |
| Compose и оба Swarm YAML | Синтаксическая проверка пройдена |
| pip check в контейнере | Конфликтов нет |
| Три VPS, TLS registry, nginx и масштабирование Swarm | Пока не выполнены |

Проверка аварии worker использовала искусственно длинное задание, чтобы гарантировать остановку во время обработки. Локальное масштабирование не является доказательством облачного распределения или ускорения. Часовое ожидание не выполнялось: проверена настройка и фактический TTL Redis.

[Фактический вывод команд](БабушкинМВ-local-checks.txt). Скриншот контейнеров получен из HTML-представления этого вывода, а не из Docker Desktop.

![CSV TOP-N в браузере](БабушкинМВ-topn.png)

![Локальные контейнеры и TTL](БабушкинМВ-containers.png)

### Итог облачного этапа

Проверка потери worker использовала синтетическое задание `time.sleep(30)` с timeout 5 секунд, без CSV. Единственный worker был принудительно остановлен через `docker kill --signal KILL` после состояния started. После истечения срока RQ задание перешло в failed с короткой ошибкой; повторного выполнения не было. Swarm восстановил контейнер, затем число worker возвращено к двум. [Журнал отказа](БабушкинМВ-worker-loss.txt).

Передача 1 179 648 байт между API на одном worker, Redis на manager и API на другом worker прошла с полным сравнением данных. Тестовый ключ удален. Проверены фактические TTL ключей задания и результата; часовое ожидание не выполнялось.

Старые локальные контейнеры проекта ct-practice4 удалены при переходе на ct-2026-practice-4. Прежний локальный volume ct-practice4_csv-data сохранен и подключен как внешний; локальные unit/HTTP-тесты после перехода прошли. Старый тег susu-cloud-practice4:2026-10-17 удален после успешных проверок. На VPS таких образов не было. Общий prune не применялся.

Итог: 3 Ready/Active узла, registry 1/1, nginx 2/2 на разных worker, API 2/2, worker 2/2, Redis 1/1. Публичные адреса: http://176.222.53.58:8084/ и http://176.222.53.58:8085/. Полный вывод: [состояние Swarm](БабушкинМВ-swarm-checks.txt).

![Облачный CSV TOP-N](БабушкинМВ-cloud-topn.png)

![Публичный nginx](БабушкинМВ-cloud-nginx.png)

![Облачный Swarm](БабушкинМВ-cloud-swarm.png)

Снимок Swarm — HTML-представление фактического вывода Docker CLI через SSH, не интерфейс Docker Desktop. Исторические результаты и скриншоты 17 октября сохранены. Сдачу выполняет студент. Отказоустойчивость единственного manager и Redis не реализована; на публичной форме использовать только тестовые CSV. Изменения практики 4 подготовлены отдельным коммитом для публикации по запросу студента.

## Как сдавать

### Показать кластер и размещение nginx

```bash
ssh practice4@176.222.53.58
docker node ls
docker service ls
docker service ps ct-2026-practice-4_nginx
```

Показать три Ready/Active узла: manager nl-vmmini и два worker. Две реплики nginx должны находиться на разных worker. Открыть http://176.222.53.58:8084/. Объяснить: WireGuard связывает серверы приватными адресами, Swarm размещает сервисы, ingress доставляет запрос к реплике.

### Показать приватный registry

На каждом из трех серверов под practice4 выполнить:

```bash
curl --cacert /etc/docker/certs.d/10.77.4.1:5000/ca.crt https://10.77.4.1:5000/v2/
docker pull 10.77.4.1:5000/ct-2026-practice-4-csv-topn:2026-10-18-amd64
```

Ожидаются `{}` и успешное получение образа. Объяснить: registry работает на manager, TLS проверяется собственной CA, публичный порт 5000 закрыт. Приватные ключи и join-токены не показывать.

### Показать масштабирование API

На manager последовательно выполнить команды, после каждой дождаться готовности новых контейнеров:

```bash
docker service scale ct-2026-practice-4_api=1
docker service scale ct-2026-practice-4_api=2
docker service scale ct-2026-practice-4_api=4
docker service scale ct-2026-practice-4_api=2
```

Показывать `docker service ps ct-2026-practice-4_api` и несколько запросов к http://176.222.53.58:8085/instance. Разные имена контейнеров подтверждают распределение запросов; строгого чередования нет. Running еще не гарантирует готовность Uvicorn: дождаться успешного HTTP-ответа.

### Показать асинхронный CSV TOP-N

Открыть http://176.222.53.58:8085/, загрузить `БабушкинМВ-example.csv`, указать столбец `price` и N=3. Результат: Keyboard/350, Headphones/350, Mouse/200. Объяснить: API возвращает ID, задание и CSV хранятся в Redis, RQ worker вычисляет результат, страница опрашивает состояние. При равных числах исходный порядок сохраняется.

Показать `/docs`: POST /jobs принимает файл, столбец и N, возвращает 202 и job_id; GET /jobs/{job_id} возвращает состояние и результат. Одно приложение используется основной практикой 4 и дополнительной карточкой практики 7.

### Показать очередь и масштабирование обработчиков

```bash
docker service scale ct-2026-practice-4_worker=0
```

Загрузить CSV: задание остается в очереди. Затем:

```bash
docker service scale ct-2026-practice-4_worker=1
```

Дождаться выполнения. Увеличить число обработчиков до двух, загрузить несколько файлов и показать журналы обоих узлов:

```bash
docker service scale ct-2026-practice-4_worker=2
docker service logs --tail 30 ct-2026-practice-4_worker
```

Не обещать двукратного ускорения: задания короткие, ресурсы ограничены. Отказы Redis, потеря worker, лимит очереди и сохранность результатов подтверждены журналами выше; разрушать рабочий кластер для их повторения не требуется.

### Завершить демонстрацию

Оставить API 2/2, worker 2/2, nginx 2/2, Redis 1/1 и registry 1/1. Передать отчет и собственные доказательства. Не удалять volumes, secrets, серверы и временный sudo-файл без отдельного указания. Согласовать с преподавателем использование FastAPI вместо указанного Flask.
