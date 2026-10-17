# Практическая работа 2. Одноконтейнерное веб-приложение

**Дисциплина:** Облачные технологии

**Автор:** Бабушкин Михаил Вадимович

**Дата последней локальной проверки:** 17 октября 2026 года

## 1. Цель и результат

Изучить создание Docker-образа, запуск контейнера с веб-приложением и его публикацию для последующего развертывания в публичном облаке.

Реализован калькулятор на Python 3.12 и FastAPI. Пользователь вводит два числа, выбирает действие и получает результат без перезагрузки страницы. Сервер выполняет сложение, вычитание, умножение и деление. Страница и API обслуживаются одним процессом Uvicorn в одном контейнере.

Приложение повторно собрано и проверено локально 17 октября 2026 года. Облачный этап ожидает доступ к VPS практики 1; инструкция приведена в разделах 5–6. Образ будет передан по SSH без registry. Сдача преподавателю не подтверждена.

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
cd "/Users/mikhail/Developer/2026-autumn/CT-2026"
python3.12 -m venv .venv
source .venv/bin/activate
python --version

cd "practice/practice-2-container-creation-and-management-in-public-clouds-single-container-application"
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

Выполнять из каталога практики. Если контейнер `susu-cloud-practice2` уже существует, для текущей демонстрации использовать `docker start susu-cloud-practice2`, а не повторный `docker run`. Docker Desktop уже установлен на Mac; команда `open` запускает его. После запуска дождаться готовности движка: `docker info` должен завершиться успешно.

```bash
open -a Docker
docker info
docker build --platform linux/arm64 -t susu-cloud-practice2:2026-10-17 .
docker run -d --name susu-cloud-practice2 \
  -p 127.0.0.1:8000:8000 \
  susu-cloud-practice2:2026-10-17

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
docker build --platform linux/arm64 -t susu-cloud-practice2:2026-10-17 .
docker stop susu-cloud-practice2
docker rm susu-cloud-practice2
docker run -d --name susu-cloud-practice2 \
  -p 127.0.0.1:8000:8000 \
  susu-cloud-practice2:2026-10-17
```

## 5. Подготовка образа и передача на VPS по SSH

Этот раздел пока не выполнен. Нужна VPS практики 1 с Ubuntu 24.04 и архитектурой x86_64. Перед сборкой проверить на сервере `uname -m`. Mac использует ARM64; серверу x86_64 нужен образ AMD64.

На Mac из каталога практики выполнить:

```bash
mkdir -p .cache
docker buildx build --platform linux/amd64 --load \
  -t susu-cloud-practice2:2026-10-17-amd64 .
docker save -o .cache/practice2-amd64.tar susu-cloud-practice2:2026-10-17-amd64
shasum -a 256 .cache/practice2-amd64.tar
```

После получения доступа настроить локальный SSH-алиас `ct-vps` с IP, пользователем, портом и путем к ключу. Секреты и приватные ключи в репозиторий не добавлять. Проверить ключ хоста сервера. Создать каталог для передачи и скопировать образ:

```bash
ssh ct-vps 'mkdir -p ~/practice2'
scp .cache/practice2-amd64.tar ct-vps:practice2/
ssh ct-vps 'sha256sum ~/practice2/practice2-amd64.tar'
```

Сравнить SHA-256 локального и переданного файлов. При несовпадении повторить передачу до загрузки образа. Registry и публикация образа не требуются. Архив остается в игнорируемом `.cache/`.

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

Облачные команды ниже пока не выполнялись. На сервере сохранить Apache и WordPress практики 1 на порту 80. Убедиться, что порт 8080 свободен и контейнер с выбранным именем еще не существует.

```bash
sudo ss -ltnp 'sport = :8080'
sudo docker ps -a --filter name=susu-cloud-practice2
sudo docker load -i ~/practice2/practice2-amd64.tar
sudo docker image inspect susu-cloud-practice2:2026-10-17-amd64 \
  --format '{{.Os}}/{{.Architecture}}'
sudo docker run -d --name susu-cloud-practice2 \
  --restart unless-stopped \
  -p 8080:8000 \
  susu-cloud-practice2:2026-10-17-amd64
sudo docker ps --filter name=susu-cloud-practice2
curl --retry 10 --retry-all-errors --retry-delay 1 --retry-max-time 30 \
  --max-time 5 --fail http://127.0.0.1:8080/health
sudo docker logs --tail 50 susu-cloud-practice2
```

Проверка образа должна вернуть `linux/amd64`. При занятом порту или существующем контейнере сначала выяснить, кому они принадлежат; чужие ресурсы не останавливать и не удалять.

### 6.3. Публичный доступ и демонстрация

В сетевых правилах провайдера разрешить входящий TCP/8080 для публичной демонстрации. Сохранить правила SSH и HTTP/80 практики 1. Если внешнего firewall у провайдера нет, настроить фильтрацию с учетом правил Docker: одного UFW недостаточно для ограничения опубликованных Docker-портов.

На Mac из каталога практики выполнить:

```bash
export SERVER_IP='<публичный-IP-сервера>'
curl --fail "http://${SERVER_IP}:8080/health"
python3.12 test_app.py "http://${SERVER_IP}:8080"
```

Открыть `http://<публичный-IP-сервера>:8080/` и `/docs`. Проверить вычисление, деление на ноль и повторный расчет. Сохранить собственные скриншоты сайта и состояния контейнера. Отдельно убедиться, что WordPress практики 1 продолжает работать на порту 80.

### 6.4. Проверка восстановления и управление

На выделенной учебной VPS проверить восстановление контейнера после перезапуска Docker. Перед этим проверить отсутствие чужих контейнеров: перезапуск Docker кратковременно прерывает их работу.

```bash
sudo systemctl restart docker
sudo docker ps --filter name=susu-cloud-practice2
curl --retry 10 --retry-all-errors --retry-delay 1 --retry-max-time 30 \
  --max-time 5 --fail http://127.0.0.1:8080/health
sudo docker logs --tail 50 susu-cloud-practice2
```

Повторить внешний HTTP-тест с Mac. Для обычного управления использовать `sudo docker stop susu-cloud-practice2` и `sudo docker start susu-cloud-practice2`. Остановленный вручную контейнер политика `unless-stopped` автоматически не поднимает.

Обновление выполнять передачей нового тега образа: сначала успешно загрузить его через `docker load`, затем пересоздать только контейнер этой практики с теми же портом и политикой перезапуска. Apache и WordPress не изменять. Удаление облачных ресурсов после сдачи согласовать отдельно.

## 7. Фактические локальные проверки

### Проверки 2 октября 2026 года

Следующие результаты сохранены из предыдущего отчета; обычный запуск Python и AMD64 17 октября повторно не проверялись.

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

### Повторная проверка 17 октября 2026 года

Docker Engine 29.3.1, macOS ARM64. Заново собран образ `susu-cloud-practice2:2026-10-17` для `linux/arm64`; Python внутри контейнера — 3.12.15. Исходники приложения, API и зависимости не менялись.

| Проверка | Фактический результат |
|---|---|
| Сборка ARM64 из текущих файлов | Пройдена |
| HTTP-тест контейнера на 127.0.0.1:8000 | Пройден до и после остановки/запуска |
| Остановка контейнера | HTTP недоступен, как ожидается |
| Повторный запуск контейнера | Health и полный HTTP-тест проходят |
| `pip check` внутри контейнера | Конфликтов нет |
| Пользователь процесса | UID 10001, без root |
| Форма в браузере | 6 / 2 = 3; 6 / 0 показывает ошибку; после исправления снова 3 |
| AMD64 и облачная доступность | В этом этапе не проверялись |

Предыдущий остановленный контейнер сохранен под именем `susu-cloud-practice2-20261002`. Новый проверенный контейнер работает под именем `susu-cloud-practice2` и доступен только на loopback Mac.

Доказательства:

- [Вывод проверок Docker и HTTP](БабушкинМВ-local-checks.txt).
- Снимок фактического вывода команд ниже получен из HTML-представления журнала, а не из интерфейса Docker Desktop: захват окна Docker Desktop оказался недоступен.

![Проверки контейнера](БабушкинМВ-local-container.png)

![Успешное вычисление](БабушкинМВ-local-calculator.png)

![Обработка деления на ноль](БабушкинМВ-local-error.png)

## 8. Вывод

Веб-приложение упаковано в один Docker-контейнер и доступно локально через опубликованный порт. Один и тот же набор HTTP-проверок прошел при обычном запуске Python и в контейнерах ARM64 и AMD64. Для облачной части подготовлена передача образа AMD64 по SSH и запуск на Ubuntu 24.04, порт 8080; ее выполнение и публичная доступность пока не подтверждены. План оставшихся действий находится в TODO.md.

## Источники

- [Задание практики 2](https://edu.susu.ru/mod/assign/view.php?id=8720330).
- [FastAPI: приложение в Docker](https://fastapi.tiangolo.com/deployment/docker/).
- [Docker: установка на Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
- [Docker: сборка для нескольких платформ](https://docs.docker.com/build/building/multi-platform/).
