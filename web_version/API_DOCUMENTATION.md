# API to-то booking.dop29.ru — Документация (по результатам записи)

> **Источник:** перехват реального трафика SPA (ExtJS/Inlearno) через расширение Navigator API Capturer
> **Дата записи:** 2026-08-27 (вторая сессия: 88 эндпоинтов / 365 запросов; первая: 49 эндпоинтов / 222 запроса)
> **Базовый URL:** `https://booking.dop29.ru`
> **Формат ответов:** обёртка `{ "data": ..., "err_code": 0, "success": true }` для всех REST-эндпоинтов.

> **Что добавлено во второй записи (08-27(1).json):** мутирующие операции над заявками
> (`POST /api/approveRequest`, `POST /api/cancelRequest`, `PUT /api/rest/order/{id}`), перевод детей
> из группы в группу (`POST /api/edu-history/kids/transfer`, `GET /api/transfer/groups/get/{id}`),
> создание/обновление групп и расписания (`POST /api/rest/eventGroups`, `PUT /api/rest/eventGroups/{id}`,
> `POST /api/rest/eventGroupSchedule`), предметы группы, система/справочники портала
> (`/api/config`, `/api/getDepartments`, `/api/getRegionGroups`, `/api/getPartnerSubordination`,
> помещения/виды спорта) и 18 новых словарей.

---

## Оглавление

1. [Авторизация](#авторизация)
2. [Справочники (dictionaries)](#справочники)
3. [Общие REST-ресурсы](#общие-rest-ресурсы)
4. [Программы/мероприятия (Events)](#программы-events)
5. [Группы (EventGroups)](#группы-eventgroups)
6. [Заявки (Orders)](#заявки-orders)
7. [Посещаемость (Attendance)](#посещаемость-attendance)
8. [Организации (Partners)](#организации-partners)
9. [Дети/Пользователи (Kids/SiteUser)](#дети-и-пользователи)
10. [Соц-услуги (Social service)](#социальные-услуги)
11. [ПФДОД / биллинг](#пфдод-биллинг)
12. [Сводная таблица полей](#краткая-сводка-по-моделям)

---

## Авторизация

### `POST /api/user/login`
Логин/пароль, возвращает JWT токены и профиль + права доступа.

**Запрос (JSON body):**
```json
{ "email": "kirill.bagrow@yandex.ru", "password": "***" }
```

**Заголовки:** `Content-Type: application/json`, `X-Requested-With: XMLHttpRequest`

**Ответ `200`:**
```json
{
  "data": {
    "user": {
      "id": "2722",
      "email": "...",
      "name": "Багров Кирилл Юрьевич",
      "group_id": "5",
      "group_name": "Педагоги",
      "group_code": "teacher",
      "is_deleted": false,
      "last_authorize_ts": "2026-08-27 10:00:11",
      "created_ts": "2020-11-02 10:59:27",
      "partner_id": "4",
      "municipality_id": "0",
      "teacher_id": "36f538a9-...-6e26b9c4f23c",
      "department_id": null,
      "is_password_outdated": false
    },
    "perms": {
      "EventCreate": true, "EventUpdate": true, "EventViewList": true,
      "PartnerViewList": true, "AttendanceGroups": true, "SiteUserViewList": true,
      "OrdersView": true, "AttendanceJournalView": true, "AttendanceJournalEdit": true,
      "PfdodContractView": true, "TeachersProfile": true, "OrderMassMoveStudy": true,
      "PrintEnrollmentApplication": true, "ViewActivityOrders": true,
      "ViewActivityKids": true, "ViewActivitySiteUsers": true,
      "SportTypesBookingView": true, "OrdersUpdate": true, "OrdersChangeStatus": true,
      "StudentsView": true, "MovementsReestrView": true, "MovementsReestrEdit": true,
      "MovementsReestrDeduction": true, "CreateActivityOrders": true, "TeacherGroup": true,
      "..." : "..."
    },
    "access_token": "eyJ0eXAiOiJKV1Qi...",
    "refresh_token": "eyJ0eXAiOiJKV1Qi...",
    "expired_at": "2026-08-27 10:30:11"
  },
  "err_code": 0,
  "success": true
}
```

> **Важно:** все последующие запросы авторизуются заголовком
> `Authorization: Bearer <access_token>`. Дополнительно SPA шлёт `X-REQUEST-ID` (UUID) и `X-Requested-With: XMLHttpRequest`.

---

## Справочники

Базовый паттерн: `GET /api/getDictionary/{Name}` — возвращает список `data: [...]` без пагинации.

| Эндпоинт | Содержимое | Формат элемента |
|---|---|---|
| `GET /api/getDictionary/SpecialMunicipalityCodes` | спец-коды муниципалитетов | `[]` (пусто в примере) |
| `GET /api/getDictionary/eventGroupFinancingSource` | источники финансирования | `{id, name}` — 4 шт |
| `GET /api/getDictionary/eventGroupOffBudgetTypes` | типы внебюджета | `{id, name}` — 3 шт |
| `GET /api/getDictionary/navOrderCancelReason` | причины отмены заявки | `{id, name, comment}` — 36 шт |
| `GET /api/getDictionary/navProgramType` | типы программ | `{id, name}` — 3 шт |
| `GET /api/getDictionary/requestStatesGrid` | статусы заявок с цветом | `{id, name, color}` — 6 шт |
| `GET /api/getDictionary/partnerType` | типы организаций (партнёров) | `{id, name}` — 11 шт |
| `GET /api/getDictionary/navStatus` | статусы программы/мероприятия | `{id, name, color}` — 6 шт |
| `GET /api/getDictionary/navSignificantProject` | значимые проекты (Кванториум и т.п.) | `{id, name}` — 8 шт |
| `GET /api/getDictionary/EventLevelsDict` | уровни программы | `{id: initial/basic/advanced, name}` — 3 шт |
| `GET /api/getDictionary/programTypeForDisabled` | типы программы для ОВЗ | `{id, name}` — 2 шт |
| `GET /api/getDictionary/programTypeFull` | полные типы программы | `{id, name}` — 15 шт |
| `GET /api/getDictionary/educationFormV2` | формы обучения (Очная/Заочная/Очно-заочная и комбинации) | `{id: FORM.MOD, name}` — >20 шт |
| `GET /api/getDictionary/eventDomainDict` | домен мероприятия | `{id: education/tourism, name}` — 2 шт |
| `GET /api/getDictionary/eventGroupType` | тип группы | `{id: 1/2, name: Группа/Класс}` |
| `GET /api/getDictionary/eventGroupBudgetTypes` | типы бюджета | `{id: 1..3, name: Федеральный/Региональный/Местный}` |
| `GET /api/getDictionary/eventGroupRestrictionHistoryTypes` | типы истории ограничений записи | `{id, name}` — 8 шт |
| `GET /api/getDictionary/navPfdodDiseases` | заболевания для ПФДОД (ОВЗ) | `{id, name}` — 10 шт |
| `GET /api/getDictionary/intalentTagsV2` | теги intalent (профнаправленности) | `{id, name, type: kas/pd, index}` — >26 шт |
| `GET /api/getDictionary/NokoEventExaminationStatuses` | статусы экспертизы НОКО | `{id, name}` — 4 шт |
| `GET /api/getDictionary/sportStages` | этапы спортивной подготовки | `{id, name, short_name, code}` — 5 шт |
| `GET /api/getDictionary/socialServiceCustomerCategory` | категории получателей соц-услуг | `{id: ***/Y*N/... , name}` — 6 шт |
| `GET /api/getDictionary/socialServiceEducationForm` | формы обучения соц-услуг (как educationFormV2) | `{id: FORM.MOD, name}` — >20 шт |
| `GET /api/getDictionary/socialServiceProgramTypeForDisabled` | тип программы соц-услуг для ОВЗ | `{id: 0..2, name}` |

**`requestStatesGrid`** (статусы заявок, используются по всему приложению):
```json
[
  { "id": "initial", "name": "Черновик",        "color": "ffd54f" },
  { "id": "pause",   "name": "Пауза",           "color": "ffb74d" },
  { "id": "approve", "name": "Подтверждена",    "color": "dce775" },
  { "id": "cancel",  "name": "Отменена",        "color": "e0e0e0" },
  { "id": "study",   "name": "Зачислен",        "color": "a5d6a7" },
  { "id": "deduct",  "name": "Отчислен",        "color": "a0a0a0" }
]
```

**`eventGroupFinancingSource`** (источники финансирования):
```json
[ { "id": 1, "name": "Бюджет" }, { "id": 2, "name": "Внебюджет" },
  { "id": 3, "name": "Совместно бюд.средств" }, { "id": 4, "name": "Грант" } ]
```

**`navProgramType`** (типы программ):
```json
[ { "id": 1, "name": "Предпрофессиональная" },
  { "id": 2, "name": "Общеразвивающая" },
  { "id": 3, "name": "Специальная программа" } ]
```

**`eventGroupOffBudgetTypes`** (типы внебюджета):
```json
[ { "id": 1, "name": "Платные образовательные услуги" },
  { "id": 2, "name": "Сертификат" }, { "id": 3, "name": "Грант" } ]
```

**Прочие общие эндпоинты вне REST:**

| Эндпоинт | Назначение | Возвращает |
|---|---|---|
| `GET /api/getMunicipality/?all=1&format=mini` | список муниципалитетов | `{id, name, sort, kids_count, fias, okato, oktmo, location_type}` — 26 шт |
| `GET /api/getRegions` | список регионов РФ | `{id, name, importance, group_id}` — 90 шт |
| `GET /api/getRegionProfile/` | профиль региона/портала | широкий набор полей (см. ниже) |
| `GET /api/modules/get` | список модулей меню | `{name, alias, package, privilege, group, sort, is_sencha, is_react, ...}` — 37 шт |
| `GET /api/getModuleBadges/` | бейджи модулей | `{alias, badge}` (напр. `{"alias":"activity_order","badge":"99+"}`) |

**Системные/служебные (добавлено во второй записи):**

| Эндпоинт | Назначение | Возвращает |
|---|---|---|
| `GET /api/config` | конфигурация портала (JS-«статика`) | `var Config = { pageTitle, hostname, mainSite, sentryDns, yandexCounter, captchaSiteKey, currentAcademicYear, portalTitle, plugins{...}, ... }`. Полезно: `currentAcademicYear` — текущий учебный год |
| `GET /api/getDepartments?page=&start=&length=` | ведомства (органы власти сфер) | `{id, name, short_name}` — 7 шт |
| `GET /api/getRegionGroups?page=&start=&length=` | группы регионов (федеральные округа) | `{id, name}` — 8 шт (`id:-1` = «Все регионы») |
| `GET /api/getPartnerSubordination?page=&start=&length=` | подчинённость организации | `{id, name}` — 4 шт (Субъект РФ/Муниципальное/Частное/Федеральное) |
| `GET /api/nokoGetEventFile/?extFilters=[{"property":"event_id","value":<id>,"comparison":"eq"}]` | файлы экспертизы НОКО по программе | `{id, name, ...}` (в примере пусто) |

**Другие REST-ресурсы (добавлено во второй записи):**

| Эндпоинт | Назначение | Возвращает |
|---|---|---|
| `GET /api/rest/inventoryObject?format=mini&page=&start=&length=` | инвентарные объекты (помещения/кабинеты) | `{id, name, partner_id, group_name, group_id, partner_name, municipality_id, is_deleted}` |
| `GET /api/rest/sport-types?all=1&sort=...` | виды спорта (классификатор) | `{id, name, parent_id, code, kind_id, is_base, is_olympic, is_5fk, ...}` — большая таблица |
| `GET /api/rest/sport-types` | типы спортивной подготовки | `{id, name}` |
| `GET /api/rest/eventGroupSubjects?extFilters=[{"property":"group_id","value":<id>,"exactMatch":true}]` | предметы группы (для КТП) | `data: [...]` (в примере пусто) |

---

## Общие REST-ресурсы

Все ресурсы живут под `GET /api/rest/{resource}` и поддерживают пагинацию через query-параметры:

- `page` — номер страницы
- `start` — сдвиг,
- `length` — размер страницы,
- `_dc` — кэш-бастер (ExtJS, игнорировать),
- `sort` — JSON `[{"property":"id","direction":"DESC"}]`,
- `extFilters` — JSON-массив фильтров:
  ```json
  [ { "property": "is_deleted", "value": false, "comparison": "eq", "type": "boolean" } ]
  ```
- `format=mini` — сокращённый формат справочника (для комбобоксов),
- `all=1` / `id=<csv>` — вернуть по конкретным id.

**Список ресурсов, зафиксированных в записи:**
`sections`, `academicYear`, `partners`, `eventGroups`, `events`, `order`, `kid`, `siteuser`, `pfdodContract`, `event_images`, `event_comments`, `eventratingdetails`, `inventoryExpert`, `municipalityRegions`, `event-partners`, `significant-regional-projects`, `edu-history/{id}`, `eventGroupSchedule`, `event-group-restriction-history`, `eventGroupSchedule`.

---

## Программы / Events

### `GET /api/rest/events` — список программ
Список с фильтрами и рейтингом. Ключевые поля записи:
```
id, name, is_locked, is_deleted, is_ovz, is_invalid_adapted,
age_from, age_to, levels, level_set, comments, active_order_kids,
domain, count_group_places, partner_name, partner_type, preview_url, points,
education_form, education_form_v2, ovz_diseases,
significant_regional_project_ids,
rating, rating_i, rating_n, rating_l, rating_e,
rating_estimation_count, rating_site_user_estimation_count,
examination_status, examination_updated, examination_finished, has_files,
department_id, subordination_id, length, length_unit, period_start,
min_persons, max_persons, date, date_changed, date_state, pfdod_date,
image_id, creator_id, partner_id, state, card
```

### `GET /api/rest/events/{id}` — одна программа (детально)
Пример `events/11410` / `events/20811`. Полный набор полей записи:
```
state, level_set, id, min_persons, max_persons, name, announce,
date, date_changed, length, length_unit, period_start, image_id,
age_from, age_to, location, is_deleted, creator_id, partner_id, date_state,
card, comments, section_id, sub_section_id, municipality_id,
program_type, sport_program_type, full_name, is_locked, is_ovz,
location_type, is_pfdod, pfdod_user_id, pfdod_date, is_invalid_adapted,
significant_project, education_form, program_type_for_disabled,
notification, is_olympic_branch, program_type_full, domain,
education_means, is_home_based, address_id, preview_url,
cost_per_hour, ovz_diseases, rating, rating_i
```

### Сопутствующие
| Эндпоинт | Назначение |
|---|---|
| `GET /api/rest/event_images?expand=["event"]&extFilters=[{"property":"event_id","value":<id>,"comparison":"eq"}]` | изображения программы — `{id, url, original, little, big, event_id}` |
| `GET /api/rest/event_comments?extFilters=[{"property":"event_id","value":<id>}]` | комментарии — `{id, created_ts, text, author_id, partner_id, event_id, author, partner, type}` |
| `GET /api/events/states/get?extFilters=[{"property":"event_id","value":<id>}]` | доступные статусы — `{name, id, possible}` |
| `GET /api/rest/eventratingdetails?extFilters=[{"property":"event_id","value":<id>,"comparison":"eq"}]` | детали рейтинга — `{id, event_id, key, points, date, text}` |
| `GET /api/social-service/event-services/get/{id}` | соц-услуги программы (пусто в примере) |

---

## Группы / EventGroups

### `GET /api/rest/eventGroups` — список групп программы
```json
extFilters: [ {"property":"event_id","value":11410},
              {"property":"is_deleted","value":"0","comparison":"eq"} ]
```
Поля: `id, name, is_deleted, teacher, size, age_to, age_from, is_locked, type, year, event_id, financing_sources, partner_id, is_pfdod, cost_hour_manual, experts, count_academic_hours, municipality_id, municipality_region_id`

### `GET /api/rest/eventGroups/{id}` — одна группа (расширенный набор)
Пример `eventGroups/59979`, `eventGroups/70011`:
```
id, type, event_id, name, teacher, age_to, age_from, size_min, size,
is_pfdod, hours_year, cost_hour_manual, date_start, date_end, is_locked,
order_from, order_to, is_locked_next_year,
available_next_year_order_from, available_next_year_order_to, is_deleted,
year, date_created, sport_stage_id, sport_training_year,
entrance_exams_enabled, is_event_address, address,
municipality_id, municipality_region_id, max_qty_orders, max_qty_enrolls,
order_enroll_date_created, address_id, partner_id, financing_sources,
available_order_current_year, available_order_next_year, schedule,
schedule_copy_prev_available, schedule_exists, experts,
teachers_update_type, teachers_update_disabled, teachers_update_comment,
hours_year_scheduled, entrance_exams_description, entrance_exams_links,
entrance_exams_files, locked_external_user_name
```

> `financing_sources`: `[{"id","group_id","financing_source","financing_cost","budget_type_id","offbudget_type_id"}]`
> `experts`: массив UUID экспертов (id преподавателя).
> `schedule`: массив объектов расписания (в примере `[]`).

### Сопутствующие
| Эндпоинт | Назначение |
|---|---|
| `GET /api/rest/eventGroupSchedule?extFilters=[{"property":"group_id","value":<id>},{"property":"academic_year_id","value":<year>}]` | расписание группы |
| `GET /api/rest/event-group-restriction-history?extFilters=[{"property":"event_group_id","value":<id>,"comparison":"eq"}]` | история ограничений |
| `GET /api/event-group-lessons/get?group_id=<id>&month=YYYY-MM` | занятия группы за месяц — `{id, group_id, date, theme, description, types[], experts[], times{time_start,duration,duration_length,breaks[],schedule_id}, active}` |
| `GET /api/event/group/stat/get?year=<yr>&id=<gid>` | статистика группы — `{initial, approve, study, id}` |

---

## Заявки / Orders

### `GET /api/rest/order` — список заявок
```json
extFilters: [ {"property":"fact_academic_year_id","value":"2026","comparison":"eq"} ]
```
Возвращает список заявок (в примере 0 элементов, но структура — как у одиночной).

### `GET /api/rest/order/{id}` — заявка детально (пример `order/1489768`)
```
state, id, academic_year_id, event_id, group_id, site_user_id, kid_id,
state_reason, created_ts, certificate_id, state_reason_comment,
fact_academic_year_id, comment, partner_id, fact_group_id, source,
entry_exams_invite, entry_exams_invite_comment, date_enroll, date_deduct,
actual_financing_source, offbudget_type, cancel_reasons, kid_is_approved,
kid_fio, kid_birthday, kid_age, user_fio, user_phone, user_email,
source_user_name, kid_certificate_municipality_id,
academic_year, fact_academic_year, is_online_payments_allowed,
congratulatory_certificate, movements_reestrs, is_new_contract_available,
user_passport_check_enabled, user_municipality_id, user_municipality_name,
municipality_id, municipality_name, entrance_exams_enabled, locked_external_user_name
```

### Сопутствующие
| Эндпоинт | Назначение |
|---|---|
| `GET /api/getRequestStates?extFilters=[{"property":"id","value":<order_id>}]` | доступные статусы заявки — `{name, id}` (напр. `{"name":"Отменена","id":"cancel"}`) |
| `GET /api/rest/pfdodContract?extFilters=[{"property":"order_id","value":<order_id>,"comparison":"eq"}]` | договоры ПФДОД по заявке |
| `GET /api/rest/edu-history/{kid_id}` | история обучения ребёнка — `{id, order_id, kid_id, group_id, group_id_to, academic_year_id, academic_year_id_to, type, financing_source, date_signing, decree_number, date_start, date_created, kid_fio, decree_info, group_name, group_name_to}` |

---

## Посещаемость / Attendance

| Эндпоинт | Назначение |
|---|---|
| `GET /api/attendance/dates/get` | список дат занятий. Фильтры: `group_id`, `dateStart`, `dateEnd` (формат `YYYY-MM-DD HH:MM:SS`) |
| `GET /api/attendance/members/get` | список участников/посещаемости. Фильтры: `group_id`, `academic_year_id`, `dateStart`, `dateEnd` |

Оба принимают `extFilters` в стандартном JSON-виде. В примере вернули `[]` (нет данных за выбранные месяцы), но сигнатура подтверждена.

---

## Организации / Partners

### `GET /api/rest/partners?id=4` и `GET /api/rest/partners/4`
Полные реквизиты организации:
```
id, name, public_name, legal_form, legal_address, legal_postal_code,
actual_address, actual_postal_code, phone, fax, site, email,
calculated_account, correspondent_account, bank_name, bank_address,
INN, KPP, OKPO, OGRN, OKVED, BIK, geo_id, image_id, has_vat,
responsible, notify_mobile, okato, oktmo, okopf, KBK,
legal_address_region/area/city/street/house/block/structure/id,
actual_address_id, city, logo, editor_id, legal_entity_id, refid,
is_deleted, created_ts, municipality_id, department_id, subordination_id
```

### `GET /api/rest/event-partners` / `event-partners/{id}`
Модуль-связанные организации: `{id, public_name, municipality_id, municipality_name, legal_address, allowed_program_types, is_deleted}`

---

## Дети и пользователи

### `GET /api/rest/kid?format=mini&all=1&id=<csv-uuids>`
Пакетное получение детей по id (CSV): `{id, first_name, last_name, site_user_id, is_approved, fio, parent_fio, birthday, age, municipality_id, municipality_name}`

### `GET /api/rest/siteuser?id=<id>`
Данные пользователя сайта: `{id, first_name, last_name, patro_name, email, phone, date_registration, date_last_login, is_verified, is_deleted, municipality_id, is_parent, is_resident, no_kids_limit, address_region/area/address/zip, sex, creator_id, summary, fio, kids_limit, is_deleted_pdp, is_accepted_consent_pdp, municipality_name, bounce_message, bounce_reason, is_large_family, ...user_can_get/insert/update/delete_identity_docs, ...user_can_get/insert/update/delete_kid_confirmation_docs}`

### `GET /api/rest/inventoryExpert?id=<teacher_id>&format=mini`
Эксперты/педагоги: `{id, fio, birthday, partner}`

---

## Социальные услуги

| Эндпоинт | Назначение |
|---|---|
| `GET /api/social-service/directory/sections/list` | разделы соц-услуг — `{id, code, title, full_title}` (7 шт) |
| `GET /api/social-service/event-services/get/{event_id}` | услуги мероприятия (пусто в примере) |

---

## ПФДОД / биллинг

### `POST /api/pfdod/billing/check/event/certificate/kid/{kid_id}?eventId=<event_id>`
Проверка сертификата ребёнка для мероприятия. Ответ содержит данные сертификата:
```
id, unit, amount, denomination, category_name, municipality, kid_id,
birthday, type, is_being_funded, is_used, is_cancelled, number, variant,
category_id, date_start, date_end, created, is_deleted,
last_name, first_name, patro_name, amount_withdraw,
signed_by_user_id, signed_at
```

---

## Краткая сводка по моделям

### Прочие справочники (секции/разделы)
- `GET /api/rest/sections` — дерево направленностей/разделов. Поля:
  `{id, parent_id, page_title, title, code, sort_order, is_deleted, significant, published_events_count, full_title, leaf}`.
  Корневые направленности (parent_id=0): Социально-гуманитарная (164), Естественнонаучная (165), Художественная (166), Физкультурно-спортивная (170), Туристско-краеведческая (172), Техническая (173).
  Вложенные элементы имеют `full_title = "<Родитель> / <Раздел>"` и `leaf: true`.
- `GET /api/rest/academicYear` — учебные года: `{id, year_from, year_to, state}` (напр. `2026`).
- `GET /api/rest/municipalityRegions?format=mini` — районы муниципалитетов: `{id, name, municipality_id, municipality_name}`.
- `GET /api/rest/significant-regional-projects` — значимые региональные проекты: `{id, name, is_public, is_deleted}`.

---

---

## Запись изменений (эндпоинты для внесения данных)

> Эти эндпоинты обнаружены в исходном коде приложения («Помойка», `application.py`) и не были
> зафиксированы пассивной записью трафика (SPA их не вызывал в ходе кликания). Это **пишущие**
> операции — требуют `Authorization: Bearer <token>` и, как правило, POST с JSON-телом.

### Типы занятий (для КТП)
```
Практическая работа — 9732
Учебное             — 7198
Дистанционное       — 3022
```

---

### `POST /api/attendance/save` — простановка посещаемости (закрытие дня)

Для каждого ребёнка группы отправляется отдельный запрос.

**Тело (на ребёнка):**
```json
{ "date": "2026-08-27", "group_id": "70011", "kid_id": "<uuid>", "value": true }
```
- `value`: `true` / `false` — присутствовал / отсутствовал.
- Отправка одним POST на каждого ребёнка (в коде — цикл).

**Заголовки:** `Content-Type: application/json` (+ стандартные).

---

### `POST /api/event-group-lessons/upsert` — заполнение занятия (КТП)

Создание/обновление записи занятия группы.

**Тело:**
```json
{
  "data": {
    "date": "2026-08-27 00:00:00",
    "group_id": "70011",
    "theme": "Тема занятия",
    "types": ["9732"],
    "description": "Описание"
  }
}
```
- `types` — массив строк-идентификаторов типа занятия (см. выше: `9732`, `7198`, `3022`).
- `date` — в формате `YYYY-MM-DD 00:00:00`.

---

### `POST /api/rest/order` — создание заявки в группу

**Тело (`data` — заявка):**
```json
{
  "data": {
    "event_id": "<id программы>",
    "state": "initial",
    "certificate_number": "нет",
    "decree_enrollment_number": "нет",
    "decree_deduction_number": "нет",
    "program_is_pfdod": false,
    "kid_is_approved": false,
    "is_online_payments_allowed": false,
    "academic_year_id": "2026",
    "certificate_certificate_number": "",
    "rpgu_deadline_date": null,
    "kid_birthday": null,
    "deadline": null,
    "created_ts": null,
    "date_enroll": null,
    "date_deduct": null,
    "rpgu_overdue_deadline": false,
    "group_id": "70011",
    "kid_id": "<uuid ребёнка>",
    "site_user_id": "<uuid родителя>"
  }
}
```
- Создаётся заявка со статусом `initial` (Черновик) в конкретную группу программы.
- Ответ: `{ "err_code": 0, ... }` при успехе; при ошибке `{ "err_code": <code>, "errors": [{ "msg": "..." }] }`.

---

### `POST /api/rest/activityOrder` — зачисление на мероприятие

**Тело:**
```json
{
  "data": {
    "activity_id": "<id мероприятия>",
    "date": "2026-08-27",
    "site_user_id": "<uuid родителя>",
    "kid_id": "<uuid ребёнка>",
    "state": "approve"
  }
}
```
- `state` по умолчанию `"approve"` (сразу подтверждённая).

---

### `POST /api/studyRequest` — принять на обучение (зачислить)

Перевод заявки из статуса `approve` (Подтверждена) в `study` (Зачислен) с оформлением приказа.

**Тело:**
```json
{
  "data": {
    "comment": "",
    "date_signing": "ГГ-ММ-ДД",
    "date_start": "ГГ-ММ-ДД",
    "decree_number": "<номер приказа>",
    "financing_source": "1",
    "id": "<id заявки>"
  }
}
```
- `financing_source`: `"1"` = Бюджет (см. `eventGroupFinancingSource`).
- `id` — id заявки в статусе `approve`.

---

### `GET /api/rest/safe/kid` — поиск детей по ФИО
Используется перед созданием заявки, чтобы найти ребёнка по ФИО.
```json
extFilters: [ {"property":"fio","value":"<Фамилия Имя Отчество>","comparison":"manual","type":null} ]
```
Параметры: `special=1`, `page/start/length`. Ответ содержит элементы с полями `id`, `fio`, `birthday`, `approve_org_caption`, `site_user_id`.

---

### `POST /api/approveRequest` — подтвердить/одобрить заявку (вторая запись)
Переводит заявку в статус `approve` (Подтверждена). Отправлено SPA при нажатии «Подтвердить».

**Тело:**
```json
{ "data": { "id": "1501739", "comment": "", "entry_exams": false, "send_to_rpgu": true } }
```
- `send_to_rpgu` — флаг отправки в РПГУ (Госуслуги).
- Ответ: `{ "data": [], "err_code": 0, "success": true }`.

---

### `POST /api/cancelRequest` — отменить заявку (вторая запись)
Переводит заявку в статус `cancel` (Отменена) с указанием причин.

**Тело:**
```json
{
  "data": {
    "id": "1498695",
    "reasons": [ { "id": 1, "comment": "<текст причины>" } ]
  }
}
```
- `reasons[].id` — id причины из словаря `navOrderCancelReason`.
- Ответ: `{ "data": [], "err_code": 0, "success": true }`.

---

### `PUT /api/rest/order/{id}` — обновление заявки (вторая запись)
Частичное обновление полей заявки (например комментарий).

**Тело:**
```json
{ "data": { "id": "1501739", "group_id": "70254", "comment": "Отправить смс с расписанием" } }
```
Ответ — полный объект заявки (см. `GET /api/rest/order/{id}`).

---

### `GET /api/transfer/groups/get/{group_id}` — группы для перевода (вторая запись)
Список групп, в которые можно перевести детей из указанной группы (для диалога перевода).

**Параметры:** `page`, `start`, `length`.
**Ответ:** `data: [ {id, name, program_name}, ... ]` — все «принимающие» группы.

---

### `POST /api/edu-history/kids/transfer` — перевод детей из группы в группу (вторая запись)
Массовый перевод детей (заявок) из одной группы в другую с оформлением приказа.

**Тело (плоское, без `data`):**
```json
{
  "group_id_to": "71112",          // целевая группа
  "group_id": "62127",             // исходная группа
  "financing_source": "1",
  "academic_year_id": 2026,
  "decree_number": "418 ",
  "date_signing": "2026-05-29 00:00:00",
  "date_start": "2026-09-01 00:00:00",
  "kid_ids": ["<uuid>", ...],
  "orders": ["1287389", ...]       // id переводимых заявок
}
```
**Ответ:** `{ "data": { "order_1287389": [], "order_1278837": [], ... }, "err_code": 0, "success": true }`.

---

### `POST /api/rest/eventGroups` — создание группы (вторая запись)
Создаёт новую группу в программе. **Тело** (`data` — объект группы):

```json
{
  "data": {
    "event_id": 20950, "partner_id": "4", "municipality_id": "1",
    "type": 1, "name": "Группа 1", "teacher": "Фамилия Имя Отчество",
    "age_from": 10, "age_to": 17,
    "hours_year": 144, "size_min": 10, "size": 30,
    "date_start": "2026-09-01 00:00:00", "date_end": "2027-05-30 00:00:00",
    "is_locked": true, "is_locked_next_year": true, "is_pfdod": false,
    "financing_sources": [ { "financing_source": 1, "budget_type_id": 2, "offbudget_type_id": null, "tariff_id": null } ],
    "order_info": { "initial": 0, "approve": 0, "study": 0 },
    "entrance_exams_files": [], "breaks": [], "schedule": [], "subjects": [], "sport_subtypes": [],
    "partner_subordination_id": 0, "is_event_address": true, "address": ""
  }
}
```
Ответ — созданная группа (поля как у `GET /api/rest/eventGroups/{id}`).

### `PUT /api/rest/eventGroups/{id}` — обновление группы (вторая запись)
Частичное обновление полей группы. **Тело:** `{ "data": { "id": "71113", "sport_subtypes": [], ... } }`.
Ответ — обновлённый объект группы.

---

### `POST /api/rest/eventGroupSchedule` — создание расписания группы (вторая запись)
Создаёт запись расписания (КТП) по неделям.

**Тело:**
```json
{ "data": {
    "group_id": "71112",
    "schedule_type": "BY_WEEK",
    "week_days": [1, 3],
    "dates": [],
    "time_start": "2008-01-01 10:00:00",
    "time_end": null,
    "duration": 2, "duration_length": 45,
    "period_from": "2026-09-01 00:00:00",
    "period_to": "2027-05-30 00:00:00",
    "breaks": [10]
} }
```
- `schedule_type: BY_WEEK` + `week_days` (1=Пн … 7=Вс), `breaks` — минуты перерыва.
- Ответ — созданный объект расписания (`{id, group_id, schedule_type, week_days, time_start, time_end, duration, duration_length, period_from, period_to, academic_year_id, ...}`).
- Для обновления расписания — `PUT /api/rest/eventGroupSchedule/{id}` (по аналогии).

---

## Сводка мутирующих эндпоинтов

| Метод | URL | Назначение |
|---|---|---|
| POST | `/api/attendance/save` | проставить посещаемость ребёнка за дату |
| POST | `/api/event-group-lessons/upsert` | создать/обновить занятие (КТП) |
| POST | `/api/rest/order` | создать заявку в группу (статус `initial`) |
| PUT | `/api/rest/order/{id}` | обновить заявку (комментарий и пр.) |
| POST | `/api/rest/activityOrder` | зачислить на мероприятие (статус `approve`) |
| POST | `/api/approveRequest` | подтвердить заявку → `approve` |
| POST | `/api/cancelRequest` | отменить заявку → `cancel` (с причинами) |
| POST | `/api/studyRequest` | принять на обучение (`approve` → `study`, приказ) |
| POST | `/api/edu-history/kids/transfer` | массовый перевод детей между группами (приказ) |
| POST | `/api/rest/eventGroups` | создать группу |
| PUT | `/api/rest/eventGroups/{id}` | обновить группу |
| POST | `/api/rest/eventGroupSchedule` | создать расписание группы (КТП) |

---

## Общие договорённости

1. **Обёртка ответа:** `{ "data": <object|array>, "err_code": 0, "success": true }`. `err_code != 0` — ошибка.
2. **Авторизация:** `Authorization: Bearer <access_token>` (получается из `/api/user/login`).
3. **Пагинация:** `page`, `start`, `length` (стандарт ExtJS Grid).
4. **Фильтры:** query-параметр `extFilters` = URL-encoded JSON-массив `[{property, value, comparison, type}]`.
5. **Сокращённый формат:** `format=mini` для справочных комбобоксов.
6. **Кэш:** параметр `_dc` — timestamp, можно игнорировать/менять произвольно.
7. **Идентификаторы:** у детей и пользователей UUID (`kid_id`, `site_user_id`, `teacher_id`); у организаций, программ, групп, заявок — числовые.
