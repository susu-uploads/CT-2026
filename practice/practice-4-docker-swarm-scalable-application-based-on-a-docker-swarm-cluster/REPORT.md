# Практика 4. Docker Swarm и асинхронный CSV TOP-N

Автор: Бабушкин Михаил Вадимович. Подготовка: 17 октября 2026 года.

## Реализация и границы результата

Один образ Python 3.12 используется API FastAPI/Uvicorn и процессами RQ. Redis хранит очередь, исходные CSV внутри аргументов заданий и результаты; AOF и volume сохраняют состояние при пересоздании контейнеров. Общая файловая система между узлами не нужна.

В задании указан Flask. По выбору студента используется FastAPI; принятие замены преподавателем не подтверждено. Локальный Compose не заменяет требуемый Swarm из трех облачных узлов. Облачное развертывание, приватный registry и публичная доступность пока не проверены.

## API и обработка

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

## Локальная подготовка на Mac

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

## Подготовка трех VPS

Требуются Ubuntu 24.04 x86_64, по 2 vCPU, 2 ГБ RAM и от 20 ГБ диска. Manager — VPS практики 1, плюс два worker в одной приватной сети. Нужны SSH-алиасы ct-manager, ct-worker1, ct-worker2, пользователи с sudo и локальные ключи. Приватные ключи, IP, токены Swarm и платежные данные в репозиторий не добавлять.

До изменений проверить чужие контейнеры/Swarm, свободные 5000/8084/8085, объем диска и RAM. Установить Docker Engine и Compose из официального репозитория Docker на всех узлах; применить инструкцию Ubuntu из практики 2. Существующую конфигурацию Docker не перезаписывать. Не менять Apache/WordPress и порты 8080/8083 предыдущих практик.

На каждом узле настроить стабильное разрешение ct-registry в приватный IP manager. На firewall провайдера и хостов разрешить только между тремя узлами TCP/2377, TCP+UDP/7946 и UDP/4789. SSH ограничить IP студента. Открыть для демонстрации TCP/8084 и TCP/8085. Порт registry 5000 разрешить только трем узлам; не открывать внешне. Учитывать NAT-правила Docker: UFW сам по себе не гарантирует фильтрацию опубликованных портов. Проверить ограничения с разрешенного узла и внешнего компьютера.

На manager (значение MANAGER_PRIVATE_IP задать в текущей SSH-сессии):

```bash
sudo docker swarm init --advertise-addr "$MANAGER_PRIVATE_IP"
sudo docker swarm join-token worker
```

Команду присоединения с полученным токеном выполнить на каждом worker через SSH. Токен не сохранять в отчете. На manager:

```bash
sudo docker node ls
```

Требуются три Ready/Active узла, один Leader и два worker. Конфигурации Swarm запускать с manager.

## TLS и приватный registry

Сгенерировать собственную CA и серверный сертификат на manager в приватном каталоге вне Git. Не запускать команды поверх существующих ключей.

```bash
umask 077
mkdir -p ~/practice4-private
cd ~/practice4-private
openssl req -x509 -newkey rsa:3072 -nodes -days 365 \
  -keyout ca.key -out ca.crt -subj '/CN=CT Practice Registry CA' \
  -addext 'basicConstraints=critical,CA:TRUE' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign'
openssl req -newkey rsa:3072 -nodes -keyout registry.key \
  -out registry.csr -subj '/CN=ct-registry'
printf '%s\n' 'subjectAltName=DNS:ct-registry' \
  'extendedKeyUsage=serverAuth' 'keyUsage=digitalSignature,keyEncipherment' > registry.ext
openssl x509 -req -in registry.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out registry.crt -days 90 -extfile registry.ext
sudo docker secret create ct-registry-cert registry.crt
sudo docker secret create ct-registry-key registry.key
```

Передать только публичный ca.crt на каждый узел, установить в `/etc/docker/certs.d/ct-registry:5000/ca.crt`. CA private key и server key не передавать worker и не включать в отчет. Проверить, что Docker доверяет сертификату; если потребуется перезапуск Docker, сначала оценить влияние на предыдущие практики.

Передать registry-stack.yaml на manager, выполнить из каталога с конфигурацией:

```bash
sudo docker stack deploy -c registry-stack.yaml ct-registry
sudo docker service ps ct-registry_registry
curl --cacert ~/practice4-private/ca.crt https://ct-registry:5000/v2/
```

Проверить HTTPS с каждого узла. Registry закреплен на manager с локальным volume; сеть ограничивает доступ кластером, пользовательская аутентификация registry не добавляется. Внешняя проверка порта 5000 должна подтвердить недоступность. Не использовать insecure-registries и не отключать проверку TLS.

## Образ и Swarm stack

На Mac из каталога практики:

```bash
mkdir -p .cache
docker buildx build --platform linux/amd64 --load -t susu-cloud-practice4:2026-10-17 .
docker save -o .cache/practice4-amd64.tar susu-cloud-practice4:2026-10-17
shasum -a 256 .cache/practice4-amd64.tar
ssh ct-manager 'mkdir -p ~/practice4'
scp .cache/practice4-amd64.tar stack.yaml registry-stack.yaml ct-manager:practice4/
```

На manager сравнить SHA-256 и затем:

```bash
cd ~/practice4
sha256sum practice4-amd64.tar
sudo docker load -i practice4-amd64.tar
sudo docker tag susu-cloud-practice4:2026-10-17 ct-registry:5000/csv-topn:2026-10-17
sudo docker push ct-registry:5000/csv-topn:2026-10-17
sudo env REGISTRY_HOST=ct-registry docker stack deploy -c stack.yaml ct-practice4
sudo docker stack services ct-practice4
sudo docker service ps ct-practice4_nginx
sudo docker service ps ct-practice4_api
```

Перед deploy вручную проверить `docker pull ct-registry:5000/csv-topn:2026-10-17` на каждом worker. Образы заранее публикуются: stack deploy не выполняет build. Nginx имеет две реплики с ограничением одной на worker; API и worker могут масштабироваться независимо. Redis закреплен на manager, отдельная overlay-сеть csv используется только приложением. В Swarm нет ожидания Compose depends_on: API сообщает 503 до готовности Redis, worker перезапускается средствами Swarm.

## Облачная демонстрация

- Проверить nginx через публичный IP любого узла на 8084. Через service ps подтвердить размещение двух реплик на разных worker.
- Проверить API на 8085 и HTTP-тест с Mac: `python3 test_app.py http://<IP>:8085`.
- Масштабировать API 1 → 2 → 4 → 2 через `sudo docker service scale ct-practice4_api=<число>`. На каждом шаге дождаться нужного количества Running tasks и сохранить service ps. Повторные запросы /instance с отдельными соединениями должны показать разные контейнеры, но не обязаны чередоваться строго.
- Масштабировать worker 1 → 2, поставить пакет заданий и показать работу обоих worker по журналам, ID и времени выполнения. Ускорение не гарантировать: короткие задания и ресурсы влияют на время.
- Проверить сохранность завершенного результата после пересоздания API/worker; Redis и его volume не удалять.
- Проверить отказ Redis и восстановление, затем подтвердить работу WordPress и практик 2–3.
- Сохранить облачные скриншоты, версии и фактические результаты. Сдача выполняется студентом. Удаление VM, secrets и volumes согласовать отдельно.

## Связь с дополнительным заданием

Этот же код выполняет CSV TOP-N для карточки practice-7-docker-swarm-scalable-application-based-on-a-docker-swarm-cluster-advanced. Отдельный код не требуется; ссылка и статус размещены в README.md соответствующей практики.

## Фактические локальные результаты 17 октября 2026 года

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
