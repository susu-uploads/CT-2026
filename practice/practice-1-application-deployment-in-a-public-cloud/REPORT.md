# Практическая работа 1. LAMP и WordPress в публичном облаке

Автор: Бабушкин Михаил Вадимович. Выполнение и проверки: 17 октября 2026 года.

## Задание и результат

Задание требует зарегистрироваться у облачного провайдера, создать виртуальную машину и показать удаленное управление, установить LAMP и WordPress. Регистрацию, заказ VPS, первоначальное обновление Ubuntu и перезагрузку выполнил студент. Установка и проверки ниже выполнены по SSH под пользователем practice1 с временно разрешенным sudo без пароля.

Провайдер — HOSTKEY. Сервер Ubuntu 24.04.5 LTS x86_64, около 6 ГБ RAM и 118 GiB в корневой файловой системе. Фактические сведения о регистрации и заказе необходимо дополнить скриншотом кабинета без платежных данных.

Публичный сайт: <http://176.222.53.58/>.

Тестовая публикация: <http://176.222.53.58/?p=4>.

## Установка и размещение

Установлены Apache, MySQL, PHP и расширения PHP для WordPress через apt. Повторное общее обновление системы и перезагрузка не выполнялись: студент уже сделал их перед передачей доступа.

```bash
sudo apt-get install -y apache2 mysql-server \
  php libapache2-mod-php php-mysql php-cli php-curl \
  php-mbstring php-xml php-zip php-gd php-intl \
  curl unzip openssl ufw
sudo systemctl enable --now apache2 mysql
sudo a2enmod rewrite
```

При первоначальной проверке обнаружено несоответствие hostname и записи /etc/hosts. Перед исправлением сохранена копия; добавлена запись для текущего имени nl-vmmini. Предупреждение sudo о невозможности разрешить имя устранено.

Файлы WordPress размещены в /var/www/practice1, владелец practice1, группа www-data. Каталоги имеют права 750, файлы — 640. Каталог wp-content/uploads доступен для записи www-data. Apache работает от www-data, MySQL — от mysql. Установка системных пакетов через sudo не изолирует практику от остального VPS.

Созданы отдельная БД wordpress и пользователь wordpress@localhost с правами только на эту БД. MySQL слушает loopback, внешнего доступа к БД нет.

WP-CLI 2.12.0 установлен из официального Phar-архива. WordPress 7.1.3 ru_RU скачан из официального источника. Первоначальная распаковка WP-CLI усекла длинные имена части файлов. Сохранена резервная копия, файлы восстановлены GNU tar из того же официального архива. После восстановления проверка официальных контрольных сумм прошла полностью.

Настроен отдельный VirtualHost /etc/apache2/sites-available/practice1.conf, стандартный 000-default отключен. Конфигурация Apache до изменения сохранена в /root/practice1-backup/. Сайт использует порт 80; Docker, другие практики, домен и HTTPS не устанавливались.

Установка WordPress завершена через WP-CLI; создан администратор practice1 и опубликована запись «Практическая работа 1: облачный сервер». Для установки использован технический адрес practice1@example.invalid; реальный адрес студента и почтовые уведомления не настраивались.

## Актуальные настройки доступа — 18 октября 2026 года

По указанию студента UFW отключен, включая запуск при загрузке. Команды: `sudo -n ufw disable` и `sudo -n ufw status`; результат — `Status: inactive`. Прежние правила сохранены в конфигурации UFW, но не применяются. Ограничение SSH текущим IP со стороны UFW больше не действует. Правила провайдера не изменялись.

Ограничение Apache `Require local` для wp-admin и wp-login сохранено: администрирование остается через SSH. Созданный студентом файл /etc/sudoers.d/90-practice1-temporary оставлен по его просьбе; sudo без пароля доступен. Описание включенного UFW и удаления временного sudo ниже относится к завершению установки 17 октября и является историческим.

## Доступ и секреты при установке 17 октября

- SSH-настройки аутентификации не изменялись; подтвержден новый вход по ключу под practice1.
- UFW включен: входящий трафик по умолчанию запрещен, SSH/22 разрешен с текущего публичного IP Mac, HTTP/80 открыт публично. При смене внешнего IP студента правило SSH понадобится обновить через существующую сессию или консоль провайдера.
- /wp-admin/ и /wp-login.php доступны только локальным запросам сервера; с Mac возвращают 403. Администрирование выполняется через WP-CLI по SSH. Публичный HTTP не используется для ввода паролей.
- wp-config.php закрыт для HTTP; редактор файлов WordPress отключен.
- Пароли БД и администратора сгенерированы на сервере и сохранены в /home/practice1/.config/practice1/credentials с правами 600, владелец practice1. Их значения в репозиторий и отчет не включены.
- При первоначальном запуске интерактивного режима WP-CLI пароли появились в служебном выводе. Оба пароля немедленно заменены без вывода новых значений; текущие секреты остались на сервере.
- Временный /etc/sudoers.d/90-practice1-temporary удален после установки. Проверка sudoers успешна; practice1 сохранил обычный sudo с паролем. Новый SSH-вход работает, sudo -n без пароля больше не проходит.

## Проверки

| Проверка | Результат |
|---|---|
| SSH с Mac под practice1 | Пройден, в том числе после включения UFW и удаления временного sudo |
| PHP через Apache | Временная страница вернула PHP OK; затем удалена |
| MySQL | Запрос версии и проверка таблиц WordPress прошли |
| Apache | 2.4.58; конфигурация Syntax OK |
| PHP | 8.3.6, пакет Ubuntu с исправлениями безопасности |
| MySQL | 8.0.46 |
| WordPress | 7.1.3 ru_RU; официальные контрольные суммы совпадают |
| Службы Apache и MySQL | Обе active и enabled |
| Главная страница с Mac | HTTP 200, название сайта и тестовая публикация присутствуют |
| Тестовая публикация в браузере | Открывается по публичному IP |
| /wp-login.php, /wp-admin/, /wp-config.php с Mac | HTTP 403 |
| Удаленная диагностическая PHP-страница | HTTP 404 |
| БД во внешней сети | Не публикуется, MySQL слушает 127.0.0.1 |
| Перезагрузка после установки | Не выполнялась; проверен включенный автозапуск |
| Скриншот кабинета, сдача в Moodle | Ожидаются от студента |

[Фактический вывод серверных проверок](БабушкинМВ-server-checks.txt).

![Главная страница WordPress](БабушкинМВ-wordpress.png)

![Тестовая публикация](БабушкинМВ-publication.png)

![Проверки сервера](БабушкинМВ-lamp-checks.png)

Снимок проверок создан из HTML-представления фактического вывода команд, а не из интерфейса терминала. Публичные страницы сняты непосредственно в браузере.

## Оставшиеся действия

Добавить скриншот регистрации/созданной VM из кабинета HOSTKEY без секретов, продемонстрировать работу преподавателю и сдать результат. По сохраненному TASK.md технические задания дают до 18 баллов, после 11 октября бонус за срок равен 0; оценку выставляет преподаватель.

VM и данные сохраняются до подтверждения сдачи. Удаление сервера и других оплачиваемых ресурсов согласовать отдельно.

## Журнал использованных команд

Ниже приведены команды фактического выполнения, включая диагностику и исправления. Повторные однотипные проверки объединены. Это исторический журнал, а не скрипт повторной установки: база, пользователь и файлы уже существуют. Значения сгенерированных паролей и исходный IP Mac не приводятся.

### Подключение и первоначальная диагностика

На Mac:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=15 practice1@176.222.53.58
```

В SSH-сессии:

```bash
id
cat /etc/os-release
uname -m
free -h
df -h /
sudo -n true
printf 'sudo_exit=%s\n' "$?"
ss -ltn
command -v apache2
command -v mysql
command -v php
```

Первый `sudo -n true` завершился сообщением о необходимости пароля. Установка была остановлена до изменения студентом временного правила sudo. После его создания выполнены:

```bash
sudo -n true
hostname
cat /etc/hosts
sudo -n ufw status
sudo -n ls /etc/apache2/sites-enabled
```

UFW и Apache тогда еще отсутствовали. `-n` запрещает запрос пароля в неинтерактивной сессии; пароль студента агенту не передавался.

Привилегированные блоки ниже передавались с Mac через стандартный ввод:

```bash
ssh -o BatchMode=yes practice1@176.222.53.58 'sudo -n bash -s' <<'REMOTE'
# Здесь выполнялся соответствующий блок команд от root.
REMOTE
```

### Резервная копия hosts, исправление hostname и установка пакетов

В привилегированном блоке:

```bash
set -eu
install -d -m 700 /root/practice1-backup
cp -an /etc/hosts /root/practice1-backup/hosts

if ! getent hosts "$(hostname)" >/dev/null; then
    printf '127.0.1.1 %s\n' "$(hostname)" >> /etc/hosts
fi

export DEBIAN_FRONTEND=noninteractive
apt-get install -y apache2 mysql-server php libapache2-mod-php \
  php-mysql php-cli php-curl php-mbstring php-xml php-zip \
  php-gd php-intl curl unzip openssl ufw

systemctl enable --now apache2 mysql
a2enmod rewrite
```

`apt update`, общее обновление пакетов и перезагрузку агент не запускал: студент уже выполнил их ранее. Команда `cp -an` сохранила исходный hosts без перезаписи существующей копии.

### Проверка PHP и установка WP-CLI

В привилегированном блоке:

```bash
printf '%s\n' '<?php echo "PHP OK\n";' > /var/www/html/practice1-check.php
curl --fail -sS http://127.0.0.1/practice1-check.php
rm /var/www/html/practice1-check.php
mysql -N -e 'SELECT VERSION();'

if [ -e /var/www/practice1/wp-config.php ]; then
    echo 'WordPress already configured; refusing to overwrite' >&2
    exit 1
fi

curl --fail --location --silent --show-error \
  https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar \
  -o /tmp/practice1-wp-cli.phar
php /tmp/practice1-wp-cli.phar --info
install -m 755 /tmp/practice1-wp-cli.phar /usr/local/bin/wp
rm /tmp/practice1-wp-cli.phar
```

### Создание БД, конфигурации и публикации WordPress

В привилегированном блоке:

```bash
install -d -o practice1 -g www-data -m 750 /var/www/practice1
install -d -o practice1 -g practice1 -m 700 /home/practice1/.config/practice1
credentials=/home/practice1/.config/practice1/credentials

if [ -e "$credentials" ]; then
    echo 'Credential file exists; refusing to replace' >&2
    exit 1
fi

umask 077
DB_PASSWORD=$(openssl rand -hex 24)
WP_ADMIN_PASSWORD=$(openssl rand -hex 24)
printf 'DB_PASSWORD=%s\nWP_ADMIN_PASSWORD=%s\nWP_ADMIN_USER=practice1\n' \
  "$DB_PASSWORD" "$WP_ADMIN_PASSWORD" > "$credentials"
chown practice1:practice1 "$credentials"

mysql <<SQL
CREATE DATABASE wordpress CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wordpress'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'localhost';
SQL

cd /var/www/practice1
sudo -u practice1 -H wp core download --locale=ru_RU

printf '%s\n' "$DB_PASSWORD" |
  sudo -u practice1 -H wp config create \
    --dbname=wordpress --dbuser=wordpress --dbhost=localhost --prompt=dbpass

sudo -u practice1 -H wp config set DISALLOW_FILE_EDIT true --raw

printf '%s\n' "$WP_ADMIN_PASSWORD" |
  sudo -u practice1 -H wp core install \
    --url='http://176.222.53.58' \
    --title='Практика 1 — Облачные технологии' \
    --admin_user=practice1 --admin_email=practice1@example.invalid \
    --skip-email --prompt=admin_password

unset DB_PASSWORD WP_ADMIN_PASSWORD

sudo -u practice1 -H wp post create \
  --post_type=post --post_status=publish \
  --post_title='Практическая работа 1: облачный сервер' \
  --post_content='Выполнил Бабушкин Михаил Вадимович. WordPress развернут на облачной виртуальной машине HOSTKEY. Используются Linux, Apache, MySQL и PHP.'

chown -R practice1:www-data /var/www/practice1
find /var/www/practice1 -type d -exec chmod 750 {} +
find /var/www/practice1 -type f -exec chmod 640 {} +
install -d -o www-data -g www-data -m 750 /var/www/practice1/wp-content/uploads
```

Исторические команды `--prompt=dbpass` и `--prompt=admin_password` приведены для полноты журнала. В этой версии WP-CLI интерактивный режим вывел развернутую команду с секретами. После этого использован следующий способ замены без вывода значений; текущие пароли отличаются от первоначальных.

### Замена паролей без вывода значений

С Mac выполнен отдельный Python-блок на сервере:

```bash
ssh -o BatchMode=yes practice1@176.222.53.58 'sudo -n python3 -' <<'PY'
from pathlib import Path
import secrets
import re
import subprocess

credentials = Path('/home/practice1/.config/practice1/credentials')
new_db = secrets.token_hex(24)
new_admin = secrets.token_hex(24)

subprocess.run(
    ['mysql'],
    input=f"ALTER USER 'wordpress'@'localhost' IDENTIFIED BY '{new_db}';\n",
    text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
)

p = Path('/var/www/practice1/wp-config.php')
s = p.read_text()
s, count = re.subn(
    r"(define\(\s*'DB_PASSWORD',\s*)'[^']*'",
    lambda m: m.group(1) + repr(new_db), s,
)
assert count == 1
p.write_text(s)

subprocess.run(
    ['sudo', '-u', 'practice1', '-H', 'wp', '--path=/var/www/practice1',
     'eval', "$u=get_user_by('login','practice1'); if (!$u) { exit(1); } wp_set_password(trim(stream_get_contents(STDIN)), $u->ID);"],
    input=new_admin + '\n', text=True,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
)

credentials.write_text(
    f'DB_PASSWORD={new_db}\nWP_ADMIN_PASSWORD={new_admin}\nWP_ADMIN_USER=practice1\n'
)
credentials.chmod(0o600)
print('Database and WordPress credentials rotated; values not printed.')
PY
```

### Конфигурация Apache

Этот блок был выполнен до первой проверки контрольных сумм и последующего восстановления файлов WordPress. В отчете он выделен отдельно от команд управления секретами.

```bash
cp -a /etc/apache2 /root/practice1-backup/apache2-before-site

cat > /etc/apache2/sites-available/practice1.conf <<'APACHE'
<VirtualHost *:80>
    ServerName 176.222.53.58
    DocumentRoot /var/www/practice1
    <Directory /var/www/practice1>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    <Files "wp-config.php">
        Require all denied
    </Files>
    <LocationMatch "^/(wp-admin(?:/|$)|wp-login\.php$)">
        Require local
    </LocationMatch>
    ErrorLog ${APACHE_LOG_DIR}/practice1-error.log
    CustomLog ${APACHE_LOG_DIR}/practice1-access.log combined
</VirtualHost>
APACHE

a2ensite practice1
a2dissite 000-default
apache2ctl configtest
systemctl restart apache2
sudo -u practice1 -H wp core verify-checksums
```

Первая проверка контрольных сумм завершилась ошибкой. Последующие команды первоначального блока (`wp db check` и проверки служб) из-за `set -e` тогда не выполнились; они выполнены после исправления и при итоговой проверке.

### Диагностика распаковки и восстановление файлов

В SSH-сессии проверены версия, службы, порты и архив:

```bash
wp --path=/var/www/practice1 core version
sudo -n systemctl is-active apache2 mysql
sudo -n ss -ltnp
find /home/practice1/.wp-cli/cache -type f -name '*7.1.3*'
find /var/www/practice1/wp-includes/php-ai-client -type f |
  awk 'length($0)>110 {print; n++; if(n==4) exit}'
```

Python сравнил имена файлов в официальном архиве и на диске. Найдены 39 отсутствовавших путей и 21 лишний усеченный путь внутри php-ai-client:

```python
from pathlib import Path
import tarfile

archive = Path('/home/practice1/.wp-cli/cache/core/wordpress-7.1.3-ru_RU.tar.gz')
root = Path('/var/www/practice1')
with tarfile.open(archive) as t:
    members = [m.name for m in t.getmembers()
               if 'php-ai-client' in m.name and len(m.name) > 100]
    print('Long archive paths:', len(members))
    print('\n'.join(members[:3]))
with tarfile.open(archive) as t:
    names = {m.name.removeprefix('wordpress/') for m in t.getmembers() if m.isfile()}
missing = [name for name in names if not (root / name).is_file()]
extras = [str(f.relative_to(root))
          for f in (root / 'wp-includes/php-ai-client').rglob('*')
          if f.is_file() and str(f.relative_to(root)) not in names]
print('Missing:', len(missing), 'Extra truncated:', len(extras))
print('\n'.join(extras[:3]))
```

Затем в привилегированном блоке сохранена копия поврежденного каталога, удалены только лишние файлы и выполнена распаковка GNU tar:

```bash
cp -a /var/www/practice1/wp-includes/php-ai-client \
  /root/practice1-backup/php-ai-client-before-repair

python3 - <<'PY'
from pathlib import Path
import tarfile
root = Path('/var/www/practice1')
archive = Path('/home/practice1/.wp-cli/cache/core/wordpress-7.1.3-ru_RU.tar.gz')
with tarfile.open(archive) as t:
    names = {m.name.removeprefix('wordpress/') for m in t.getmembers() if m.isfile()}
for f in (root / 'wp-includes/php-ai-client').rglob('*'):
    if f.is_file() and str(f.relative_to(root)) not in names:
        f.unlink()
PY

tar -xzf /home/practice1/.wp-cli/cache/core/wordpress-7.1.3-ru_RU.tar.gz \
  --strip-components=1 --no-same-owner -C /var/www/practice1
chown -R practice1:www-data /var/www/practice1
find /var/www/practice1 -type d -exec chmod 750 {} +
find /var/www/practice1 -type f -exec chmod 640 {} +
chown www-data:www-data /var/www/practice1/wp-content/uploads

sudo -u practice1 -H wp --path=/var/www/practice1 \
  core verify-checksums --locale=ru_RU
sudo -u practice1 -H wp --path=/var/www/practice1 db check
apache2ctl configtest
systemctl is-enabled apache2 mysql
```

Контрольные суммы и проверка БД после исправления прошли.

### Firewall и повторный SSH-вход

Этот блок выполнен в обычной SSH-сессии practice1, где доступна переменная SSH_CONNECTION:

```bash
set -eu
client_ip=${SSH_CONNECTION%% *}
ssh_port=$(printf '%s\n' "$SSH_CONNECTION" | awk '{print $4}')

sudo -n ufw allow from "$client_ip" to any port "$ssh_port" proto tcp >/dev/null
sudo -n ufw allow 80/tcp >/dev/null
sudo -n ufw default deny incoming >/dev/null
sudo -n ufw default allow outgoing >/dev/null
sudo -n ufw --force enable >/dev/null
```

С Mac открыта новая сессия без использования существующего SSH multiplexing-соединения:

```bash
ssh -o BatchMode=yes -o ControlMaster=no -o ControlPath=none \
  -o ConnectTimeout=15 practice1@176.222.53.58 \
  'whoami; curl -sS -o /dev/null -w "HTTP local: %{http_code}\n" http://127.0.0.1/'
```

Получены practice1 и HTTP 200.

### Итоговые проверки на сервере

Команды выполнялись под practice1; привилегированные проверки — через sudo:

```bash
whoami
cat /etc/os-release
uname -m
free -h
df -h /
apache2 -v
php -v | head -1
sudo -n mysql -N -e 'SELECT VERSION();'
wp --path=/var/www/practice1 core version
wp --path=/var/www/practice1 core verify-checksums --locale=ru_RU
wp --path=/var/www/practice1 db check
systemctl is-active apache2 mysql
systemctl is-enabled apache2 mysql
sudo -n ss -ltnp | sed -E 's/users:.*//'
sudo -n ufw status verbose |
  sed -E 's/([0-9]{1,3}\.){3}[0-9]{1,3}/<IPv4>/g'
wp --path=/var/www/practice1 post list \
  --post_type=post --post_status=publish --fields=ID,post_title --format=json
sudo -n visudo -c
sudo -n -l
stat -c '%a %U:%G %n' \
  /home/practice1/.config/practice1/credentials \
  /var/www/practice1/wp-config.php
```

Вывод безопасных проверок сохранен в БабушкинМВ-server-checks.txt. В отчете firewall исходный IP Mac заменен маркером; содержимое credentials и wp-config.php не выводилось.

С Mac выполнена внешняя HTTP-проверка:

```bash
python3 - <<'PY'
from urllib.request import urlopen
from urllib.error import HTTPError

base = 'http://176.222.53.58'
for path, expected in [('/', 200), ('/wp-login.php', 403),
                       ('/wp-admin/', 403), ('/wp-config.php', 403),
                       ('/practice1-check.php', 404)]:
    try:
        with urlopen(base + path, timeout=20) as response:
            status = response.status
            body = response.read().decode()
    except HTTPError as error:
        status, body = error.code, ''
    assert status == expected, (path, status)
    if path == '/':
        assert 'Практика 1' in body and 'Практическая работа 1' in body
    print(path, status)
PY
```

### Удаление временного sudo без пароля

Последний привилегированный блок:

```bash
set -eu
rm /etc/sudoers.d/90-practice1-temporary
visudo -c
sudo -l -U practice1
```

В новой SSH-сессии:

```bash
id
if sudo -n true 2>/dev/null; then
    echo 'Unexpected passwordless sudo remains'
    exit 1
else
    echo 'Temporary passwordless sudo removed; password required again.'
fi
test ! -e /etc/sudoers.d/90-practice1-temporary
```

Проверка sudoers после удаления успешна; у practice1 осталось правило обычного sudo `(ALL : ALL) ALL`.

### Скриншоты и локальная проверка файлов

На Mac использован Playwright CLI. Команды выполнялись из /tmp; полные пути указаны для сохранения файлов непосредственно в папку практики:

```bash
PWCLI=/Users/mikhail/.codex/skills/playwright/scripts/playwright_cli.sh
PRACTICE=/Users/mikhail/Developer/2026-autumn/CT-2026/practice/practice-1-application-deployment-in-a-public-cloud

"$PWCLI" -s=ct-practice1 open http://176.222.53.58 --headed
"$PWCLI" -s=ct-practice1 screenshot --full-page \
  --filename "$PRACTICE/БабушкинМВ-wordpress.png"
"$PWCLI" -s=ct-practice1 goto 'http://176.222.53.58/?p=4'
"$PWCLI" -s=ct-practice1 screenshot --full-page \
  --filename "$PRACTICE/БабушкинМВ-publication.png"
```

Для снимка проверок локальный Python прочитал БабушкинМВ-server-checks.txt, экранировал текст через html.escape и записал HTML в игнорируемый .report/checks.html. Сервер представления запускался командой:

```bash
python3 -m http.server 8767 --bind 127.0.0.1 \
  --directory CT-2026/practice/practice-1-application-deployment-in-a-public-cloud/.report
```

В другом локальном процессе:

```bash
"$PWCLI" -s=ct-practice1-checks open http://127.0.0.1:8767/checks.html
"$PWCLI" -s=ct-practice1-checks screenshot --full-page \
  --filename "$PRACTICE/БабушкинМВ-lamp-checks.png"
```

После снимка локальный сервер остановлен Ctrl+C. Изображения просмотрены перед завершением работы. Проверки репозитория:

```bash
git -C CT-2026 status --short
git -C CT-2026 diff --check
git -C CT-2026 lfs fsck
```

Дополнительно локальный Python проверил REPORT.md, TODO.md и текстовый журнал на отсутствие приватного SSH-ключа и присваиваний фактических паролей. Коммит и push при развертывании практики 1 не выполнялись.
