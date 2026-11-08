# Процесс разработки 1С (сервер)

Единое описание: хранилище, репозитории, сборка, запуск и проверка.
Дополняет `AGENTS.md` (глобальные правила) и `_store\README.md` (правила хранилища).

## Источники правды

| Что | Где |
|---|---|
| Базы, v8path, default | `_store\.v8-project.json` |
| Эталон XML конфигурации | `_store\reference\config\<ИмяКонфигурации>_<Версия>` (read-only) |
| Эталон XML расширений | `_store\reference\extensions\<Имя>\<Версия>` (read-only) |
| Вендорские CFE | `_store\vendor\extensions` |
| CF/CFE сборки конфигурации | `_store\vendor\config` (для развёртывания с нуля) |
| Опубликованные сборки | `_store\extensions\<Имя>\<X.Y.Z>\<Имя>_v<X.Y.Z>.cfe` (create-only) |
| Исходники расширения | `<Проект>\src\cfe\<Имя>` (git проекта) |
| Сборки проекта | `<Проект>\build` |
| Чек-листы | `<Проект>\checks` |

## Поток

1. Правка XML в `src\cfe\<Имя>` (эталоны — в `_store\reference`; типовую не меняем).
2. Сборка CFE: `db-load-xml` (свободная база) → `db-update` → `db-dump-cf` → `build`.
3. Загрузка/применение в тестовую базу: `db-load-xml` → `db-update -Dynamic on`.
4. Публикация: `_store\extensions` — create-only, имя `<Имя>_v<X.Y.Z>.cfe`, бронь `current.json`.
5. Проверка: `1c-check-task` (preflight + запуск, `-Deep` — применимость и версия в базе).

Правила версий: `<Version>` в `Configuration.xml` = суффикс CFE; каждая сборка — инкремент.
Префиксы расширений в базе уникальны; на метод — не более одного `&Вместо`.

## Запуск операций (без ожидания оболочки)

**Основной способ — MCP-сервер `cc`** (stdio, зарегистрирован в `opencode.jsonc`):

| Инструмент | Назначение |
|---|---|
| `run_start(script, args?, cwd?)` | detached-запуск `.py` из `skills`; сразу `run_id/pid/out` |
| `run_status(run_id)` | `state` (`run|done|fail|stale`), exit, длительность, последняя строка |
| `run_tail(run_id, offset?)` | новые байты `out.log` с offset (стриминг) |
| `run_wait(run_id, timeout_sec?)` | ожидание завершения (ограниченное) |
| `run_kill(run_id)` / `run_list(limit?)` | прерывание / список запусков |

Замеры (задача ~3 с): отклик direct 3.07 s → async_run 0.22 s → **MCP 0.15 s**;
стоимость опроса: CLI `async_run status` ~207 мс против **MCP ~7 мс**.

**Fallback без MCP:** `python skills\_shared\async_run.py start -- python "<скрипт>" ...`
(+ `status/tail/list/wait`), данные те же.

**Монитор для человека:** `python skills\_shared\cc-status.py` — живой дашборд
(секции «В ПРОЦЕССЕ»/«ЗАВЕРШЁННЫЕ», прогресс по медиане, лог выбранной операции).

## Инструменты процесса

- `1c-init` — новый проект/расширение: свободная база, `.v8-project.json`, заготовка;
  `-Adopt` — подключить существующий проект к стору (ничего не удаляет).
- `1c-check-task` — preflight + запуск клиента в согласованной базе.
- `cc-status.py` — наблюдение за всеми запусками (в т.ч. других сессий).

## Технические правила

- Файлы — UTF-8; PowerShell/консоль портят кириллицу — предпочитать Python.
- Пароли в выводе маскируются (`-Password ***`); учётные данные — только в `.v8-project.json`.
- Долгие операции не ждать синхронно: `run_start` → `run_tail/run_status`.
- `LoadConfigFromFiles`/`UpdateDBCfg` требуют свободы от Конфигуратора; фоновые задания
  могут давать «Ошибку исключительной блокировки» — повторить позже.
