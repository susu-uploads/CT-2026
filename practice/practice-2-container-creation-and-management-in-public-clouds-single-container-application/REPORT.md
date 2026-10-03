# Практическая работа 2. Одноконтейнерное веб-приложение

**Дисциплина:** Облачные технологии

**Автор:** Бабушкин Михаил Вадимович

**Дата локальной проверки:** 2 октября 2026 года

## 1. Цель и результат

Изучить создание Docker-образа, запуск контейнера с веб-приложением и его публикацию для последующего развертывания в публичном облаке.

Реализован калькулятор на Python 3.12 и FastAPI. Пользователь вводит два числа, выбирает действие и получает результат без перезагрузки страницы. Сервер выполняет сложение, вычитание, умножение и деление. Страница и API обслуживаются одним процессом Uvicorn в одном контейнере.

Приложение выполнено и проверено локально. Публикация в registry и развертывание на удаленной машине выполняются отдельно по разделам 5–6; на момент локальной проверки они не выполнялись. Сдача преподавателю не подтверждена.

## 2. Файлы и HTTP API

Все файлы находятся в текущем каталоге практики:

| Файл | Назначение |
|---|---|
| `main.py` | Маршруты FastAPI, вычисления и проверка результата |
| `index.html` | Страница калькулятора, стили и запросы к API |
| `requirements.txt` | Зафиксированные версии FastAPI, Uvicorn и их зависимостей |
| `Dockerfile` | Сборка образа и команда запуска приложения |
| `.dockerignore` | Ограничение контекста сборки файлами приложения |
| `test_app.py` | HTTP-проверка на стандартной библиотеке Python |
| `TASK.md` | Исходное задание |
| `REPORT.md` | Описание решения и команды развертывания |

| Метод и путь | Результат |
|---|---|
| `GET /` | HTML-страница калькулятора |
| `GET /health` | `{"status":"ok"}` |
| `GET /api/calculate?a=6&b=2&operation=divide` | `{"result":3.0}` |
| `GET /docs` | Интерактивная документация Swagger UI |
| `GET /openapi.json` | Схема API |

Параметры `a`, `b`, `operation` обязательны. Действия: `add`, `subtract`, `multiply`, `divide`. Нечисловые значения, `NaN`, бесконечность, неизвестное действие и отсутствующие параметры возвращают HTTP 422. Деление на ноль и переполнение результата возвращают HTTP 400 с пояснением. Страница показывает результат или сообщение об ошибке.

Числа обрабатываются как `float`, поэтому возможна обычная погрешность вычислений с плавающей точкой. Приложение не хранит пользовательские данные.

## 3. Окружение Python и запуск без Docker

Команды для локального компьютера. В курсе используется общее окружение `.venv`; его файлы исключены из Git. Если окружение уже создано, повторять команду его создания не нужно.

```bash
cd "/Users/mikhail/Developer/SUSU.PE/СП-М-О-ОТ-2026"
python3.12 -m venv .venv
source .venv/bin/activate
python --version

cd "Практика/Практика 2 - 2. Формирование и управление контейнерами в публичных облаках (одноконтейнерное приложение)"
python -m pip install -r requirements.txt
python -m pip check
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Открыть в браузере [калькулятор](http://127.0.0.1:8000/) и [документацию API](http://127.0.0.1:8000/docs).

В другом терминале перейти в каталог этой практики и проверить запущенный сервер:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail 'http://127.0.0.1:8000/api/calculate?a=6&b=2&operation=divide'
python3.12 test_app.py http://127.0.0.1:8000
```

Ожидаются `{"status":"ok"}`, `{"result":3.0}` и строка `HTTP-проверки пройдены: http://127.0.0.1:8000`.

Перед следующим разделом остановить обычный сервер через **Ctrl+C**, чтобы освободить порт 8000.

## 4. Локальная сборка и запуск Docker

Выполнять из каталога практики. Docker Desktop уже установлен на Mac; команда `open` запускает его. После запуска дождаться готовности движка: `docker info` должен завершиться успешно.

```bash
open -a Docker
docker info
docker build -t susu-cloud-practice2:1.0 .
docker run -d --name susu-cloud-practice2 \
  -p 127.0.0.1:8000:8000 \
  susu-cloud-practice2:1.0

curl --retry 10 --retry-all-errors --retry-delay 1 --retry-max-time 30 \
  --max-time 5 --fail http://127.0.0.1:8000/health
python3.12 test_app.py http://127.0.0.1:8000
docker logs susu-cloud-practice2
docker exec susu-cloud-practice2 id
docker exec susu-cloud-practice2 python --version
```

Открыть `http://127.0.0.1:8000/`. Привязка `127.0.0.1:8000:8000` делает локальный контейнер доступным с этого компьютера. В контейнере Uvicorn слушает `0.0.0.0:8000`, что позволяет Docker направлять к нему опубликованные запросы.

Образ основан на `python:3.12-slim`. Сначала устанавливаются зависимости, затем копируются `main.py` и `index.html`. Это позволяет повторно использовать слой зависимостей при изменении приложения. Процесс работает от пользователя `app` с UID 10001. Команда запуска задана в exec-форме, без `--reload`; отдельный Python на удаленном сервере не требуется.

Управление локальным контейнером:

```bash
docker stop susu-cloud-practice2
docker start susu-cloud-practice2
```

Для пересоздания контейнера после изменения приложения:

```bash
docker build -t susu-cloud-practice2:1.0 .
docker stop susu-cloud-practice2
docker rm susu-cloud-practice2
docker run -d --name susu-cloud-practice2 \
  -p 127.0.0.1:8000:8000 \
  susu-cloud-practice2:1.0
```

## 5. Публикация образа в Docker registry

Команды выполняются **на локальном компьютере** из каталога практики. Сначала создать репозиторий `susu-cloud-practice2` в выбранном registry, если сервис требует этого. Заменить значения в угловых скобках своими. В качестве примера адреса используется Docker Hub (`docker.io`); для другого registry указать его адрес без `https://`.

```bash
export REGISTRY='docker.io'
export REGISTRY_USER='<имя-пользователя-или-namespace>'
export IMAGE="${REGISTRY}/${REGISTRY_USER}/susu-cloud-practice2:1.0"

docker login "$REGISTRY" --username "$REGISTRY_USER"
```

При запросе пароля использовать пароль или токен согласно требованиям registry. Если namespace организации отличается от имени учетной записи, для `--username` указать имя учетной записи, сохранив namespace в `IMAGE`.

### 5.1. Образ для ARM64 и AMD64

Этот Mac использует ARM64. Образ, собранный обычным `docker build` на нем, предназначен для ARM64; для сервера x86_64 нужна сборка AMD64. Следующая команда публикует обе архитектуры под одним тегом, и сервер автоматически выбирает подходящую.

Создать отдельный builder и опубликовать образ:

```bash
docker buildx create --name susu-cloud-builder --driver docker-container --use
docker buildx inspect --bootstrap
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "$IMAGE" \
  --push .
docker buildx imagetools inspect "$IMAGE"
```

Если builder `susu-cloud-builder` уже создан, вместо повторного `create` выполнить `docker buildx use susu-cloud-builder`. Флаг `--push` сразу публикует образ; отдельный `docker push` для этой сборки не нужен. В выводе проверки должны присутствовать `linux/amd64` и `linux/arm64`.

### 5.2. Публикация одного уже собранного образа

Если удаленная машина тоже ARM64, можно отправить локальный образ напрямую:

```bash
docker tag susu-cloud-practice2:1.0 "$IMAGE"
docker push "$IMAGE"
```

Для отправки уже проверенного образа AMD64 вместо первого имени использовать `susu-cloud-practice2:1.0-amd64`. Такой `push` публикует только выбранную архитектуру и заменяет содержимое тега; применять этот вариант вместо раздела 5.1, а не после него.

## 6. Развертывание на Ubuntu 24.04

Команды этого раздела выполнять **на удаленной машине по SSH**. Нужны публичный IP и учетная запись с `sudo`. Здесь подразумевается новая Ubuntu 24.04; если Docker Engine уже установлен и работает, перейти к разделу 6.2.

### 6.1. Установка Docker Engine

Подключить официальный репозиторий Docker:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker version
sudo docker run --rm hello-world
```

### 6.2. Загрузка и запуск приложения

Параметры из локального терминала не передаются через SSH автоматически: задать их повторно на сервере, используя тот же опубликованный образ.

```bash
export REGISTRY='docker.io'
export REGISTRY_USER='<имя-пользователя-или-namespace>'
export IMAGE="${REGISTRY}/${REGISTRY_USER}/susu-cloud-practice2:1.0"
```

Для приватного репозитория выполнить вход под той же учетной записью, от которой будет выполняться загрузка. Все команды Docker на сервере здесь используют `sudo`, поэтому вход тоже выполняется через `sudo`:

```bash
sudo docker login "$REGISTRY" --username "$REGISTRY_USER"
```

Для публичного репозитория вход можно пропустить. Затем загрузить и запустить образ:

```bash
sudo docker pull "$IMAGE"
sudo docker run -d --name susu-cloud-practice2 \
  --restart unless-stopped \
  -p 80:8000 \
  "$IMAGE"

sudo docker ps --filter name=susu-cloud-practice2
curl --retry 10 --retry-all-errors --retry-delay 1 --retry-max-time 30 \
  --max-time 5 --fail http://127.0.0.1/health
curl --fail 'http://127.0.0.1/api/calculate?a=6&b=2&operation=divide'
sudo docker logs --tail 50 susu-cloud-practice2
```

Порт 80 на сервере должен быть свободен. `80:8000` связывает внешний HTTP-порт сервера с портом приложения в контейнере. `--restart unless-stopped` обеспечивает автоматический запуск после перезапуска Docker или машины, если контейнер не был остановлен вручную.

### 6.3. Публичный доступ и демонстрация

В настройках сети облачного провайдера назначить машине публичный IP и разрешить входящий **TCP/80** в группе безопасности. Для публичной демонстрации источник — `0.0.0.0/0`; правило SSH должно сохраняться. Docker публикует порт собственными сетевыми правилами, поэтому доступ к нему задавать прежде всего через группу безопасности облака.

На локальном компьютере задать адрес сервера и проверить:

```bash
export SERVER_IP='<публичный-IP-сервера>'
curl --fail "http://${SERVER_IP}/health"
curl --fail "http://${SERVER_IP}/api/calculate?a=6&b=2&operation=divide"
python3.12 test_app.py "http://${SERVER_IP}"
```

Открыть `http://<публичный-IP-сервера>/` и `http://<публичный-IP-сервера>/docs`. Показать вычисление в форме, ответ API, состояние контейнера и журналы. Доступность по публичному IP проверять с локального компьютера, а не только изнутри удаленной машины.

### 6.4. Журналы, остановка и обновление

На удаленном сервере:

```bash
sudo docker logs --tail 50 susu-cloud-practice2
sudo docker logs -f susu-cloud-practice2
```

Завершить просмотр журналов через **Ctrl+C**; контейнер продолжит работу.

```bash
sudo docker stop susu-cloud-practice2
sudo docker start susu-cloud-practice2
```

Для обновления сначала опубликовать новый образ, затем задать на сервере его полное имя с новым тегом, например `1.1`, и загрузить его **до** остановки текущего приложения:

```bash
export IMAGE="${REGISTRY}/${REGISTRY_USER}/susu-cloud-practice2:1.1"
sudo docker pull "$IMAGE"
```

После успешной загрузки пересоздать контейнер:

```bash
sudo docker stop susu-cloud-practice2
sudo docker rm susu-cloud-practice2
sudo docker run -d --name susu-cloud-practice2 \
  --restart unless-stopped \
  -p 80:8000 \
  "$IMAGE"
```

Повторить проверки из разделов 6.2–6.3. Пока контейнер пересоздается, приложение кратковременно недоступно.

## 7. Фактические локальные проверки

Среда: macOS ARM64; Python 3.12.10 в общем окружении курса; Docker Desktop 4.68.0, Docker Engine 29.3.1. В образе `python:3.12-slim` на момент сборки — Python 3.12.14. FastAPI 0.142.2, Uvicorn 0.54.0. Обе версии Python относятся к выбранной ветке 3.12.

| Проверка | Результат |
|---|---|
| `pip check` в окружении курса | Конфликтов зависимостей нет |
| HTTP-тест обычного запуска, порт 8001 | Пройден |
| Сборка и запуск ARM64, порт 8000 | Пройдены |
| HTTP-тест контейнера ARM64 | Пройден |
| Сборка и запуск AMD64 под эмуляцией Docker Desktop, порт 8002 | Пройдены; `uname -m` возвращает `x86_64` |
| HTTP-тест контейнера AMD64 | Пройден |
| Пользователь контейнеров | `uid=10001(app)`, выполнение без root |
| Работа формы в браузере | Проверены вычисление, сообщение о делении на ноль и повторное вычисление после исправления ввода; страница контейнера проверена при ширине 360 px |
| Публикация в registry и доступ по публичному IP | Пока не выполнялись |

HTTP-тест проверяет страницу, health, документацию, четыре операции, отрицательные и дробные числа, обязательные параметры, недопустимые действия, `NaN`, бесконечность, деление на ноль и переполнение.

Команды, использованные для проверки архитектур:

```bash
docker buildx build --platform linux/arm64 --load \
  -t susu-cloud-practice2:1.0 .
docker buildx build --platform linux/amd64 --load \
  -t susu-cloud-practice2:1.0-amd64 .
docker run -d --platform linux/amd64 --name susu-cloud-practice2-amd64 \
  -p 127.0.0.1:8002:8000 \
  susu-cloud-practice2:1.0-amd64
curl --retry 10 --retry-all-errors --retry-delay 1 --retry-max-time 30 \
  --max-time 5 --fail http://127.0.0.1:8002/health
python3.12 test_app.py http://127.0.0.1:8002
docker exec susu-cloud-practice2-amd64 uname -m
docker rm -f susu-cloud-practice2-amd64
```

## 8. Вывод

Веб-приложение упаковано в один Docker-контейнер и доступно локально через опубликованный порт. Один и тот же набор HTTP-проверок прошел при обычном запуске Python и в контейнерах ARM64 и AMD64. Для облачной части подготовлена последовательность публикации образа и запуска на Ubuntu 24.04; ее выполнение и публичная доступность пока не подтверждены.

## Источники

- [Задание практики 2](https://edu.susu.ru/mod/assign/view.php?id=8720330).
- [FastAPI: приложение в Docker](https://fastapi.tiangolo.com/deployment/docker/).
- [Docker: установка на Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
- [Docker: сборка для нескольких платформ](https://docs.docker.com/build/building/multi-platform/).
