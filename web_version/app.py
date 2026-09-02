"""Navigator API Capturer Web — лёгкий веб интерфейс (MVP) к booking.dop29.ru."""

import functools
import os
import json
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    g,
)

from navigator import NavigatorClient, NavigatorError

app = Flask(__name__)
app.config["SECRET_KEY"] = "nav-web-mvp-secret-key"  # меняется на проде
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# Серверный кэш клиентов: sid -> NavigatorClient
_clients = {}


@app.after_request
def _no_cache(resp):
    # интерфейс живой — не даём браузеру кэшировать устаревшие HTML/CSS,
    # иначе после правок пользователь видит «пустые» ячейки
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


def get_client():
    """Клиент текущей сессии (с авторизацией, если ещё нет)."""
    sid = session.get("sid")
    if sid and sid in _clients:
        c = _clients[sid]
        if not c.access_token:
            raise NavigatorError("Нет доступа")
        return c
    raise NavigatorError("Не авторизован")


LOGIN_INI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "login.ini")


def _load_enroll_year():
    """Год набора (счётчики новых/принятых заявок) из 4-й строки login.ini.

    Независим от года посещаемости (self.year): заявки на зачисление в
    следующем году регистрируются под годом набора. Если в файле нет 4-й
    строки — вернёт None, и будет использован текущий год входа.
    """
    try:
        with open(LOGIN_INI, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) >= 4:
            return lines[3]
    except OSError:
        pass
    return None


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("sid") or session["sid"] not in _clients:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def safe(fn):
    """Обёртка, превращающая NavigatorError в flash + редирект на главную."""
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except NavigatorError as e:
            flash(str(e), "error")
            return redirect(url_for("index"))
    return wrapped


def enrich_groups(client, groups):
    """Дополняет каждый объект группы счётчиками заявок и макс. учеников.

    Ставит атрибуты:
      _initial  — новых заявок (статус initial),
      _approve  — принятых (статус approve),
      _enrolled — уже зачисленных (статус study / обучаются),
      _max      — max учеников в группе (max_persons программы).
    При ошибке получения данных атрибуты остаются None — страница не падает.
    """
    stats_ok = False
    try:
        stats = client.get_group_order_stats([g.get("id") for g in groups])
        stats_ok = True
    except Exception:
        stats = {}
    try:
        max_by_event = client.get_max_persons_by_event()
    except Exception:
        max_by_event = {}
    for g in groups:
        gid = str(g.get("id"))
        if stats_ok:
            c = stats.get(gid, {}) or {}
            # у группы без заявок это 0, а не «нет данных»
            g["_initial"] = c.get("initial", 0)
            g["_approve"] = c.get("approve", 0)
            g["_enrolled"] = c.get("study", 0)
        else:
            g["_initial"] = None
            g["_approve"] = None
            g["_enrolled"] = None
        g["_max"] = (max_by_event or {}).get(str(g.get("event_id")))


# ------------------------------------------------------------------ авторизация
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        year = (request.form.get("year") or "2026").strip()
        if not email or not password:
            flash("Укажите логин и пароль", "error")
            return render_template("login.html")
        enroll_year = _load_enroll_year() or year
        client = NavigatorClient(email, password, year, enroll_year=enroll_year)
        try:
            user = client.login()
        except NavigatorError as e:
            flash(f"Ошибка входа: {e}", "error")
            return render_template("login.html")

        sid = session.pop("_new_sid", None)
        try:
            import secrets
            sid = sid or secrets.token_hex(16)
        except Exception:
            sid = sid or email
        _clients[sid] = client
        session["sid"] = sid
        session["email"] = email
        session["user_name"] = (user or {}).get("name", email)
        flash("Вы вошли в систему", "ok")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    sid = session.pop("sid", None)
    _clients.pop(sid, None)
    session.clear()
    return redirect(url_for("login"))


@app.context_processor
def inject_globals():
    return {
        "current_user": session.get("user_name", ""),
        "current_year": _client_year(),
        "academic_years": _academic_years(),
    }


def _client_year():
    sid = session.get("sid")
    c = _clients.get(sid)
    return c.year if c else "2026"


def _academic_years():
    try:
        c = get_client()
        return c.get_academic_years()
    except NavigatorError:
        return []


@app.route("/set_year", methods=["POST"])
@login_required
def set_year():
    """Сменить учебный год текущей сессии и сбросить кэш клиента."""
    year = (request.form.get("year") or "").strip()
    sid = session.get("sid")
    c = _clients.get(sid)
    if not c:
        return jsonify({"ok": False, "error": "не авторизован"}), 401
    if not year:
        return jsonify({"ok": False, "error": "нет года"}), 400
    c.year = year
    c._invalidate()
    return jsonify({"ok": True, "year": year})


# ------------------------------------------------------------------ главная
@app.route("/")
@login_required
@safe
def index():
    client = get_client()
    groups = client.get_groups()
    programs = client.get_programs()

    # группировка групп по программам
    by_program = {}  # program_id -> {program: ..., groups: [...]}
    for g in groups:
        pid = str(g.get("event_id"))
        if pid not in by_program:
            prog = next((p for p in programs if str(p.get("id")) == pid), None)
            by_program[pid] = {"id": pid, "program": prog, "groups": []}
        by_program[pid]["groups"].append(g)

    enrich_groups(client, groups)

    return render_template(
        "index.html",
        groups=groups,
        programs=programs,
        by_program=by_program,
        selected_group=request.args.get("group"),
    )


# ------------------------------------------------------------------ посещаемость (выбор группы)
@app.route("/attendance")
@login_required
@safe
def attendance():
    client = get_client()
    groups = client.get_groups()
    programs = client.get_programs()
    by_program = {}
    for g in groups:
        pid = str(g.get("event_id"))
        if pid not in by_program:
            prog = next((p for p in programs if str(p.get("id")) == pid), None)
            by_program[pid] = {"id": pid, "program": prog, "groups": []}
        by_program[pid]["groups"].append(g)
    enrich_groups(client, groups)
    return render_template("attendance.html", groups=groups, by_program=by_program)


# ------------------------------------------------------------------ страница группы
@app.route("/group/<int:group_id>")
@login_required
@safe
def group_page(group_id):
    client = get_client()
    group = client.get_group(group_id)
    tab = request.args.get("tab", "attendance")
    month = request.args.get("month", "") or time_now("%Y-%m")

    # заявки показываем под годом набора (enroll_year), а не под годом
    # посещаемости: новые/принятые заявки регистрируются на год набора
    orders = client.get_orders(group_id=group_id, academic_year=client.enroll_year)

    members = []
    dates = []
    lessons = []
    schedule = []
    attendance_matrix = []

    if tab == "attendance" or not tab:
        members = client.get_members(group_id, month)
        dates = client.get_dates(group_id, month)
        attendance_matrix = build_attendance_matrix(client, members, dates, month)
    elif tab == "ktp":
        lessons = client.get_lessons(group_id, month)
    elif tab == "schedule":
        # расписание берём из детального объекта группы (поле ``schedule``),
        # т.к. сам endpoint eventGroupSchedule в этом захвате отдал пусто
        schedule = group.get("schedule") or [] if isinstance(group, dict) else []

    # флаг доступности копирования расписания из прошлого года
    schedule_copy_prev_available = False
    schedule_exists = {}
    if isinstance(group, dict):
        schedule_copy_prev_available = bool(group.get("schedule_copy_prev_available"))
        schedule_exists = group.get("schedule_exists") or {}

    # словари для перевода кодов настроек группы/заявок в названия
    dictionaries = {
        "type": dict_map(client.get_dictionary("eventGroupType")),
        "financing_source": dict_map(client.get_dictionary("eventGroupFinancingSource")),
        "budget_type": dict_map(client.get_dictionary("eventGroupBudgetTypes")),
        "offbudget_type": dict_map(client.get_dictionary("eventGroupOffBudgetTypes")),
        "sport_stage": dict_map(client.get_dictionary("sportStages")),
    }
    cancel_reasons = client.get_cancel_reasons()
    subjects = client.get_event_group_subjects(group_id)

    all_states = client.get_status_dictionary()
    prev_month, next_month = month_nav(month)

    return render_template(
        "group.html",
        group=group,
        members=members,
        dates=dates,
        lessons=lessons,
        orders=orders,
        schedule=schedule,
        schedule_copy_prev_available=schedule_copy_prev_available,
        schedule_exists=schedule_exists,
        attendance_matrix=attendance_matrix,
        all_states=all_states,
        dictionaries=dictionaries,
        cancel_reasons=cancel_reasons,
        subjects=subjects,
        tab=tab,
        month=month,
        prev_month=prev_month,
        next_month=next_month,
        month_label=month_label(month),
    )


def time_now(fmt):
    import time
    return time.strftime(fmt)


def month_nav(month):
    """Вернуть (предыдущий, следующий) месяц вида 'YYYY-MM'."""
    y, m = int(month[:4]), int(month[5:7])
    pm = f"{y:04d}-{m-1:02d}" if m > 1 else f"{y-1:04d}-12"
    nm = f"{y:04d}-{m+1:02d}" if m < 12 else f"{y+1:04d}-01"
    return pm, nm


def month_label(month):
    names = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
             "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    try:
        return f"{names[int(month[5:7])]} {month[:4]}"
    except Exception:
        return month


def build_attendance_matrix(client, members, dates, month=None):
    """Сетка посещаемости: строки = дети, колонки = даты занятий.

    Колонки — объединение (по возрастанию):
      * дат занятий по расписанию (dates),
      * дат, на которые уже есть отметки посещаемости (a-поля в members).
    Так прошлые месяцы (где расписание пустое, но посещаемость велась) тоже
    показывают свои отметки, а будущие — пустые кликабельные колонки.

    Если передан ``month`` ('YYYY-MM'), колонки ограничиваются этим месяцем
    (поля a<YYYY>_<M>_<D> в members приходят сразу за весь учебный год —
    поэтому их нужно отфильтровать по выбранному месяцу).

    Для каждого ребёнка берём текущее значение из поля a<YYYY>_<M>_<D>
    (1 посетил, 2 нет, 3 болел).
    """
    import datetime
    year = client.year
    wd = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    # диапазон выбранного месяца (ограничиваем колонки месячной таблицей)
    month_prefix = None
    if month:
        month_prefix = month[:7]  # 'YYYY-MM'

    # собираем даты, на которые есть отметки, из a-полей всех детей
    e_dates = set()
    for m in members:
        for k, v in m.items():
            if v is not None and k.startswith("a"):
                # формат ключа: a<YYYY>_<M>_<D> (без ведущих нулей), напр. a2026_4_25
                try:
                    parts = k[1:].split("_")
                    if len(parts) != 3:
                        continue
                    yy, mm, dd = parts
                    e_dates.add(f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}")
                except Exception:
                    continue

    # объединяем расписание и фактические отметки, сортируем
    all_dates = set(
        (d.get("date") or "")[:10] for d in dates if (d.get("date") or "")[:10]
    )
    all_dates |= e_dates
    if month_prefix:
        all_dates = {d for d in all_dates if d[:7] == month_prefix}

    cols = []
    for date in sorted(all_dates):
        try:
            dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            weekday = wd[dt.weekday()]
            daynum = dt.day
        except Exception:
            weekday, daynum = "", ""
        key = client.attendance_field_key(date, year)
        cols.append({
            "date": date,
            "daynum": daynum,
            "weekday": weekday,
            "key": key,
            "recorded": key in e_dates,
        })

    rows = []
    for m in members:
        cells = []
        for c in cols:
            v = m.get(c["key"])
            # e-поле может вернуться как строка — нормализуем
            try:
                v = int(v) if v is not None else None
            except Exception:
                v = None
            cells.append({"date": c["date"], "key": c["key"], "value": v})
        rows.append({
            "kid_id": m.get("kid_id"),
            "name": f"{m.get('kid_last_name','')} {m.get('kid_first_name','')} {m.get('kid_patro_name','')}".strip(),
            "birthday": m.get("kid_birthday"),
            "age": m.get("kid_age"),
            "type_code": m.get("type_code"),
            "cells": cells,
        })
    return {"cols": cols, "rows": rows}


@app.route("/group/<int:group_id>/attendance", methods=["POST"])
@login_required
@safe
def attendance_cell(group_id):
    """AJAX: проставить статус посещаемости в ячейке сетки."""
    client = get_client()
    data = request.get_json(silent=True) or {}
    date = (data.get("date") or "")
    kid_id = (data.get("kid_id") or "")
    value = data.get("value")  # 1 посетил, 2 нет, 3 болел
    if not date or not kid_id:
        return jsonify({"ok": False, "error": "не хватает параметров"}), 400
    try:
        client.save_attendance(date, group_id, kid_id, int(value))
        return jsonify({"ok": True, "value": int(value)})
    except NavigatorError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/group/<int:group_id>/save_attendance", methods=["POST"])
@login_required
@safe
def save_attendance(group_id):
    client = get_client()
    date = (request.form.get("date") or "").strip()
    month = (request.form.get("month") or "").strip()
    kids = request.form.getlist("present[]")
    members = client.get_members(group_id, month or None)
    saved = 0
    errors = 0
    for m in members:
        kid_id = m.get("kid_id")
        if not kid_id:
            continue
        present = kit_id_in(kid_id, kids)
        try:
            client.save_attendance(date, group_id, kid_id, 1 if present else 2)
            saved += 1
        except Exception:
            errors += 1
    flash(f"Посещаемость за {date} сохранена: {saved} записей"
          + (f", ошибок: {errors}" if errors else ""), "ok" if not errors else "error")
    return redirect(url_for("group_page", group_id=group_id, tab="attendance", month=month))


def kit_id_in(kid_id, kids):
    return any(k == kid_id or k == str(kid_id) for k in kids)


@app.route("/group/<int:group_id>/save_lesson", methods=["POST"])
@login_required
@safe
def save_lesson(group_id):
    client = get_client()
    date = (request.form.get("lesson_date") or "").strip()
    theme = (request.form.get("theme") or "").strip()
    desc = (request.form.get("description") or "").strip()
    types = request.form.getlist("types")
    if not date or not theme:
        flash("Укажите дату и тему занятия", "error")
        return redirect(url_for("group_page", group_id=group_id, tab="ktp"))
    try:
        client.save_lesson(date, group_id, theme, types, desc)
        flash("Занятие (КТП) сохранено", "ok")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("group_page", group_id=group_id, tab="ktp"))


@app.route("/group/<int:group_id>/accept", methods=["POST"])
@login_required
@safe
def accept_order(group_id):
    """Принять конкретную заявку на обучение."""
    client = get_client()
    order_id = request.form.get("order_id")
    date_signing = (request.form.get("date_signing") or "").strip()
    date_start = (request.form.get("date_start") or "").strip()
    decree_number = (request.form.get("decree_number") or "").strip()
    if not order_id:
        flash("Не указана заявка", "error")
        return redirect(url_for("group_page", group_id=group_id))
    if not (date_signing and date_start and decree_number):
        flash("Нужны дата приказа, дата начала и номер приказа", "error")
        return redirect(url_for("group_page", group_id=group_id))
    try:
        client.accept_to_study(order_id, date_signing, date_start, decree_number)
        flash("Заявка принята на обучение", "ok")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("group_page", group_id=group_id))


@app.route("/group/<int:group_id>/schedule/create", methods=["POST"])
@login_required
def schedule_create(group_id):
    """Создание расписания группы (реально отправляет запрос после подтверждения в UI)."""
    client = get_client()
    try:
        data = (request.get_json(silent=True) or {}).get("data") or {}
        client.create_group_schedule(group_id, data)
        return {"ok": True}
    except NavigatorError as e:
        return {"ok": False, "error": str(e)}, 400
    except Exception as e:
        return {"ok": False, "error": str(e)}, 400


@app.route("/group/<int:group_id>/schedule/<int:schedule_id>/update", methods=["POST"])
@login_required
def schedule_update(group_id, schedule_id):
    """Обновление расписания группы (реально отправляет запрос после подтверждения в UI)."""
    client = get_client()
    try:
        data = (request.get_json(silent=True) or {}).get("data") or {}
        client.update_group_schedule(schedule_id, group_id, data)
        return {"ok": True}
    except NavigatorError as e:
        return {"ok": False, "error": str(e)}, 400
    except Exception as e:
        return {"ok": False, "error": str(e)}, 400


@app.route("/group/<int:group_id>/schedule/<int:schedule_id>/delete", methods=["POST"])
@login_required
def schedule_delete(group_id, schedule_id):
    """Удаление расписания группы (реально отправляет запрос после подтверждения в UI)."""
    client = get_client()
    try:
        client.delete_group_schedule(schedule_id, group_id)
        return {"ok": True}
    except NavigatorError as e:
        return {"ok": False, "error": str(e)}, 400
    except Exception as e:
        return {"ok": False, "error": str(e)}, 400


@app.route("/group/<int:group_id>/schedule/copy_prev", methods=["POST"])
@login_required
def schedule_copy_prev(group_id):
    """Копирование расписания из прошлого года (реально отправляет запрос после подтверждения в UI)."""
    client = get_client()
    try:
        client.copy_prev_schedule(group_id)
        return {"ok": True}
    except NavigatorError as e:
        return {"ok": False, "error": str(e)}, 400
    except Exception as e:
        return {"ok": False, "error": str(e)}, 400


@app.route("/group/<int:group_id>/update", methods=["POST"])
@login_required
def group_update(group_id):
    """Обновление группы (переименование и/или период обучения / даты приёма заявок).

    Реально отправляет запрос после подтверждения в UI (кнопки «Уверен»/«Отмена»).
    """
    client = get_client()
    try:
        data = (request.get_json(silent=True) or {}).get("data") or {}
        client.update_group(group_id, data)
        return {"ok": True}
    except NavigatorError as e:
        return {"ok": False, "error": str(e)}, 400
    except Exception as e:
        return {"ok": False, "error": str(e)}, 400


def dictionary_name(dictionary, key):
    """Название по id из словаря list[{id,name}] (id может быть str/int)."""
    if dictionary is None:
        return None
    if key in (None, ""):
        return None
    skey = str(key)
    for item in dictionary or []:
        if str(item.get("id")) == skey:
            return item.get("name")
    return None


def dict_map(lst):
    """list[{id,name}] -> {str(id): name} для удобного использования в шаблонах."""
    m = {}
    for item in lst or []:
        m[str(item.get("id"))] = item.get("name")
    return m


@app.route("/group/<int:group_id>/approve", methods=["POST"])
@login_required
@safe
def approve_order(group_id):
    """Подтвердить заявку (initial -> approve)."""
    client = get_client()
    order_id = request.form.get("order_id")
    if not order_id:
        flash("Не указана заявка", "error")
        return redirect(url_for("group_page", group_id=group_id, tab="orders"))
    try:
        client.approve_order(order_id)
        flash(f"Заявка #{order_id} подтверждена", "ok")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("group_page", group_id=group_id, tab="orders"))


@app.route("/group/<int:group_id>/cancel", methods=["POST"])
@login_required
@safe
def cancel_order(group_id):
    """Отменить заявку (в cancel) с выбором причины."""
    client = get_client()
    order_id = request.form.get("order_id")
    reason_id = request.form.get("reason_id")
    comment = (request.form.get("reason_comment") or "").strip()
    if not order_id or not reason_id:
        flash("Не указана заявка или причина отмены", "error")
        return redirect(url_for("group_page", group_id=group_id, tab="orders"))
    try:
        client.cancel_order(order_id, reason_id, comment)
        flash(f"Заявка #{order_id} отменена", "ok")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("group_page", group_id=group_id, tab="orders"))


# ------------------------------------------------------------------ программы
@app.route("/programs")
@login_required
@safe
def programs():
    client = get_client()
    programs = client.get_programs()
    return render_template("programs.html", programs=programs)


@app.route("/programs/<int:event_id>")
@login_required
@safe
def program_page(event_id):
    client = get_client()
    program = client.get_program(event_id)
    groups = client.get_groups()
    prog_groups = [g for g in groups if str(g.get("event_id")) == str(event_id)]
    return render_template("programs.html", programs=[program], focus=event_id, groups=prog_groups)


# ------------------------------------------------------------------ заявки
@app.route("/orders")
@login_required
@safe
def orders():
    client = get_client()
    state = request.args.get("state", "")

    if state:
        state = state.split(",") if "," in state else state
    kwargs = {}
    if state:
        kwargs["state"] = state

    # сколько заявок показывать (по умолчанию 100)
    try:
        limit = int(request.args.get("limit") or 100)
    except Exception:
        limit = 100
    limit = min(max(limit, 10), 500)

    # год заявок = год сессии (единый на всё приложение), меняется через
    # навбар ИЛИ через селект года на этой странице (оба идут через /set_year)
    orders = client.get_orders(length=limit, **kwargs)
    all_states = client.get_status_dictionary()

    return render_template(
        "orders.html",
        orders=orders,
        all_states=all_states,
        cur_state=request.args.get("state", ""),
        cur_year=_client_year(),
        cur_limit=limit,
        cancel_reasons=client.get_cancel_reasons("initial"),
    )


# ------------------------------------------------------------------ заявки: деталь и действия (JSON)
def _order_state_detail(order):
    return (order.get("state") or order.get("state_grid") or "").strip()


@app.route("/orders/<int:order_id>/detail")
@login_required
@safe
def order_detail(order_id):
    """Вся информация по заявке (JSON) для панели на странице заявок."""
    client = get_client()
    order = client.get_order(order_id)
    state = _order_state_detail(order)
    reasons = client.get_cancel_reasons(state) if state in ("initial", "approve") else client.get_cancel_reasons("initial")
    # полные контакты родителя (без маски) — отдельный запрос siteuser по site_user_id
    site_user = client.get_site_user(order.get("site_user_id"))
    return jsonify({"ok": True, "order": order, "state": state,
                    "cancel_reasons": reasons, "site_user": site_user})


@app.route("/orders/<int:order_id>/approve", methods=["POST"])
@login_required
@safe
def order_approve(order_id):
    client = get_client()
    try:
        client.approve_order(order_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
@safe
def order_cancel(order_id):
    client = get_client()
    reason_id = (request.form.get("reason_id") or "").strip()
    comment = (request.form.get("reason_comment") or "").strip()
    if not reason_id:
        return jsonify({"ok": False, "error": "Не выбрана причина отмены"}), 400
    try:
        client.cancel_order(order_id, reason_id, comment)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/orders/<int:order_id>/accept", methods=["POST"])
@login_required
@safe
def order_accept(order_id):
    client = get_client()
    date_signing = (request.form.get("date_signing") or "").strip()
    date_start = (request.form.get("date_start") or "").strip()
    decree_number = (request.form.get("decree_number") or "").strip()
    if not (date_signing and date_start and decree_number):
        return jsonify({"ok": False, "error": "Нужны дата приказа, дата начала и номер приказа"}), 400
    try:
        client.accept_to_study(order_id, date_signing, date_start, decree_number)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/group/<int:group_id>/contacts")
@login_required
@safe
def group_contacts(group_id):
    """Список заявок группы (все статусы) с полными контактами представителя
    (без маски, через siteuser) — для модалки 'Получить контакт. данные'.
    Клиент фильтрует по выбранным типам (чекбоксы)."""
    client = get_client()
    # заявки берём под годом набора (enroll_year), как и счётчики на главной —
    # заявки регистрируются под годом набора, а не годом посещаемости
    orders = client.get_orders(group_id=group_id, academic_year=client.enroll_year, length=500)
    items = []
    for o in orders:
        st = (o.get("state_grid") or o.get("state") or "").strip()
        if not st:
            continue
        su = client.get_site_user(o.get("site_user_id")) or {}
        kid_fio = o.get("kid_last_name", "") + " " + o.get("kid_first_name", "") + " " + o.get("kid_patro_name", "")
        kid_fio = " ".join(kid_fio.split())
        bd = (o.get("kid_birthday") or "")
        if bd:
            bd = str(bd)[:10]
        items.append({
            "id": o.get("id"),
            "state": st,
            "rep_fio": su.get("fio") or o.get("user_fio") or "",
            "phone": su.get("phone") or o.get("user_phone") or "",
            "email": su.get("email") or o.get("user_email") or "",
            "kid_fio": kid_fio or o.get("kid_fio") or "",
            "kid_birthday": bd,
            "kid_age": o.get("kid_age"),
        })
    return jsonify({"ok": True, "group_id": group_id, "count": len(items), "contacts": items})


# ------------------------------------------------------------------ быстрое действие: поиск ребёнка
@app.route("/search_kid")
@login_required
@safe
def search_kid():
    client = get_client()
    q = request.args.get("q", "")
    if not q:
        return jsonify([])
    return jsonify(client.search_kid(q))


# ------------------------------------------------------------------ функции (перенесено из pomoika.py)
def _kid_full(o):
    return " ".join(str(o.get(k) or "") for k in ("kid_last_name", "kid_first_name", "kid_patro_name")).strip()


@app.route("/group/<int:group_id>/members")
@login_required
@safe
def group_members(group_id):
    """Список активных обучающихся группы (чтение)."""
    client = get_client()
    members = client.get_members(group_id)
    rows = []
    for m in members:
        if int(m.get("type_active", 1)) != 1:
            continue
        rows.append({
            "id": m.get("kid_id"),
            "name": _kid_full(m) or m.get("kid_fio") or "",
            "birthday": (m.get("kid_birthday") or "")[:10],
            "age": m.get("kid_age"),
        })
    return jsonify({"ok": True, "group_id": group_id, "rows": rows})


@app.route("/group/<int:group_id>/order_preview", methods=["POST"])
@login_required
@safe
def order_preview(group_id):
    """ПРЕДПРОСМОТР (без отправки!) заявки на зачисление ребёнка в группу.

    Строит точный payload, который БЫЛ БЫ отправлен в /api/rest/order,
    и возвращает его — НИКАКОЙ запрос в навигатор не выполняется.
    """
    client = get_client()
    kid_id = (request.form.get("kid_id") or request.form.get("kid") or "").strip()
    site_user_id = (request.form.get("site_user_id") or "").strip()
    if not kid_id or not site_user_id:
        return jsonify({"ok": False, "error": "Выберите ребёнка (нужен id и site_user_id)"}), 400
    group = client.get_group(group_id)
    payload = {"data": {
        "event_id": group.get("event_id"),
        "state": "initial",
        "certificate_number": "нет",
        "decree_enrollment_number": "нет",
        "decree_deduction_number": "нет",
        "program_is_pfdod": False,
        "kid_is_approved": False,
        "is_online_payments_allowed": False,
        "academic_year_id": client.enroll_year or client.year,
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
    }}
    return jsonify({
        "ok": True,
        "endpoint": "POST /api/rest/order",
        "preview": payload,
        "note": "Запрос НЕ отправлен — только предпросмотр.",
    })


@app.route("/group/<int:group_id>/close_day_preview", methods=["POST"])
@login_required
@safe
def close_day_preview(group_id):
    """ПРЕДПРОСМОТР (без отправки!) «закрытия дня»: случайная посещаемость
    по всем активным детям + запись занятия (КТП). Ничего не отправляет."""
    import random as _r
    client = get_client()
    date = (request.form.get("date") or "").strip()
    theme = (request.form.get("theme") or "").strip()
    type_id = (request.form.get("type_id") or "").strip()
    description = (request.form.get("description") or "").strip()
    try:
        percent = int(request.form.get("percent") or "")
    except Exception:
        percent = 80
    if not date:
        return jsonify({"ok": False, "error": "Укажите дату"}), 400
    date_visit = date[:10]
    members = client.get_members(group_id)
    attendance = []
    _r.seed()
    for m in members:
        if int(m.get("type_active", 1)) != 1:
            continue
        visit = _r.randint(0, 99) < percent
        attendance.append({"date": date_visit, "group_id": str(group_id),
                           "kid_id": m.get("kid_id"), "value": visit})
    ktp_payload = {"data": {
        "date": date + " 00:00:00",
        "group_id": str(group_id),
        "theme": theme,
        "types": [str(type_id)] if type_id else [],
        "description": description,
    }}
    return jsonify({
        "ok": True,
        "attendance_endpoint": "POST /api/attendance/save",
        "attendance_total": len(attendance),
        "attendance_preview": attendance[:5],
        "ktp_endpoint": "POST /api/event-group-lessons/upsert",
        "ktp_preview": ktp_payload,
        "note": "Запрос НЕ отправлен — только предпросмотр.",
    })


@app.route("/api/reports")
@login_required
@safe
def api_reports():
    """Отчёты (только чтение, безопасно).

    kind: by_age | by_program | problem_groups | duplicates
    Все данные берутся из кэшированных (read-only) вызовов.
    """
    client = get_client()
    kind = request.args.get("kind", "by_age")
    groups = client.get_groups()

    # фильтр по выбранным группам (id через запятую)
    group_ids_param = request.args.get("group_ids", "")
    if group_ids_param:
        selected_ids = set(g.strip() for g in group_ids_param.split(",") if g.strip())
        if selected_ids:
            groups = [g for g in groups if str(g.get("id")) in selected_ids]

    gname = {str(g.get("id")): (g.get("program_name") or "") + " " + (g.get("name") or "")
             for g in groups}

    # один обход всех групп: считаем детей, возраста, программы, дубликаты
    per_group_size = {}
    ages = {}
    prog = {}
    kid_groups = {}

    if kind in ("by_age", "by_program", "duplicates"):
        for g in groups:
            gid = str(g.get("id"))
            pname = g.get("program_name") or f"Программа #{g.get('event_id')}"
            try:
                members = client.get_members(gid)
            except Exception:
                members = []
            prog.setdefault(pname, 0)
            for m in members:
                if int(m.get("type_active", 1)) != 1:
                    continue
                per_group_size[gid] = per_group_size.get(gid, 0) + 1
                a = m.get("kid_age")
                if a is not None:
                    ages[str(a)] = ages.get(str(a), 0) + 1
                prog[pname] += 1
                kid_id = str(m.get("kid_id")) if m.get("kid_id") is not None else None
                if kid_id:
                    kid_groups.setdefault(kid_id, set()).add(gid)

    if kind == "by_age":
        rows = [{"age": int(k), "count": v} for k, v in ages.items()]
        rows.sort(key=lambda r: r["age"])
        return jsonify({"ok": True, "kind": "by_age", "rows": rows,
                        "total": sum(ages.values())})

    if kind == "by_program":
        rows = [{"program": k, "count": v} for k, v in prog.items()]
        rows.sort(key=lambda r: r["count"], reverse=True)
        return jsonify({"ok": True, "kind": "by_program", "rows": rows,
                        "total": sum(prog.values())})

    if kind == "problem_groups":
        try:
            mn = int(request.args.get("min") or 0)
        except Exception:
            mn = 0
        # подсчитаем размер групп (для надёжности используем активных детей)
        for g in groups:
            gid = str(g.get("id"))
            if gid not in per_group_size:
                try:
                    members = client.get_members(gid)
                except Exception:
                    members = []
                per_group_size[gid] = sum(1 for m in members if int(m.get("type_active", 1)) == 1)
        rows = [{"program": g.get("program_name"), "name": g.get("name"),
                 "id": g.get("id"), "size": per_group_size.get(str(g.get("id")), 0)}
                for g in groups if per_group_size.get(str(g.get("id")), 0) < mn]
        rows.sort(key=lambda r: r["size"])
        return jsonify({"ok": True, "kind": "problem_groups", "rows": rows, "min": mn})

    if kind == "duplicates":
        # статусы для фильтрации (по умолчанию — все)
        statuses_param = request.args.get("statuses", "")
        allowed_statuses = set()
        if statuses_param:
            allowed_statuses = set(s.strip() for s in statuses_param.split(",") if s.strip())

        # собираем заявки по группам: kid_id -> {group_id: status}
        kid_groups = {}
        kid_names = {}
        for g in groups:
            gid = str(g.get("id"))
            try:
                orders = client.get_orders(group_id=gid, academic_year=client.enroll_year)
            except Exception:
                orders = []
            for o in orders:
                st = (o.get("state") or o.get("state_grid") or "").strip()
                if allowed_statuses and st not in allowed_statuses:
                    continue
                kid_id = str(o.get("kid_id")) if o.get("kid_id") is not None else None
                if not kid_id:
                    continue
                kid_groups.setdefault(kid_id, {})[gid] = st
                nm = _kid_full(o)
                if nm:
                    kid_names[kid_id] = nm

        rows = []
        for kid_id, gmap in kid_groups.items():
            if len(gmap) > 1:
                groups_info = []
                for gid in sorted(gmap.keys()):
                    groups_info.append({
                        "group": gname.get(gid, gid),
                        "status": gmap[gid]
                    })
                rows.append({
                    "name": kid_names.get(kid_id, kid_id),
                    "groups": groups_info,
                    "count": len(groups_info)
                })
        rows.sort(key=lambda r: r["count"], reverse=True)
        return jsonify({"ok": True, "kind": "duplicates", "rows": rows,
                        "total": len(rows)})

    return jsonify({"ok": False, "error": "Неизвестный вид отчёта"}), 400


if __name__ == "__main__":
    import webbrowser
    port = 5000
    webbrowser.open(f"http://127.0.0.1:{port}/login")
    app.run(debug=True, port=port)
