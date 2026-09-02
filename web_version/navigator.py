"""API клиент к booking.dop29.ru (Inlearno/ExtJS).

Все методы возвращают распарсенный JSON (dict). Роуты в app.py кэшируют
результаты и ловят исключения. Методы с префиксом get_* — чтение,
с префиксом save_* / create_* / accept_* — запись (изменение данных).
"""

import json
import time
import uuid
import requests

BASE = "https://booking.dop29.ru"


class NavigatorError(Exception):
    """Ошибка API (err_code != 0) или сетевой сбой."""


class NavigatorClient:
    def __init__(self, email, password, year="2026", enroll_year=None):
        self.email = email
        self.password = password
        self.year = year
        self.enroll_year = enroll_year or year
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.expired_at = None
        self.user = None
        self.headers = {}
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        )
        self._cache = {}

    def _cached(self, key, ttl, builder):
        """Кэш с TTL для медленных read-методов (API отвечает ~5 c на запрос)."""
        now = time.time()
        hit = self._cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
        value = builder()
        self._cache[key] = (now, value)
        return value

    def _invalidate(self, *prefixes):
        """Сброс кэша по префиксам ключей после операций записи.
        Без аргументов — сбрасывается весь кэш клиента."""
        if not prefixes:
            self._cache = {}
            return
        self._cache = {
            k: v for k, v in self._cache.items()
            if not any(k.startswith(p) for p in prefixes)
        }

    # ------------------------------------------------------------------ auth
    def login(self):
        """Авторизация, возвращает профиль пользователя или бросает NavigatorError."""
        url = BASE + "/api/user/login"
        payload = {"email": self.email, "password": self.password}
        r = self.session.post(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "*/*",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": BASE,
                "Referer": BASE + "/admin/",
            },
            data=json.dumps(payload),
            timeout=30,
        )
        b = self._check(r)
        data = b["data"]
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self.expired_at = data.get("expired_at")
        self.user = data.get("user", {})

        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Authorization": "Bearer " + (self.access_token or ""),
            "X-REQUEST-ID": str(uuid.uuid4()),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": BASE + "/admin/",
        }
        return self.user

    # ------------------------------------------------------------------ core
    def _get(self, path, params=None, silent=False):
        url = path if path.startswith("http") else BASE + path
        r = self.session.get(url, headers=self.headers, params=params, timeout=45)
        return self._check(r, silent=silent)

    def _post(self, path, payload, params=None):
        url = path if path.startswith("http") else BASE + path
        r = self.session.post(
            url, headers=self.headers, json=payload, params=params, timeout=60
        )
        return self._check(r)

    def _put(self, path, payload, params=None):
        url = path if path.startswith("http") else BASE + path
        r = self.session.put(
            url, headers=self.headers, json=payload, params=params, timeout=60
        )
        return self._check(r)

    def _delete(self, path, payload, params=None):
        url = path if path.startswith("http") else BASE + path
        r = self.session.delete(
            url, headers=self.headers, json=payload, params=params, timeout=60
        )
        return self._check(r)

    @staticmethod
    def _check(r, silent=False):
        try:
            b = r.json()
        except Exception:
            b = {}
        if "err_code" not in b:
            raise NavigatorError(f"Некорректный ответ ({r.status_code})")
        if b.get("err_code") != 0 or not b.get("success", True):
            msg = ""
            errs = b.get("errors") or []
            if errs:
                msg = errs[0].get("msg", "") if isinstance(errs[0], dict) else str(errs[0])
            if silent:
                return b
            raise NavigatorError(msg or f"Ошибка API (err_code={b.get('err_code')})")
        return b

    @staticmethod
    def _data(b):
        return b.get("data")

    # ------------------------------------------------------------------ программы и группы
    def get_programs(self):
        """Список программ (мероприятий) с фильтром не-удалённых."""
        def build():
            filters = json.dumps(
                [{"type": "boolean", "property": "is_deleted", "value": False, "comparison": "eq"}],
                ensure_ascii=True,
            )
            b = self._get(
                "/api/rest/events",
                {
                    "page": 1,
                    "start": 0,
                    "length": 500,
                    "extFilters": filters,
                },
            )
            return self._data(b)

        return self._cached("programs", 300, build)

    def get_program(self, event_id):
        def build():
            b = self._get(f"/api/rest/events/{event_id}")
            data = self._data(b)
            if isinstance(data, list) and data:
                return data[0]
            return data

        return self._cached(f"program:{event_id}", 300, build)

    def get_groups(self):
        """Все группы по всем программам (формат для посещаемости), с пагинацией.

        API отдаёт максимум 500 записей на страницу; цикл добирает остальные.
        """
        def build():
            filters = json.dumps(
                [
                    {"property": "is_deleted", "value": "0", "comparison": "eq"},
                    {"property": "event.is_deleted", "value": "N", "comparison": "eq"},
                ],
                ensure_ascii=True,
            )
            all_groups = []
            page = 1
            while True:
                b = self._get(
                    "/api/rest/eventGroups",
                    {
                        "_dc": int(time.time() * 1000),
                        "page": page,
                        "start": (page - 1) * 500,
                        "format": "attendance",
                        "length": 500,
                        "extFilters": filters,
                    },
                )
                chunk = self._data(b) or []
                all_groups.extend(chunk)
                if len(chunk) < 500:
                    break
                page += 1
            return all_groups

        return self._cached("groups", 300, build)

    def get_group(self, group_id):
        def build():
            b = self._get(f"/api/rest/eventGroups/{group_id}")
            data = self._data(b)
            if isinstance(data, list) and data:
                return data[0]
            return data

        return self._cached(f"group:{group_id}", 300, build)

    def get_group_schedule(self, group_id):
        def build():
            filters = json.dumps(
                [
                    {"property": "group_id", "value": str(group_id)},
                    {"property": "academic_year_id", "value": str(self.year)},
                ],
                ensure_ascii=True,
            )
            try:
                b = self._get(
                    "/api/rest/eventGroupSchedule",
                    {"page": 1, "start": 0, "length": 500, "extFilters": filters},
                    silent=True,
                )
                return self._data(b)
            except NavigatorError:
                return []

        return self._cached(f"schedule:{group_id}", 300, build)

    def create_group_schedule(self, group_id, data):
        """Создание расписания группы (BY_WEEK/DATES).

        POST /api/rest/eventGroupSchedule. data — dict с полями
        {schedule_type, week_days, dates, time_start, time_end, duration,
         duration_length, period_from, period_to, breaks}.
        """
        payload = {"data": dict(data or {})}
        payload["data"]["group_id"] = str(group_id)
        b = self._post("/api/rest/eventGroupSchedule", payload)
        self._refresh_schedule(group_id)
        return self._data(b)

    def update_group_schedule(self, schedule_id, group_id, data):
        """Обновление расписания группы по id. PUT /api/rest/eventGroupSchedule/{id}."""
        payload = {"data": dict(data or {})}
        payload["data"]["id"] = str(schedule_id)
        b = self._put(f"/api/rest/eventGroupSchedule/{schedule_id}", payload)
        self._refresh_schedule(group_id)
        return self._data(b)

    def delete_group_schedule(self, schedule_id, group_id):
        """Удаление расписания группы по id. DELETE /api/rest/eventGroupSchedule/{id}."""
        b = self._delete(
            f"/api/rest/eventGroupSchedule/{schedule_id}",
            {"data": {"id": str(schedule_id)}},
        )
        self._refresh_schedule(group_id)
        return self._data(b)

    def copy_prev_schedule(self, group_id):
        """Копирование расписания из прошлого года. POST /api/event/schedule/copyPrev."""
        b = self._post(
            "/api/event/schedule/copyPrev", {"data": {"group_id": str(group_id)}}
        )
        self._refresh_schedule(group_id)
        return self._data(b)

    def _refresh_schedule(self, group_id):
        """Сброс кэша расписания и детального объекта группы после записи."""
        self._invalidate(f"schedule:{group_id}", f"group:{group_id}")

    def update_group(self, group_id, data):
        """Обновление группы: переименование и/или поля периода/приёма заявок.

        PUT /api/rest/eventGroups/{id}. data — поля группы для обновления
        (name, date_start, date_end, order_from, order_to и т.п.).
        Отправляем переданные поля вместе с сохранённым id.
        """
        payload = {"data": dict(data or {})}
        payload["data"]["id"] = str(group_id)
        b = self._put(f"/api/rest/eventGroups/{group_id}", payload)
        self._invalidate(f"group:{group_id}")
        return self._data(b)

    # ------------------------------------------------------------------ посещаемость (дети)
    def get_members(self, group_id, month=None):
        """Обучающиеся в группе (активные). month: 'YYYY-MM' — вернёт диапазон дат.

        ВАЖНО: length=25 обязателен — только так в записях появляются
        поля посещаемости по дням вида ``e2026_3_14`` (значения: 1 — посетил,
        2 — нет, 3 — болел). С length>25 эти поля не приходят.
        """
        def build():
            if month:
                date_start, date_end = self._month_range(month)
            else:
                date_start = f"{self.year}-01-01 00:00:00"
                date_end = f"{self.year}-12-31 23:59:59"

            filters = json.dumps(
                [
                    {"property": "group_id", "value": str(group_id)},
                    {"property": "academic_year_id", "value": self.year},
                    {"property": "dateStart", "value": date_start},
                    {"property": "dateEnd", "value": date_end},
                ],
                ensure_ascii=True,
            )
            b = self._get(
                "/api/attendance/members/get",
                {"_dc": int(time.time() * 1000), "page": 1, "start": 0, "length": 25, "extFilters": filters},
            )
            items = self._data(b) or []
            return items

        return self._cached(f"members:{group_id}:{month}:{self.year}", 300, build)

    @staticmethod
    def attendance_field_key(date_str, year):
        """Ключ поля посещаемости a<YYYY>_<M>_<D> (без ведущих нулей) для даты.

        Реальное имя поля — с префиксом ``a`` (attendance), напр. ``a2026_4_25``,
        где YYYY — календарный год даты (не учебный год группы).
        """
        # date_str: 'YYYY-MM-DD' или 'YYYY-MM-DD HH:MM:SS'
        d = (date_str or "")[:10].split("-")
        if len(d) != 3:
            return None
        y, m, day = d
        return f"a{y}_{int(m)}_{int(day)}"

    def get_academic_years(self):
        """Список учебных годов для переключателя в навбаре."""
        def build():
            try:
                b = self._get("/api/rest/academicYear", {"page": 1, "start": 0, "length": 50})
                return self._data(b) or []
            except NavigatorError:
                return []

        return self._cached("academic_years", 600, build)

    @staticmethod
    def _month_range(month):
        m = month.split("-")
        year, mon = int(m[0]), int(m[1])
        if mon == 12:
            n_year, n_mon = year + 1, 1
        else:
            n_year, n_mon = year, mon + 1
        return (
            f"{year:04d}-{mon:02d}-01 00:00:00",
            f"{n_year:04d}-{n_mon:02d}-01 00:00:00",
        )

    def get_dates(self, group_id, month=None):
        """Даты занятий группы."""
        def build():
            if month:
                date_start, date_end = self._month_range(month)
            else:
                date_start = f"{self.year}-01-01 00:00:00"
                date_end = f"{self.year}-12-31 23:59:59"

            filters = json.dumps(
                [
                    {"property": "group_id", "value": str(group_id)},
                    {"property": "dateStart", "value": date_start},
                    {"property": "dateEnd", "value": date_end},
                ],
                ensure_ascii=True,
            )
            b = self._get(
                "/api/attendance/dates/get",
                {"_dc": int(time.time() * 1000), "page": 1, "start": 0, "length": 500, "extFilters": filters},
            )
            return self._data(b) or []

        return self._cached(f"dates:{group_id}:{month}:{self.year}", 300, build)

    def save_attendance(self, date, group_id, kid_id, value):
        """Проставить посещаемость ребёнка за дату.

        value: 1 — посетил, 2 — нет, 3 — болел (или bool True/False).
        """
        payload = {"date": date, "group_id": str(group_id), "kid_id": kid_id, "value": value}
        b = self._post("/api/attendance/save", payload)
        self._invalidate(f"members:{group_id}", f"dates:{group_id}")
        return self._data(b)

    # ------------------------------------------------------------------ КТП (занятия)
    def get_lessons(self, group_id, month=None):
        """Занятия (КТП) группы за месяц."""
        if month is None:
            month = time.strftime("%Y-%m")

        def build():
            b = self._get(
                "/api/event-group-lessons/get",
                {
                    "_dc": int(time.time() * 1000),
                    "group_id": str(group_id),
                    "month": month,
                    "page": 1,
                    "start": 0,
                    "length": 500,
                },
            )
            return self._data(b) or []

        return self._cached(f"lessons:{group_id}:{month}", 300, build)

    def save_lesson(self, date, group_id, theme, types, description=""):
        """Создание/обновление занятия (КТП). types — список строк вида ['9732']."""
        payload = {
            "data": {
                "date": f"{date} 00:00:00",
                "group_id": str(group_id),
                "theme": theme,
                "types": [str(t) for t in (types or [])],
                "description": description,
            }
        }
        b = self._post("/api/event-group-lessons/upsert", payload)
        self._invalidate(f"lessons:{group_id}")
        return self._data(b)

    def get_event_group_subjects(self, group_id):
        """Предметы группы (для списка типов занятий КТП).

        GET /api/rest/eventGroupSubjects по ``group_id``. Если группа не
        ведёт предметы или вернулся пустой ответ — [].
        """
        def build():
            filters = json.dumps(
                [{"property": "group_id", "value": str(group_id), "exactMatch": True}],
                ensure_ascii=True,
            )
            try:
                b = self._get(
                    "/api/rest/eventGroupSubjects",
                    {"extFilters": filters, "page": 1, "start": 0, "length": 500},
                    silent=True,
                )
                return self._data(b) or []
            except NavigatorError:
                return []

        return self._cached(f"subjects:{group_id}", 300, build)

    # ------------------------------------------------------------------ заявки
    def get_orders(self, academic_year=None, state=None, event_id=None, group_id=None, length=500):
        """Заявки. state — список (в виде list) или строка."""
        def build():
            filters = []
            filters.append({"property": "fact_academic_year_id", "value": str(academic_year or self.year), "comparison": "eq"})
            if event_id:
                filters.append({"property": "event_id", "value": str(event_id), "comparison": "eq"})
            if group_id:
                filters.append({"property": "fact_group_id", "value": str(group_id), "comparison": "eq"})
            if state:
                if isinstance(state, (list, tuple)):
                    filters.append({"property": "state", "value": list(state), "comparison": "in"})
                else:
                    filters.append({"property": "state", "value": state, "comparison": "eq"})

            b = self._get(
                "/api/rest/order",
                {
                    "_dc": int(time.time() * 1000),
                    "page": 1,
                    "start": 0,
                    "length": length,
                    "pagination": "arrows",
                    "extFilters": json.dumps(filters, ensure_ascii=True),
                },
            )
            return self._data(b) or []

        # ключ должен содержать РЕЗОЛЬВИРОВАННЫЙ год (academic_year или self.year),
        # иначе разные годы коллизируют в один кэш-ключ при academic_year=None
        key = f"orders:{academic_year or self.year}:{event_id}:{group_id}:{state}:{length}"
        return self._cached(key, 120, build)

    def get_order_counts_by_group(self, states=("initial", "approve"), year=None):
        """Число заявок по статусам в разрезе групп за год набора.

        Возвращает {group_id(str): {state: n, ...}}. Заявки качаются единым
        списком по всем группам (пагинация по 500) и агрегируются здесь,
        чтобы не делать по запросу на каждую из ~800 групп.

        Счёт идёт за self.enroll_year (год набора), а не за self.year (год,
        под которым смотрят посещаемость): новые/принятые заявки относятся к
        году набора (часто следующему за годом посещаемости). Если year задан
        явно — используется он.
        """
        yr = str(year or self.enroll_year)
        def build():
            counts = {}
            all_o = []
            page = 1
            while True:
                filters = json.dumps(
                    [
                        {"property": "state", "value": list(states), "comparison": "in"},
                        {"property": "fact_academic_year_id", "value": yr, "comparison": "eq"},
                    ],
                    ensure_ascii=True,
                )
                b = self._get(
                    "/api/rest/order",
                    {
                        "_dc": int(time.time() * 1000),
                        "page": page,
                        "start": (page - 1) * 500,
                        "length": 500,
                        "pagination": "arrows",
                        "extFilters": filters,
                    },
                )
                data = self._data(b) or []
                all_o.extend(data)
                if len(data) < 500:
                    break
                page += 1
            for o in all_o:
                gid = str(o.get("fact_group_id") or "").strip()
                st = o.get("state")
                if not gid:
                    continue
                if gid not in counts:
                    counts[gid] = {}
                counts[gid][st] = counts[gid].get(st, 0) + 1
            return counts

        return self._cached(f"order_counts_by_group:{yr}:{tuple(states)}", 120, build)

    def get_group_order_stats(self, group_ids, year=None):
        """Счётчики заявок по группам одним батч-запросом.

        Вызывает /api/event/group/stat/get списком id групп (пачками до 150).
        Возвращает {group_id(str): {"initial": n, "approve": n, "study": n}},
        где:
          initial — новых заявок,
          approve — принятых,
          study   — уже зачисленных (обучаются).
        Счёт за year (= self.enroll_year по умолчанию), а не за self.year.
        """
        yr = str(year or self.enroll_year)
        ids = sorted({str(x) for x in group_ids if x not in (None, "")})
        def build():
            result = {}
            chunk = 150
            for i in range(0, len(ids), chunk):
                part = ids[i:i + chunk]
                filters = json.dumps([], ensure_ascii=True)
                b = self._get(
                    "/api/event/group/stat/get",
                    {
                        "_dc": int(time.time() * 1000),
                        "id": ",".join(part),
                        "year": yr,
                        "page": 1,
                        "start": 0,
                        "length": len(part) + 1,
                        "extFilters": filters,
                    },
                )
                for d in self._data(b) or []:
                    gid = str(d.get("id"))
                    if gid:
                        result[gid] = {
                            "initial": int(d.get("initial") or 0),
                            "approve": int(d.get("approve") or 0),
                            "study": int(d.get("study") or 0),
                        }
            return result

        return self._cached(f"group_stat:{yr}:{','.join(ids)}", 120, build)

    def get_max_persons_by_event(self):
        """event_id(str) -> max_persons (max учеников в группе по настройкам программы)."""
        def build():
            mapping = {}
            try:
                programs = self.get_programs() or []
            except NavigatorError:
                programs = []
            for p in programs:
                eid = str(p.get("id"))
                if not eid:
                    continue
                try:
                    detail = self.get_program(eid)
                except NavigatorError:
                    continue
                mp = detail.get("max_persons") if isinstance(detail, dict) else None
                mapping[eid] = mp
            return mapping

        return self._cached("max_persons_by_event", 600, build)


    def get_order(self, order_id):
        b = self._get(f"/api/rest/order/{order_id}")
        data = self._data(b)
        if isinstance(data, list) and data:
            return data[0]
        return data

    def get_site_user(self, site_user_id):
        """Полные контакты родителя (email, phone — БЕЗ маски) и ФИО.

        GET /api/rest/siteuser?id={site_user_id}
        """
        def build():
            if not site_user_id:
                return {}
            b = self._get("/api/rest/siteuser", {"id": str(site_user_id)}, silent=True)
            data = self._data(b)
            if isinstance(data, list) and data:
                return data[0]
            return data if isinstance(data, dict) else {}
        return self._cached(f"siteuser:{site_user_id}", 600, build)

    def get_order_states(self, order_id):
        """Доступные состояния для заявки."""
        filters = json.dumps([{"property": "id", "value": str(order_id)}], ensure_ascii=True)
        try:
            b = self._get("/api/getRequestStates", {"page": 1, "start": 0, "length": 25, "extFilters": filters})
            return self._data(b) or []
        except NavigatorError:
            return []

    def create_order(self, event_id, group_id, kid_id, site_user_id, state="initial"):
        """Создать заявку в группу."""
        payload = {
            "data": {
                "event_id": str(event_id),
                "state": state,
                "certificate_number": "нет",
                "decree_enrollment_number": "нет",
                "decree_deduction_number": "нет",
                "program_is_pfdod": False,
                "kid_is_approved": False,
                "is_online_payments_allowed": False,
                "academic_year_id": str(self.year),
                "certificate_certificate_number": "",
                "rpgu_deadline_date": None,
                "kid_birthday": None,
                "deadline": None,
                "created_ts": None,
                "date_enroll": None,
                "date_deduct": None,
                "rpgu_overdue_deadline": False,
                "group_id": str(group_id),
                "kid_id": str(kid_id),
                "site_user_id": str(site_user_id),
            }
        }
        b = self._post("/api/rest/order?_dc=" + str(int(time.time() * 1000)), payload)
        self._invalidate("orders:")
        return self._data(b)

    def accept_to_study(self, order_id, date_signing, date_start, decree_number, financing_source="1", comment=""):
        """Принять на обучение (approve -> study)."""
        payload = {
            "data": {
                "comment": comment,
                "date_signing": date_signing,
                "date_start": date_start,
                "decree_number": decree_number,
                "financing_source": str(financing_source),
                "id": str(order_id),
            }
        }
        b = self._post("/api/studyRequest", payload)
        self._invalidate("orders:")
        return self._data(b)

    def approve_order(self, order_id, comment="", send_to_rpgu=True):
        """Подтвердить заявку (статус initial -> approve).

        POST /api/approveRequest.
        """
        payload = {
            "data": {
                "id": str(order_id),
                "comment": comment,
                "entry_exams": False,
                "send_to_rpgu": bool(send_to_rpgu),
            }
        }
        b = self._post("/api/approveRequest", payload)
        self._invalidate("orders:")
        return self._data(b)

    def cancel_order(self, order_id, reason_id, comment=""):
        """Отменить заявку (в cancel) с указанием причины из navOrderCancelReason.

        POST /api/cancelRequest.
        """
        payload = {
            "data": {
                "id": str(order_id),
                "reasons": [{"id": int(reason_id), "comment": comment or ""}],
            }
        }
        b = self._post("/api/cancelRequest", payload)
        self._invalidate("orders:")
        return self._data(b)

    # ------------------------------------------------------------------ справочники
    def get_dictionary(self, name, params=None):
        """Универсальный словарь: GET /api/getDictionary/{name} -> list.

        Кэшируется и не падает при ошибке (вернёт []).
        """
        def build():
            filters = {"page": 1, "start": 0, "length": 500}
            if params:
                filters.update(params)
            try:
                b = self._get(f"/api/getDictionary/{name}", filters, silent=True)
                return self._data(b) or []
            except NavigatorError:
                return []

        return self._cached(f"dict:{name}", 600, build)

    def get_cancel_reasons(self, state="initial"):
        """Причины отмены заявки (словарь navOrderCancelReason), фильтр по статусу."""
        def build():
            filters = json.dumps(
                [{"property": "status", "value": state, "comparison": "eq"}],
                ensure_ascii=True,
            )
            try:
                b = self._get(
                    "/api/getDictionary/navOrderCancelReason",
                    {"page": 1, "start": 0, "length": 500, "extFilters": filters},
                    silent=True,
                )
                return self._data(b) or []
            except NavigatorError:
                return []

        return self._cached(f"cancel_reasons:{state}", 600, build)

    def get_status_dictionary(self):
        """Статусы заявок с цветами."""
        def build():
            try:
                b = self._get("/api/getDictionary/requestStatesGrid")
                return self._data(b) or []
            except NavigatorError:
                return []

        return self._cached("status_dict", 300, build)

    def search_kid(self, fio):
        """Поиск ребёнка по ФИО."""
        def build():
            filters = json.dumps(
                [{"property": "fio", "value": fio, "comparison": "manual", "type": None}],
                ensure_ascii=True,
            )
            b = self._get(
                "/api/rest/safe/kid",
                {"_dc": int(time.time() * 1000), "special": 1, "page": 1, "start": 0, "length": 20, "extFilters": filters},
            )
            return self._data(b) or []

        return self._cached(f"kid:{fio}", 120, build)
