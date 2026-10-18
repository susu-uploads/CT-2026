# Практическая работа 2. Одноконтейнерное веб-приложение

## Что сделано

**Дисциплина:** Облачные технологии

**Автор:** Бабушкин Михаил Вадимович

**Дата последней локальной и облачной проверки:** 18 октября 2026 года

### 1. Цель и результат

Изучить создание Docker-образа, запуск контейнера с веб-приложением и его публикацию для последующего развертывания в публичном облаке.

Реализован калькулятор на Python 3.12 и FastAPI. Пользователь вводит два числа, выбирает действие и получает результат без перезагрузки страницы. Сервер выполняет сложение, вычитание, умножение и деление. Страница и API обслуживаются одним процессом Uvicorn в одном контейнере.

Приложение проверено локально на Mac ARM64 и развернуто на VPS x86_64 18 октября 2026 года. Публичный адрес: <http://176.222.53.58:8080/>. Образ передан по SSH без registry. Используется имя ct-2026-practice-2-calculator. Сдача преподавателю не подтверждена.

### 2. Файлы и HTTP API

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

### 3. Окружение Python и запуск без Docker

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

### 4. Локальная сборка и проверка ARM64

Выполнено на Mac из каталога практики. Dockerfile, код приложения, API и зависимости сохранены без изменений.

```bash
docker buildx build --platform linux/arm64 --load \
  -t ct-2026-practice-2-calculator:2026-10-18-arm64 .
docker run -d --name ct-2026-practice-2-calculator \
  -p 127.0.0.1:8000:8000 \
  ct-2026-practice-2-calculator:2026-10-18-arm64
curl --retry 10 --retry-all-errors --retry-delay 1 --max-time 5 \
  --fail -sS http://127.0.0.1:8000/health
python3 test_app.py http://127.0.0.1:8000
```

Контейнер остается запущенным на loopback Mac. При повторной работе не выполнять docker run поверх существующего имени: использовать docker start или плановое пересоздание после сборки.

### 5. Сборка AMD64 и передача на VPS

Пользователя practice2 создал студент и добавил в группы sudo и docker. Новый SSH-вход подтвердил группу docker и доступ к Engine без sudo. Engine 29.9.1 и Compose уже были установлены; агент их не переустанавливал.

Проверки на VPS после подключения `ssh -o BatchMode=yes -o ConnectTimeout=15 practice2@176.222.53.58`:

```bash
id
docker info --format '{{.ServerVersion}} {{.Architecture}}'
docker ps -a --format '{{.Names}} {{.Image}} {{.Status}} {{.Ports}}'
docker image ls --format '{{.Repository}}:{{.Tag}}'
ss -ltn
systemctl is-active apache2 mysql
```

На VPS порт 8080 был свободен, образы и контейнеры отсутствовали. На Mac выполнены:

```bash
docker buildx build --platform linux/amd64 --load \
  -t ct-2026-practice-2-calculator:2026-10-18-amd64 .
mkdir -p .cache .report
docker save -o .cache/ct-2026-practice-2-calculator-2026-10-18-amd64.tar \
  ct-2026-practice-2-calculator:2026-10-18-amd64
shasum -a 256 .cache/ct-2026-practice-2-calculator-2026-10-18-amd64.tar
ssh -o BatchMode=yes practice2@176.222.53.58 'mkdir -p ~/ct-2026-practice-2'
scp -o BatchMode=yes .cache/ct-2026-practice-2-calculator-2026-10-18-amd64.tar \
  practice2@176.222.53.58:ct-2026-practice-2/
ssh -o BatchMode=yes practice2@176.222.53.58 \
  'sha256sum ~/ct-2026-practice-2/ct-2026-practice-2-calculator-2026-10-18-amd64.tar'
```

Обе суммы совпали: `3b7acb2174fb1aebaa24c7be2ddc3631312c02cd1e4a9be6d7fc3da0f7c607ff`.

Архив на Mac находится в игнорируемом .cache/, на сервере — в /home/practice2/ct-2026-practice-2/. Registry не нужен. Docker — общая системная служба; хранение архива в домашней папке не изолирует daemon. Группа docker дает фактически административный доступ к VPS.

### 6. Развертывание и проверки на VPS

#### Загрузка и запуск

В SSH-сессии practice2 выполнены:

```bash
set -eu
docker load -i ~/ct-2026-practice-2/ct-2026-practice-2-calculator-2026-10-18-amd64.tar
docker image inspect ct-2026-practice-2-calculator:2026-10-18-amd64 \
  --format '{{.Os}}/{{.Architecture}}'
docker run -d --name ct-2026-practice-2-calculator \
  --restart unless-stopped -p 8080:8000 \
  ct-2026-practice-2-calculator:2026-10-18-amd64
curl --retry 10 --retry-all-errors --retry-delay 1 --max-time 5 \
  --fail -sS http://127.0.0.1:8080/health
docker exec ct-2026-practice-2-calculator id
docker exec ct-2026-practice-2-calculator python --version
docker exec ct-2026-practice-2-calculator python -m pip check
docker inspect ct-2026-practice-2-calculator \
  --format '{{.HostConfig.RestartPolicy.Name}}'
```

Образ — linux/amd64, Python 3.12.15, процесс — UID 10001(app), без root. Docker направляет публичный порт 8080 на 8000 внутри контейнера. Порт 80 WordPress сохраняется. Firewall и конфигурации Apache/MySQL не менялись, UFW не включался.

С Mac выполнен внешний тест:

```bash
python3 test_app.py http://176.222.53.58:8080
```

Форма в браузере проверена: 6 / 2 = 3, деление на ноль показывает ошибку, после исправления снова получается 3. Swagger UI открывается по <http://176.222.53.58:8080/docs>.

#### Остановка и повторный запуск

```bash
ssh -o BatchMode=yes practice2@176.222.53.58 \
  'docker stop ct-2026-practice-2-calculator'
```

С Mac подтверждена недоступность остановленного контейнера:

```bash
python3 - <<'PY'
from urllib.request import urlopen
from urllib.error import URLError
try:
    urlopen('http://176.222.53.58:8080/health', timeout=5)
    raise AssertionError('Stopped container is still reachable')
except URLError:
    print('Stopped container: unavailable as expected')
PY

ssh -o BatchMode=yes practice2@176.222.53.58 \
  'docker start ct-2026-practice-2-calculator'
curl --retry 10 --retry-all-errors --retry-delay 1 --max-time 5 \
  --fail -sS http://176.222.53.58:8080/health
python3 test_app.py http://176.222.53.58:8080
```

Полный HTTP-тест после запуска прошел. Краткие ошибки соединения во время старта были обработаны curl с retry.

#### Восстановление после перезапуска Docker

На VPS перед перезапуском проверено отсутствие других работающих контейнеров. Для systemctl оказался доступен sudo без пароля; Docker-команды выполнялись без sudo. Правила sudo агент не создавал и не изменял.

```bash
set -eu
others=$(docker ps --format '{{.Names}}' | sed '/^ct-2026-practice-2-calculator$/d')
if [ -n "$others" ]; then
    echo 'Docker restart skipped: other containers are running'
    exit 1
fi
sudo -n systemctl restart docker
curl --retry 15 --retry-all-errors --retry-delay 1 --max-time 5 \
  --fail -sS http://127.0.0.1:8080/health
docker ps --filter name=ct-2026-practice-2-calculator \
  --format '{{.Names}} {{.Status}}'
systemctl is-active apache2 mysql
```

Затем с Mac снова прошел `python3 test_app.py http://176.222.53.58:8080`. Контейнер восстановился автоматически. Ручной docker stop оставляет контейнер остановленным до явного запуска — это поведение unless-stopped.

Работа WordPress проверена отдельно с Mac:

```bash
python3 - <<'PY'
from urllib.request import urlopen
with urlopen('http://176.222.53.58/', timeout=15) as response:
    assert response.status == 200 and 'Практика 1' in response.read().decode()
print('WordPress on port 80: OK')
PY
```

### 7. Фактические локальные проверки

#### Проверки 2 октября 2026 года

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

#### Повторная проверка 17 октября 2026 года

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

### 8. Вывод

Веб-приложение упаковано в один Docker-контейнер и доступно локально через опубликованный порт. Один и тот же набор HTTP-проверок прошел при обычном запуске Python и в контейнерах ARM64 и AMD64. Облачная часть выполнена 18 октября 2026 года. Проверены публичная доступность, HTTP API, форма и восстановление контейнера после перезапуска Docker. Сдача преподавателю пока не подтверждена.

### Источники

- [Задание практики 2](https://edu.susu.ru/mod/assign/view.php?id=8720330).
- [FastAPI: приложение в Docker](https://fastapi.tiangolo.com/deployment/docker/).
- [Docker: установка на Ubuntu](https://docs.docker.com/engine/install/ubuntu/).
- [Docker: сборка для нескольких платформ](https://docs.docker.com/build/building/multi-platform/).

### 9. Результат 18 октября 2026 года и удаление старых образов

| Проверка | Фактический результат |
|---|---|
| SSH practice2 и группа docker | Подтверждены; Docker доступен без sudo |
| ARM64 на Mac | Сборка и HTTP-тест прошли |
| AMD64 на VPS | Сборка, передача, проверка SHA-256 и запуск прошли |
| Внешний HTTP-тест | Прошел после запуска, остановки/запуска и перезапуска Docker |
| Форма и Swagger UI | Проверены в браузере |
| UID контейнера | 10001(app), без root |
| pip check | Конфликтов нет |
| Restart policy | unless-stopped; восстановление после перезапуска daemon проверено |
| WordPress и MySQL | Работают; публичная страница WordPress возвращает 200 |
| Старые контейнеры и теги практики 2 | Удалены на Mac; на VPS их не было |
| Практики 3–4 и сторонние образы | Не изменялись |
| Сдача | Не подтверждена |

После проверки новых образов на Mac осмотрены старые контейнеры: оба остановлены, подключенных томов нет. Затем выполнены:

```bash
docker inspect susu-cloud-practice2 susu-cloud-practice2-20261002 \
  --format '{{.Name}} mounts={{json .Mounts}} image={{.Config.Image}}'
docker rm susu-cloud-practice2 susu-cloud-practice2-20261002
docker image rm susu-cloud-practice2:1.0 \
  susu-cloud-practice2:1.0-amd64 susu-cloud-practice2:2026-10-17
docker image ls --format '{{.Repository}}:{{.Tag}}'
```

Удаление выполнялось без force и без общего prune. Отдельная проверка подтвердила отсутствие тегов susu-cloud-practice2. На VPS проверены docker image ls и docker ps: остались новый образ и новый контейнер. Исторические журналы и снимки раздела 7 сохраняют прежние имена; они описывают прошлое состояние, а не текущие контейнеры.

Итоговый журнал: [вывод облачных проверок](БабушкинМВ-cloud-checks.txt). В нем приведены команды docker version, ps, image inspect, inspect, exec, sha256sum и systemctl is-active вместе с фактическим выводом. После очистки старых образов HTTP-тесты локального и облачного контейнеров также прошли.

Для создания новых скриншотов использован Playwright CLI на Mac:

```bash
PWCLI=/Users/mikhail/.codex/skills/playwright/scripts/playwright_cli.sh
PRACTICE=/Users/mikhail/Developer/2026-autumn/CT-2026/practice/practice-2-container-creation-and-management-in-public-clouds-single-container-application
"$PWCLI" -s=ct-practice2-vps open http://176.222.53.58:8080 --headed
```

После snapshot выполнены `click e13`, снимок результата, `fill e10 0`, `click e13`, снимок ошибки, затем `fill e10 2`, `click e13` и проверка восстановления. Референсы относятся к снимку этой страницы; при повторном запуске нужно получить новые через snapshot. Для проверки документации выполнены goto http://176.222.53.58:8080/docs и snapshot. Команды сохранения:

```bash
"$PWCLI" -s=ct-practice2-vps screenshot \
  --filename "$PRACTICE/БабушкинМВ-cloud-calculator.png"
"$PWCLI" -s=ct-practice2-vps screenshot \
  --filename "$PRACTICE/БабушкинМВ-cloud-error.png"
```

Эти две команды выполнялись в соответствующих состояниях формы. Во время системного перезапуска Docker один запрос формы попал на кратковременную недоступность сервиса; после восстановления повторное вычисление прошло. Изменений кода для этого не требовалось.

Для снимка контейнера фактический текст журнала преобразован в HTML через html.escape и сохранен в игнорируемой .report/cloud-checks.html. Запуск локального просмотра и снимок:

```bash
python3 -m http.server 8768 --bind 127.0.0.1 --directory .report
"$PWCLI" -s=ct-practice2-evidence open http://127.0.0.1:8768/cloud-checks.html
"$PWCLI" -s=ct-practice2-evidence screenshot --full-page \
  --filename "$PRACTICE/БабушкинМВ-cloud-container.png"
```

Снимок контейнера — представление фактического вывода команд, а не интерфейс Docker Desktop. Архивы, промежуточный HTML и исходники приложения в Git не добавлялись повторно; код приложения не изменялся. Изменения практики 2 подготовлены отдельным коммитом для публикации по запросу студента.

![Облачный калькулятор](БабушкинМВ-cloud-calculator.png)

![Ошибка деления на ноль](БабушкинМВ-cloud-error.png)

![Облачный контейнер и проверки](БабушкинМВ-cloud-container.png)

## Как сдавать

### Показать приложение и HTTP API

Открыть http://176.222.53.58:8080/. Выполнить сложение, вычитание, умножение и деление; затем деление на ноль и повторный расчет после исправления. Показать понятную ошибку без traceback. Открыть `/health` и `/docs` на том же адресе.

### Показать образ и контейнер

Подключиться к VPS и проверить контейнер:

```bash
ssh practice2@176.222.53.58
docker ps --filter name=ct-2026-practice-2-calculator
docker inspect ct-2026-practice-2-calculator --format '{{.Config.Image}} {{.HostConfig.RestartPolicy.Name}}'
```

Объяснить: один контейнер содержит FastAPI и Uvicorn; внешний порт 8080 перенаправлен на 8000 контейнера. На VPS используется AMD64-образ, на Mac — ARM64. Образ передан через docker save/SSH/docker load без registry.

### Показать остановку и восстановление

```bash
docker stop ct-2026-practice-2-calculator
docker start ct-2026-practice-2-calculator
```

После остановки приложение недоступно; после запуска и готовности `/health` снова работает. Показать `unless-stopped`. Docker daemon во время сдачи не перезапускать: теперь на сервере работают другие практики.

### Подтвердить проверки и сдать

На Mac из папки практики:

```bash
python3 test_app.py http://176.222.53.58:8080
```

Для основной части показать локальный контейнер на http://127.0.0.1:8000/ и ARM64-образ; для дополнительной — публичный адрес VPS. Приложить отчет, журналы и скриншоты. После демонстрации оставить контейнер запущенным.
