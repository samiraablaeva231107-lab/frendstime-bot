
import html
import json
import logging
import os
import random
import re
import sqlite3
from datetime import datetime
from contextlib import closing
from dataclasses import dataclass
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = "8621917534:AAFzt1OAkymb89KLDeIyndT_4BHFlHtVcdM"
ADMIN_IDS = {6200142729}
SUPERADMIN_IDS = {7673695956}    
REVIEW_CHAT_IDS = {-1003888708715}       
DB_NAME = os.path.join(os.path.dirname(__file__), "bot.db")
START_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "come_home_dating.jpg")

START_TEXT = (
    "Привет! 🍃\n"
    "На связи администрация FriendsTime. Рады приветствовать в рядах своих потенциальных участников :)\n\n"
    "Чтобы продолжить, выбери с помощью кнопки один из составов, к которому хочешь принадлежать:\n"
    "● МИРНЫЙ — состав, подразумевающий совместное времяпровождение с составом ВНЕ АРЕНЫ. "
    "Любые выходы на арену с тегом клана или без немедленно возбраняются и караются предупреждением; "
    "в случае повторного нарушения — баном.\n"
    "● БОЕВОЙ — состав, в котором доступен свободный выход на арену при наличии у Вас соответствующего "
    "опыта командной игры и нахождения в боевых кланах (!) и при соответствии выдвинутым критериям.\n\n"
    "По техническим неполадкам бота обращайся к @Xzqwxx\n"
    "Ждем твоей анкеты, друг!"
)

PROFILE_TEXT = (
    "Профиль — это отдельная карточка участника, не анкета вступления и не анкета знакомств.\n"
    "Здесь можно сохранить краткую информацию о себе для внутреннего использования."
)

SEARCH_HELP_TEXT = (
    "Поиск анкет для знакомств:\n\n"
    "1. <code>.знакомство @username</code> — показать анкету пользователя по юзу.\n"
    "2. <code>.знакомство рандом</code> — показать 3 случайные анкеты.\n"
    "После выдачи случайных анкет можно нажать кнопки 1, 2, 3 или «Обновить анкеты».\n\n"
    "Поиск профилей:\n\n"
    "<code>.профиль @username</code> — показать профиль пользователя."
)

PRIMARY_GREETING = (
    "Привет! На связи администрация FriendsTime"
)

MS_QUESTIONS = [
    ("telegram_username", "Пожалуйста, укажи свой юз в телеграме (пожалуйста, не меняй до получения личного сообщения от администрации клана)"),
    ("game_nick", "Твой игровой ник:"),
    ("display_name", "Твой псевдоним или имя, по которому мы можем обращаться к тебе:"),
    ("age_birth", "Укажи свой возраст и дату рождения в формате дд.мм.гг. (например, 11.11.2011)"),
    ("clans_relations", "Кланы, в которых ты в черном списке или не в лучших отношениях?"),
    ("profile_screenshot", "Пожалуйста, отправь скриншот своего игрового профиля, на котором четко видны ник, ранг, репутация, киллы и поединки. (бот принимает фото или файл)"),
    ("gender", "Укажи свой пол"),
    ("about_self", "Пожалуйста, расскажи что-нибудь о себе."),
]

BS_QUESTIONS = [
    ("telegram_username", "Пожалуйста, укажи свой юз в телеграме (пожалуйста, не меняй до получения личного сообщения от администрации клана)"),
    ("game_nick", "Твой игровой ник:"),
    ("display_name", "Твой псевдоним или имя, по которому мы можем обращаться к тебе:"),
    ("gender", "Укажи свой пол"),
    ("age_birth", "Укажи свой возраст и дату рождения в формате дд.мм.гг. (например, 11.11.2011)"),
    ("lvl210_animals", "Животные уровня 210, которые у тебя есть:"),
    ("buddies_levels", "Уровни всех твоих приятелей:"),
    ("team_exp", "Опыт командной игры (нет/немного/большой)"),
    ("clans_relations", "Кланы, в которых ты в черном списке или не в лучших отношениях + прошлые БОЕВЫЕ | НЕЙТРАЛЬНЫЕ КЛАНЫ:"),
    ("profile_screenshot", "Отправь скриншот своего игрового профиля, на котором четко видны ник, ранг, репутация, киллы и поединки. (бот принимает фото или файл)"),
    ("about_self", "Пожалуйста, расскажи что-нибудь о себе."),
]

DATING_QUESTIONS = [
("intro", "Я - ваш ник/псевдоним, должность в клане"),
("interests", "Какие интересы у тебя есть помимо этой игры? В каких фандомах состоишь?"),
("music", "Твой любимый музыкальный исполнитель?"),
("extra_optional", "По желанию можешь написать текст о себе и прикрепить фотографии, картинки для поста, героя, с которым ассоциируешь себя, MBTI и т.д. Когда закончишь, нажми кнопку «Готово»."),
("why_friendstime", "Почему в свое время выбрал именно FriendsTime как игровое сообщество, в которое хочешь вступить?"),
("first_impression", "Самое первое впечатление о нашем игровом сообществе?"),
("clan_time", "Как давно находишься в клане?"),
("what_keeps", "Что держит тебя здесь?"),
("associations", "3-4 ассоциации с кланом: предметы, запахи, ощущения, цвета, животные, природа — всё, что угодно."),
("close_people", "Перечисли несколько человек, с которыми ты общаешься близко внутри клана.")
]

PROFILE_QUESTIONS = [
    ("name", "Как тебя подписать в профиле?"),
    ("about", "Коротко расскажи о себе для профиля."),
]

FORM_TITLES = {
    "primary_ms": "Анкета МС",
    "primary_bs": "Анкета БС",
    "dating": "Анкета знакомств",
    "profile": "Профиль",
}

MONTH_NAME_TO_NUM = {
    "январь": 1, "января": 1,
    "февраль": 2, "февраля": 2,
    "март": 3, "марта": 3,
    "апрель": 4, "апреля": 4,
    "май": 5, "мая": 5,
    "июнь": 6, "июня": 6,
    "июль": 7, "июля": 7,
    "август": 8, "августа": 8,
    "сентябрь": 9, "сентября": 9,
    "октябрь": 10, "октября": 10,
    "ноябрь": 11, "ноября": 11,
    "декабрь": 12, "декабря": 12,
}

MONTH_NUM_TO_LABEL = {
    1: "январь", 2: "февраль", 3: "март", 4: "апрель", 5: "май", 6: "июнь",
    7: "июль", 8: "август", 9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь",
}

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@dataclass
class FormConfig:
    form_key: str
    questions: list[tuple[str, str]]
    approval_kind: Optional[str] = None


FORM_CONFIGS = {
    "primary_ms": FormConfig("primary_ms", MS_QUESTIONS, "primary"),
    "primary_bs": FormConfig("primary_bs", BS_QUESTIONS, "primary"),
    "dating": FormConfig("dating", DATING_QUESTIONS, "dating"),
    "profile": FormConfig("profile", PROFILE_QUESTIONS, None),
}


def db_connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    points INTEGER DEFAULT 0,
    choice_type TEXT,
    current_form TEXT,
    current_step INTEGER DEFAULT 0,
    current_status TEXT,
    pending_message_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS form_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    form_key TEXT NOT NULL,
    field_key TEXT NOT NULL,
    value_text TEXT,
    value_file_id TEXT,
    value_file_type TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, form_key, field_key)
);

CREATE TABLE IF NOT EXISTS form_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    form_key TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    submitted_at TEXT,
    approved_at TEXT,
    approved_by INTEGER,
    UNIQUE(user_id, form_key)
);

CREATE TABLE IF NOT EXISTS bot_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS monthly_points (
    period TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT,
    points INTEGER DEFAULT 0,
    snapshotted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (period, user_id)
);
"""


def init_db() -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.executescript(SCHEMA)
    ensure_points_period_current()


def ensure_user(user_id: int, username: Optional[str], full_name: Optional[str]) -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    full_name=excluded.full_name,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, username, full_name),
            )


def get_user(user_id: int):
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return cur.fetchone()


def set_role_if_admin(user_id: int) -> None:
    role = "admin" if user_id in ADMIN_IDS or user_id in SUPERADMIN_IDS else "user"
    with closing(db_connect()) as conn:
        with conn:
            conn.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))

def current_period_key(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.now()
    return dt.strftime("%Y-%m")


def previous_period_key(period: str) -> str:
    year, month = map(int, period.split("-"))
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def format_period_label(period: str) -> str:
    year, month = map(int, period.split("-"))
    return f"{MONTH_NUM_TO_LABEL.get(month, month)} {year}"


def set_meta_value(key: str, value: str) -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO bot_meta (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )


def get_meta_value(key: str) -> Optional[str]:
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM bot_meta WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None


def ensure_points_period_current() -> None:
    today_period = current_period_key()
    stored_period = get_meta_value("points_current_period")

    if not stored_period:
        set_meta_value("points_current_period", today_period)
        return

    if stored_period == today_period:
        return

    with closing(db_connect()) as conn:
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO monthly_points (period, user_id, username, full_name, points)
                SELECT ?, user_id, username, full_name, points FROM users
                """,
                (stored_period,),
            )
            conn.execute("UPDATE users SET points=0, updated_at=CURRENT_TIMESTAMP")

    set_meta_value("points_current_period", today_period)


def parse_points_period_arg(arg: str) -> Optional[str]:
    raw = arg.strip().lower()
    if not raw:
        return None
    if raw in {"текущий", "сейчас", "now"}:
        return current_period_key()
    if raw in {"прошлый", "предыдущий"}:
        return previous_period_key(current_period_key())
    if re.fullmatch(r"\d{4}-\d{2}", raw):
        year, month = map(int, raw.split("-"))
        if 1 <= month <= 12:
            return f"{year:04d}-{month:02d}"
        return None
    parts = raw.split()
    if len(parts) == 1 and parts[0] in MONTH_NAME_TO_NUM:
        month = MONTH_NAME_TO_NUM[parts[0]]
        year = datetime.now().year
        return f"{year:04d}-{month:02d}"
    if len(parts) == 2 and parts[0] in MONTH_NAME_TO_NUM and parts[1].isdigit():
        month = MONTH_NAME_TO_NUM[parts[0]]
        year = int(parts[1])
        return f"{year:04d}-{month:02d}"
    return None


def set_current_form(user_id: int, form_key: Optional[str], step: int = 0, status: Optional[str] = None) -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.execute(
                """
                UPDATE users
                SET current_form=?, current_step=?, current_status=?, updated_at=CURRENT_TIMESTAMP
                WHERE user_id=?
                """,
                (form_key, step, status, user_id),
            )


def save_answer(
    user_id: int,
    form_key: str,
    field_key: str,
    value_text: Optional[str] = None,
    value_file_id: Optional[str] = None,
    value_file_type: Optional[str] = None,
) -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO form_answers (user_id, form_key, field_key, value_text, value_file_id, value_file_type)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, form_key, field_key) DO UPDATE SET
                    value_text=excluded.value_text,
                    value_file_id=excluded.value_file_id,
                    value_file_type=excluded.value_file_type,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (user_id, form_key, field_key, value_text, value_file_id, value_file_type),
            )


def append_answer_text(user_id: int, form_key: str, field_key: str, text_part: str) -> None:
    existing = get_answers(user_id, form_key).get(field_key)
    previous = existing["value_text"] if existing and existing["value_text"] else ""
    value_text = f"{previous}\n{text_part}" if previous else text_part
    value_file_id = existing["value_file_id"] if existing else None
    value_file_type = existing["value_file_type"] if existing else None
    save_answer(user_id, form_key, field_key, value_text, value_file_id, value_file_type)


def append_answer_photo(user_id: int, form_key: str, field_key: str, file_id: str) -> None:
    existing = get_answers(user_id, form_key).get(field_key)
    photos = []
    if existing and existing["value_file_id"]:
        try:
            photos = json.loads(existing["value_file_id"])
            if not isinstance(photos, list):
                photos = [existing["value_file_id"]]
        except Exception:
            photos = [existing["value_file_id"]]
    photos.append(file_id)
    value_text = existing["value_text"] if existing else None
    save_answer(user_id, form_key, field_key, value_text, json.dumps(photos, ensure_ascii=False), "photos")


def get_answers(user_id: int, form_key: str) -> dict[str, sqlite3.Row]:
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM form_answers WHERE user_id=? AND form_key=? ORDER BY id",
            (user_id, form_key),
        )
        rows = cur.fetchall()
        return {row["field_key"]: row for row in rows}


def clear_form_answers(user_id: int, form_key: str) -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.execute("DELETE FROM form_answers WHERE user_id=? AND form_key=?", (user_id, form_key))
            conn.execute("DELETE FROM form_submissions WHERE user_id=? AND form_key=?", (user_id, form_key))


def mark_form_submitted(user_id: int, form_key: str) -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO form_submissions (user_id, form_key, status, submitted_at)
                VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, form_key) DO UPDATE SET
                    status='pending',
                    submitted_at=CURRENT_TIMESTAMP,
                    approved_at=NULL,
                    approved_by=NULL
                """,
                (user_id, form_key),
            )


def set_submission_status(user_id: int, form_key: str, status: str, admin_id: int | None = None) -> None:
    with closing(db_connect()) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO form_submissions (user_id, form_key, status, approved_at, approved_by)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(user_id, form_key) DO UPDATE SET
                    status=excluded.status,
                    approved_at=CURRENT_TIMESTAMP,
                    approved_by=excluded.approved_by
                """,
                (user_id, form_key, status, admin_id),
            )


def get_submission(user_id: int, form_key: str):
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM form_submissions WHERE user_id=? AND form_key=?", (user_id, form_key))
        return cur.fetchone()


def get_role(user_id: int) -> str:
    row = get_user(user_id)
    return row["role"] if row and row["role"] else "user"


def update_points_by_username(username: str, delta: int) -> Optional[int]:
    ensure_points_period_current()
    clean = username.lstrip("@").strip().lower()
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, points FROM users WHERE lower(username)=? OR lower('@' || username)=?",
            (clean, clean),
        )
        row = cur.fetchone()
        if not row:
            return None
        new_points = int(row["points"] or 0) + delta
        with conn:
            conn.execute("UPDATE users SET points=?, updated_at=CURRENT_TIMESTAMP WHERE user_id=?", (new_points, row["user_id"]))
        return new_points


def find_user_by_username(username: str):
    clean = username.lstrip("@").strip().lower()
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE lower(username)=? OR lower('@' || username)=?",
            (clean, clean),
        )
        return cur.fetchone()


def delete_user_from_db_by_username(username: str) -> bool:
    target = find_user_by_username(username)
    if not target:
        return False

    user_id = target["user_id"]
    with closing(db_connect()) as conn:
        with conn:
            conn.execute("DELETE FROM form_answers WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM form_submissions WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM monthly_points WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    return True


def list_random_dating_users(limit: int = 3, exclude_user_id: Optional[int] = None) -> list[sqlite3.Row]:
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        if exclude_user_id:
            cur.execute(
                """
                SELECT u.*
                FROM users u
                JOIN form_submissions fs ON fs.user_id = u.user_id
                WHERE fs.form_key='dating' AND fs.status='approved' AND u.user_id != ?
                """,
                (exclude_user_id,),
            )
        else:
            cur.execute(
                """
                SELECT u.*
                FROM users u
                JOIN form_submissions fs ON fs.user_id = u.user_id
                WHERE fs.form_key='dating' AND fs.status='approved'
                """
            )
        rows = list(cur.fetchall())
        random.shuffle(rows)
        return rows[:limit]


def get_user_pending_form(user_id: int):
    row = get_user(user_id)
    if not row:
        return None, None
    return row["current_form"], row["current_step"]


def get_primary_form_key_for_user(user_id: int) -> str | None:
    user = get_user(user_id)
    if user and user["choice_type"] == "БС":
        return "primary_bs"
    if user and user["choice_type"] == "МС":
        return "primary_ms"

    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT form_key
            FROM form_submissions
            WHERE user_id=? AND form_key IN ('primary_ms', 'primary_bs')
            ORDER BY COALESCE(submitted_at, '') DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row["form_key"]

        cur.execute(
            """
            SELECT DISTINCT form_key
            FROM form_answers
            WHERE user_id=? AND form_key IN ('primary_ms', 'primary_bs')
            ORDER BY form_key DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row["form_key"]

    if form_has_saved_data(user_id, "primary_bs"):
        return "primary_bs"
    if form_has_saved_data(user_id, "primary_ms"):
        return "primary_ms"
    return None



def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id in SUPERADMIN_IDS


def is_private_chat(update: Update) -> bool:
    if not update.effective_chat:
        return False
    return update.effective_chat.type == ChatType.PRIVATE


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("МС", callback_data="apply_ms"),
                InlineKeyboardButton("БС", callback_data="apply_bs"),
            ],
            [InlineKeyboardButton("Открыть меню", callback_data="open_menu")],
        ]
    )


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Профиль", callback_data="menu_profile")],
            [InlineKeyboardButton("Анкета знакомств", callback_data="menu_dating")],
            [InlineKeyboardButton("Поиск анкет", callback_data="menu_search")],
            [InlineKeyboardButton("Помощь", callback_data="menu_help")],
        ]
    )


def bottom_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["Профиль", "Анкета знакомств"],
        ["Поиск анкет", "Помощь"],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=False,
    )


def mixed_step_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Готово", callback_data="mixed_done")]]
    )


def profile_keyboard(has_profile: bool) -> InlineKeyboardMarkup:
    if has_profile:
        rows = [
            [InlineKeyboardButton("Изменить профиль", callback_data="profile_edit")],
            [InlineKeyboardButton("Сохранить профиль", callback_data="profile_show")],
        ]
    else:
        rows = [[InlineKeyboardButton("Создать профиль", callback_data="profile_edit")]]
    rows.append([InlineKeyboardButton("Назад в меню", callback_data="open_menu")])
    return InlineKeyboardMarkup(rows)


def dating_keyboard(has_dating: bool) -> InlineKeyboardMarkup:
    rows = []
    if has_dating:
        rows.extend(
            [
                [InlineKeyboardButton("Изменить анкету", callback_data="dating_edit")],
                [InlineKeyboardButton("Сохранить анкету", callback_data="dating_show")],
                [InlineKeyboardButton("Удалить анкету", callback_data="dating_delete")],
                [InlineKeyboardButton("Заполнить анкету заново", callback_data="dating_restart")],
            ]
        )
    else:
        rows.append([InlineKeyboardButton("Создать анкету", callback_data="dating_edit")])
    rows.append([InlineKeyboardButton("Назад в меню", callback_data="open_menu")])
    return InlineKeyboardMarkup(rows)


def dating_offer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Заполнить анкету знакомств", callback_data="dating_edit")],
            [InlineKeyboardButton("Позже", callback_data="open_menu")],
        ]
    )


def approval_keyboard(kind: str, user_id: int, form_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Принять", callback_data=f"approve:{kind}:{user_id}:{form_key}"),
            InlineKeyboardButton("Отклонить", callback_data=f"reject:{kind}:{user_id}:{form_key}"),
        ]]
    )


def random_profiles_keyboard(user_ids: list[int]) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(str(i + 1), callback_data=f"show_random:{uid}") for i, uid in enumerate(user_ids)]
    return InlineKeyboardMarkup([row, [InlineKeyboardButton("Обновить анкеты", callback_data="refresh_random")]])


def get_question_text(form_key: str, step: int) -> Optional[str]:
    cfg = FORM_CONFIGS.get(form_key)
    if not cfg or step < 0 or step >= len(cfg.questions):
        return None
    _, question = cfg.questions[step]
    return question


def get_field_key(form_key: str, step: int) -> Optional[str]:
    cfg = FORM_CONFIGS.get(form_key)
    if not cfg or step < 0 or step >= len(cfg.questions):
        return None
    field_key, _ = cfg.questions[step]
    return field_key


def form_has_saved_data(user_id: int, form_key: str) -> bool:
    return bool(get_answers(user_id, form_key))


def get_answer_text(answers: dict[str, sqlite3.Row], field_key: str) -> str:
    row = answers.get(field_key)
    if not row or not row["value_text"]:
        return "—"
    return str(row["value_text"])


def get_admin_display(admin_id: Optional[int]) -> str:
    if not admin_id:
        return "—"
    admin = get_user(admin_id)
    if admin:
        if admin["username"]:
            return f"@{admin['username']}"
        if admin["full_name"]:
            return str(admin["full_name"])
    return str(admin_id)


def format_primary_application_text(user_id: int) -> str:
    form_key = get_primary_form_key_for_user(user_id)
    if not form_key:
        return "У этого пользователя нет анкеты вступления."

    answers = get_answers(user_id, form_key)
    submission = get_submission(user_id, form_key)
    status = submission["status"] if submission else "pending"
    approved_by = submission["approved_by"] if submission else None

    if status == "approved":
        status_line = f"✅ ПРИНЯТО администратором {html.escape(get_admin_display(approved_by))}"
    elif status == "rejected":
        status_line = f"❌ ОТКЛОНЕНО администратором {html.escape(get_admin_display(approved_by))}"
    else:
        status_line = "🕓 НА ПРОВЕРКЕ"

    applicant_id = user_id

    return (
        f"{status_line}\n\n"
        "✅ НОВАЯ АНКЕТА В КЛАН\n\n"
        "ЗАЯВКА НА ВСТУПЛЕНИЕ\n\n"
        f"1. Контакт: {html.escape(get_answer_text(answers, 'telegram_username'))}\n"
        f"2. Игровой ник: {html.escape(get_answer_text(answers, 'game_nick'))}\n"
        f"3. У210: {html.escape(get_answer_text(answers, 'lvl210_animals'))}\n"
        f"4. Дата рождения: {html.escape(get_answer_text(answers, 'age_birth'))}\n"
        f"5. Имя: {html.escape(get_answer_text(answers, 'display_name'))}\n"
        f"6. Пол: {html.escape(get_answer_text(answers, 'gender'))}\n"
        f"7. Приятели: {html.escape(get_answer_text(answers, 'buddies_levels'))}\n"
        f"8. Опыт К.И: {html.escape(get_answer_text(answers, 'team_exp'))}\n\n"
        f"✖️ Чужие черные списки: {html.escape(get_answer_text(answers, 'clans_relations'))}\n\n"
        f"📝 О себе:\n{html.escape(get_answer_text(answers, 'about_self'))}\n\n"
        f"🆔 ID заявителя: {applicant_id}"
    )


def format_dating_application_text(user_id: int) -> str:
    form_key = "dating"

    answers = get_answers(user_id, form_key)
    if not answers:
        return "У этого пользователя нет анкеты знакомств."

    submission = get_submission(user_id, form_key)
    status = submission["status"] if submission else "pending"
    approved_by = submission["approved_by"] if submission else None

    if status == "approved":
        status_line = f"✅ ПРИНЯТО администратором {html.escape(get_admin_display(approved_by))}"
    elif status == "rejected":
        status_line = f"❌ ОТКЛОНЕНО администратором {html.escape(get_admin_display(approved_by))}"
    else:
        status_line = "🕓 НА ПРОВЕРКЕ"

    return (
        f"{status_line}\n\n"
        "💚 АНКЕТА ЗНАКОМСТВ\n\n"
        f"1. Имя: {html.escape(get_answer_text(answers, 'intro'))}\n"
        f"2. Интересы и фандомы: {html.escape(get_answer_text(answers, 'interests'))}\n"
        f"3. Любимый исполнитель: {html.escape(get_answer_text(answers, 'music'))}\n"
        f"4. О себе: {html.escape(get_answer_text(answers, 'extra_optional'))}\n"
        f"5. Почему вступил/а: {html.escape(get_answer_text(answers, 'why_friendstime'))}\n"
        f"6. Первое впечатление: {html.escape(get_answer_text(answers, 'first_impression'))}\n"
        f"7. В клане: {html.escape(get_answer_text(answers, 'clan_time'))}\n"
        f"8. Держит в клане: {html.escape(get_answer_text(answers, 'what_keeps'))}\n"
        f"9. Ассоциации с кланом: {html.escape(get_answer_text(answers, 'associations'))}\n"
        f"10. Теплые отношения: {html.escape(get_answer_text(answers, 'close_people'))}"
    )

def extract_file_items(row: Optional[sqlite3.Row]) -> list[tuple[str, str]]:
    if not row or not row["value_file_id"]:
        return []
    file_type = row["value_file_type"] or "document"
    file_value = row["value_file_id"]
    if file_type == "photos":
        try:
            photo_ids = json.loads(file_value)
            if not isinstance(photo_ids, list):
                photo_ids = [file_value]
        except Exception:
            photo_ids = [file_value]
        return [("photo", pid) for pid in photo_ids]
    return [(file_type, file_value)]


async def send_answer_attachments(bot, chat_id: int, answers: dict[str, sqlite3.Row], field_keys: Optional[list[str]] = None) -> None:
    items: list[tuple[str, str]] = []
    rows_iter = answers.items() if field_keys is None else [(k, answers.get(k)) for k in field_keys]
    for _, row in rows_iter:
        items.extend(extract_file_items(row))

    for item_type, file_id in items:
        try:
            if item_type == "photo":
                await bot.send_photo(chat_id=chat_id, photo=file_id)
            else:
                await bot.send_document(chat_id=chat_id, document=file_id)
        except Exception as e:
            logger.exception("Не удалось отправить вложение в %s: %s", chat_id, e)


def format_answers_block(user_id: int, form_key: str) -> str:
    answers = get_answers(user_id, form_key)
    cfg = FORM_CONFIGS[form_key]
    chunks = [f"<b>{html.escape(FORM_TITLES.get(form_key, form_key))}</b>"]
    for field_key, question in cfg.questions:
        row = answers.get(field_key)
        if not row:
            value = "—"
        else:
            parts = []
            if row["value_text"]:
                parts.append(row["value_text"])
            if row["value_file_id"]:
                if row["value_file_type"] == "photos":
                    try:
                        photo_count = len(json.loads(row["value_file_id"]))
                    except Exception:
                        photo_count = 1
                    parts.append(f"[прикреплено фото: {photo_count}]")
                else:
                    parts.append(f"[файл: {row['value_file_type']}]")
            value = "\n".join(parts) if parts else "—"
        chunks.append(f"<b>{html.escape(question)}</b>\n{html.escape(str(value))}")
    return "\n\n".join(chunks)


def format_profile_short(user_id: int) -> str:
    user = get_user(user_id)
    answers = get_answers(user_id, "profile")
    name = answers.get("name")
    about = answers.get("about")
    points = user["points"] if user else 0
    username = f"@{user['username']}" if user and user['username'] else "нет username"
    return (
        f"<b>Профиль</b>\n"
        f"Username: {html.escape(username)}\n"
        f"Имя: {html.escape(name['value_text']) if name and name['value_text'] else '—'}\n"
        f"О себе: {html.escape(about['value_text']) if about and about['value_text'] else '—'}\n"
        f"Очки: {points}"
    )


def parse_username_arg(text: str) -> Optional[str]:
    match = re.search(r"@([A-Za-z0-9_]{4,})", text)
    return f"@{match.group(1)}" if match else None


async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, form_key: str) -> None:
    row = get_user(user_id)
    step = row["current_step"] if row else 0
    question = get_question_text(form_key, step)
    if not question:
        await finish_form_submission(update, context, user_id, form_key)
        return

    prefix = ""
    if step == 0 and form_key in ("primary_ms", "primary_bs"):
        prefix = PRIMARY_GREETING + "\n\n"

    reply_markup = mixed_step_keyboard() if form_key == "dating" and get_field_key(form_key, step) == "extra_optional" else None
    await context.bot.send_message(chat_id=user_id, text=prefix + question, reply_markup=reply_markup)


async def send_submission_for_review(context: ContextTypes.DEFAULT_TYPE, user_id: int, form_key: str) -> bool:
    cfg = FORM_CONFIGS[form_key]
    admin_text = format_primary_application_text(user_id) if form_key.startswith("primary_") else format_answers_block(user_id, form_key)
    kind = cfg.approval_kind or form_key
    targets = set(ADMIN_IDS) | set(REVIEW_CHAT_IDS)
    answers = get_answers(user_id, form_key)
    sent = False
    for target_id in targets:
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=admin_text,
                parse_mode="HTML",
                reply_markup=approval_keyboard(kind, user_id, form_key),
            )
            await send_answer_attachments(context.bot, target_id, answers)
            sent = True
        except Exception as e:
            logger.exception("Не удалось отправить анкету в %s: %s", target_id, e)
    return sent


async def finish_form_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, form_key: str) -> None:
    set_current_form(user_id, None, 0, None)

    if form_key == "profile":
        await context.bot.send_message(chat_id=user_id, text="Профиль сохранён.", reply_markup=menu_keyboard())
        return

    mark_form_submitted(user_id, form_key)
    sent_to_any_admin = await send_submission_for_review(context, user_id, form_key)

    if form_key.startswith("primary_"):
        if sent_to_any_admin:
            await context.bot.send_message(chat_id=user_id, text="Спасибо. Твоя анкета отправлена на проверку.")
        else:
            await context.bot.send_message(chat_id=user_id, text="Анкета сохранена, но я не смог отправить её на проверку. Проверь ADMIN_IDS или REVIEW_CHAT_IDS.")
    elif form_key == "dating":
        if sent_to_any_admin:
            await context.bot.send_message(chat_id=user_id, text="Анкета знакомств отправлена на проверку.")
        else:
            await context.bot.send_message(chat_id=user_id, text="Анкета знакомств сохранена, но я не смог отправить её на проверку.")


async def show_primary_application(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, target_user_id: int) -> None:
    form_key = get_primary_form_key_for_user(target_user_id)
    if not form_key:
        await context.bot.send_message(chat_id=chat_id, text="У этого пользователя нет анкеты вступления.")
        return

    text = format_primary_application_text(target_user_id)
    answers = get_answers(target_user_id, form_key)
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    await send_answer_attachments(context.bot, chat_id, answers, field_keys=["profile_screenshot"])



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.full_name)
    set_role_if_admin(user.id)

    if not is_private_chat(update):
        await update.message.reply_text("Бот работает через личные сообщения. Напиши мне в личку: /start")
        return

    photo_sent = False

    if os.path.exists(START_IMAGE_PATH):
        try:
            with open(START_IMAGE_PATH, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=START_TEXT,
                    reply_markup=start_keyboard(),
                )
            photo_sent = True
        except Exception as e:
            logger.exception("Не удалось отправить стартовое фото: %s", e)

    if not photo_sent:
        await update.message.reply_text(
            START_TEXT,
            reply_markup=start_keyboard(),
        )

    await update.message.reply_text(
        "Нижнее меню включено.",
        reply_markup=bottom_menu_keyboard(),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.full_name)
    if not is_private_chat(update):
        await update.message.reply_text("Меню доступно только в личке с ботом.")
        return
    await update.message.reply_text("Нижнее меню включено.", reply_markup=bottom_menu_keyboard())
    await update.message.reply_text("Меню бота:", reply_markup=menu_keyboard())


async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    ensure_user(user.id, user.username, user.full_name)
    set_role_if_admin(user.id)
    data = query.data

    # Кнопки модерации и просмотра случайных анкет можно использовать и в беседе, и в личке
    if data.startswith("approve:") or data.startswith("reject:"):
        if not is_admin(user.id):
            await query.answer("Нет доступа", show_alert=True)
            return

        action, kind, target_user_id, form_key = data.split(":", 3)
        target_user_id = int(target_user_id)
        status = "approved" if action == "approve" else "rejected"
        set_submission_status(target_user_id, form_key, status, user.id)

        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"Решение сохранено: {status}")

        if status == "approved":
            if kind == "primary":
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        "☑️ ваша анкета рассмотрена и одобрена советом!\n"
                        "основной чат клана: https://t.me/+AV2gZLH7NZY0Mjhi\n\n"
                        "по вопросам добавления в игровой тег обращайтесь к руководству."
                    ),
                )
            else:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="Твоя анкета знакомств принята.",
                )
        else:
            if kind == "primary":
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        "✖️ ваша анкета была рассмотрена и отклонена советом, "
                        "мы имеем право не оглашать причину отказа. всего доброго!"
                    ),
                )
            else:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="Твоя анкета знакомств была отклонена администрацией.",
                )
        return
        if data == "refresh_random":
            await send_random_profiles(update, context, user.id, query.message.chat_id)
            return

        if data == "mixed_done":
            row = get_user(user.id)
            if not row:
                await query.answer("Пользователь не найден.", show_alert=True)
                return

        if row["current_form"] == "dating" and get_field_key("dating", row["current_step"] or 0) == "extra_optional":
            next_step = (row["current_step"] or 0) + 1
            set_current_form(user.id, "dating", next_step, "collecting")
            await query.message.reply_text("Переходим дальше.")
            if next_step >= len(FORM_CONFIGS["dating"].questions):
                await finish_form_submission(update, context, user.id, "dating")
            else:
                await query.message.reply_text(get_question_text("dating", next_step))
            return

        await query.answer("Эта кнопка сейчас неактивна.", show_alert=True)
        return

    # Всё, что ниже, только в личке
    if query.message.chat.type != ChatType.PRIVATE:
        await query.answer("Эта кнопка работает только в личке с ботом.", show_alert=True)
        return

    if data == "open_menu":
        await query.message.reply_text("Нижнее меню включено.", reply_markup=bottom_menu_keyboard())
        await query.message.reply_text("Меню бота:", reply_markup=menu_keyboard())
        return

    if data == "apply_ms":
        clear_form_answers(user.id, "primary_ms")
        set_current_form(user.id, "primary_ms", 0, "collecting")
        with closing(db_connect()) as conn:
            with conn:
                conn.execute("UPDATE users SET choice_type='МС' WHERE user_id=?", (user.id,))
        await query.message.reply_text("Начинаем анкету МС.")
        await send_next_question(update, context, user.id, "primary_ms")
        return

    if data == "apply_bs":
        clear_form_answers(user.id, "primary_bs")
        set_current_form(user.id, "primary_bs", 0, "collecting")
        with closing(db_connect()) as conn:
            with conn:
                conn.execute("UPDATE users SET choice_type='БС' WHERE user_id=?", (user.id,))
        await query.message.reply_text("Начинаем анкету БС.")
        await send_next_question(update, context, user.id, "primary_bs")
        return

    if data == "menu_profile":
        await query.message.reply_text(
            PROFILE_TEXT,
            reply_markup=profile_keyboard(form_has_saved_data(user.id, "profile")),
        )
        return

    if data == "profile_edit":
        set_current_form(user.id, "profile", 0, "collecting")
        await query.message.reply_text("Переходим к редактированию профиля.")
        await send_next_question(update, context, user.id, "profile")
        return

    if data == "profile_show":
        await query.message.reply_text(format_profile_short(user.id), parse_mode="HTML", reply_markup=profile_keyboard(True))
        return

    if data == "menu_dating":
        await query.message.reply_text(
            "Раздел анкеты знакомств:",
            reply_markup=dating_keyboard(form_has_saved_data(user.id, "dating")),
        )
        return

    if data in ("dating_edit", "dating_restart"):
        if data == "dating_restart":
            clear_form_answers(user.id, "dating")
        set_current_form(user.id, "dating", 0, "collecting")
        await query.message.reply_text("Начинаем анкету знакомств.")
        await send_next_question(update, context, user.id, "dating")
        return

    if data == "dating_show":
        submission = get_submission(user.id, "dating")
        status = submission["status"] if submission else "draft"
        await query.message.reply_text(
            format_answers_block(user.id, "dating") + f"\n\nСтатус: <b>{html.escape(status)}</b>",
            parse_mode="HTML",
            reply_markup=dating_keyboard(True),
        )
        return

    if data == "dating_delete":
        clear_form_answers(user.id, "dating")
        await query.message.reply_text("Анкета знакомств удалена.", reply_markup=dating_keyboard(False))
        return

    if data == "menu_search":
        await query.message.reply_text(SEARCH_HELP_TEXT, parse_mode="HTML", reply_markup=bottom_menu_keyboard())
        return

    if data == "menu_help":
        await query.message.reply_text(SEARCH_HELP_TEXT, parse_mode="HTML", reply_markup=bottom_menu_keyboard())
        return


async def handle_form_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.full_name)
    set_role_if_admin(user.id)

    if not is_private_chat(update):
        return

    current_form, current_step = get_user_pending_form(user.id)
    if not current_form:
        return

    cfg = FORM_CONFIGS.get(current_form)
    if not cfg:
        return

    step = int(current_step or 0)
    if step >= len(cfg.questions):
        await finish_form_submission(update, context, user.id, current_form)
        return

    field_key, _ = cfg.questions[step]

    text_value = None
    file_id = None
    file_type = None

    if current_form == "dating" and field_key == "extra_optional":
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            append_answer_photo(user.id, current_form, field_key, file_id)
            await update.message.reply_text(
                "Фото сохранено. Можешь отправить ещё фото, написать текст или нажать «Готово».",
                reply_markup=mixed_step_keyboard(),
            )
            return
        if update.message.document:
            await update.message.reply_text("На этом шаге можно отправлять только фотографии и текст.", reply_markup=mixed_step_keyboard())
            return
        if not update.message.text:
            await update.message.reply_text("Можешь написать текст, отправить фото или нажать «Готово».", reply_markup=mixed_step_keyboard())
            return
        text_value = update.message.text.strip()
        if not text_value:
            await update.message.reply_text("Пустой ответ не подойдёт. Напиши текст, отправь фото или нажми «Готово».", reply_markup=mixed_step_keyboard())
            return
        append_answer_text(user.id, current_form, field_key, text_value)
        await update.message.reply_text(
            "Текст сохранён. Можешь дописать ещё, отправить фото или нажать «Готово».",
            reply_markup=mixed_step_keyboard(),
        )
        return

    if field_key == "profile_screenshot":
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            file_type = "photo"
        elif update.message.document:
            file_id = update.message.document.file_id
            file_type = "document"
        else:
            await update.message.reply_text("Здесь нужно отправить фото или файл, а не текст.")
            return
    else:
        if not update.message.text:
            await update.message.reply_text("Здесь нужен текстовый ответ.")
            return
        text_value = update.message.text.strip()
        if not text_value:
            await update.message.reply_text("Пустой ответ не подойдёт.")
            return

    save_answer(user.id, current_form, field_key, text_value, file_id, file_type)
    next_step = step + 1
    set_current_form(user.id, current_form, next_step, "collecting")

    if next_step >= len(cfg.questions):
        await finish_form_submission(update, context, user.id, current_form)
    else:
        reply_markup = mixed_step_keyboard() if current_form == "dating" and get_field_key(current_form, next_step) == "extra_optional" else None
        await update.message.reply_text(get_question_text(current_form, next_step), reply_markup=reply_markup)


async def handle_search_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user
    ensure_user(user.id, user.username, user.full_name)
    set_role_if_admin(user.id)

    if text.lower().startswith(".знакомство рандом"):
        await send_random_profiles(update, context, user.id, update.message.chat_id)
        return

    if text.lower().startswith(".знакомство "):
        username = parse_username_arg(text)
        if not username:
            await update.message.reply_text("Используй формат: .знакомство @username")
            return
        target = find_user_by_username(username)
        if not target:
            await update.message.reply_text("Анкета не найдена.")
            return
        submission = get_submission(target["user_id"], "dating")
        if not submission or submission["status"] != "approved":
            await update.message.reply_text("У этого пользователя нет одобренной анкеты знакомств.")
            return
        await show_dating_profile_by_user_id(update, context, update.message.chat_id, target["user_id"])
        return

    if text.lower().startswith(".профиль "):
        username = parse_username_arg(text)
        if not username:
            await update.message.reply_text("Используй формат: .профиль @username")
            return
        target = find_user_by_username(username)
        if not target:
            await update.message.reply_text("Профиль не найден.")
            return
        if not form_has_saved_data(target["user_id"], "profile"):
            await update.message.reply_text("У этого пользователя нет заполненного профиля.")
            return
        await update.message.reply_text(format_profile_short(target["user_id"]), parse_mode="HTML")
        return

    if text.lower().startswith(".анкета "):
        if update.message.chat.type == ChatType.PRIVATE and not is_admin(user.id):
            await update.message.reply_text("Эта команда нужна для беседы администрации.")
            return
        if update.message.chat.type != ChatType.PRIVATE and not is_admin(user.id):
            await update.message.reply_text("В беседе эту команду могут использовать только админы.")
            return
        username = parse_username_arg(text)
        if not username:
            await update.message.reply_text("Используй формат: .анкета @username")
            return
        target = find_user_by_username(username)
        if not target:
            await update.message.reply_text("Пользователь не найден.")
            return
        await show_primary_application(update, context, update.message.chat_id, target["user_id"])
        return

    if text.lower().startswith(".исключить "):
        if not is_admin(user.id):
            await update.message.reply_text("Эта команда доступна только админам.")
            return
        username = parse_username_arg(text)
        if not username:
            await update.message.reply_text("Используй формат: .исключить @username")
            return
        deleted = delete_user_from_db_by_username(username)
        if not deleted:
            await update.message.reply_text("Пользователь не найден.")
            return
        await update.message.reply_text(f"Пользователь {username} удалён из базы вместе с анкетами и очками.")
        return

    if text.lower().startswith(".очки"):
        if not is_admin(user.id):
            await update.message.reply_text("Эта команда доступна только админам.")
            return

        m = re.fullmatch(r"\.очки([+-]\d+)\s+@([A-Za-z0-9_]{4,})", text)
        if m:
            delta = int(m.group(1))
            username = f"@{m.group(2)}"
            new_points = update_points_by_username(username, delta)
            if new_points is None:
                await update.message.reply_text("Пользователь не найден.")
                return
            await update.message.reply_text(f"Очки обновлены. Теперь у {username}: {new_points}")
            return

        arg = text[5:].strip()
        if not arg:
            await send_points_list(update.message.chat_id, context)
            return

        period = parse_points_period_arg(arg)
        if not period:
            await update.message.reply_text(
                "Не понял период. Используй, например: .очки, .очки прошлый, .очки март 2026 или .очки 2026-03"
            )
            return

        await send_points_list(update.message.chat_id, context, period=period)
        return


def get_all_points_rows() -> list[sqlite3.Row]:
    ensure_points_period_current()
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT username, full_name, points
            FROM users
            ORDER BY points DESC, lower(COALESCE(username, full_name, '')) ASC
            """
        )
        return list(cur.fetchall())


def get_points_rows_for_period(period: str) -> list[sqlite3.Row]:
    current = current_period_key()
    if period == current:
        return get_all_points_rows()
    with closing(db_connect()) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT username, full_name, points
            FROM monthly_points
            WHERE period=?
            ORDER BY points DESC, lower(COALESCE(username, full_name, '')) ASC
            """,
            (period,),
        )
        return list(cur.fetchall())


async def send_points_list(chat_id: int, context: ContextTypes.DEFAULT_TYPE, period: Optional[str] = None) -> None:
    ensure_points_period_current()
    target_period = period or current_period_key()
    rows = get_points_rows_for_period(target_period)
    if not rows:
        await context.bot.send_message(chat_id=chat_id, text="В базе пока нет участников.")
        return

    lines = ["Очки участников:\n"]
    for i, row in enumerate(rows, start=1):
        username = f"@{row['username']}" if row['username'] else "(без username)"
        full_name = row['full_name'] or "Без имени"
        points = row['points'] or 0
        lines.append(f"{i}. {username} | {full_name} | {points} очк.")

    message = "\n".join(lines)
    if len(message) <= 4000:
        await context.bot.send_message(chat_id=chat_id, text=message)
        return

    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > 4000:
            await context.bot.send_message(chat_id=chat_id, text=chunk)
            chunk = line
        else:
            chunk = f"{chunk}\n{line}" if chunk else line
    if chunk:
        await context.bot.send_message(chat_id=chat_id, text=chunk)


async def send_random_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE, requester_id: int, chat_id: int) -> None:
    rows = list_random_dating_users(limit=3, exclude_user_id=requester_id)
    if not rows:
        await context.bot.send_message(chat_id=chat_id, text="Пока нет доступных анкет знакомств.")
        return

    lines = ["Вот 3 случайные анкеты. Нажми кнопку 1, 2 или 3:"]
    user_ids = []
    for idx, row in enumerate(rows, start=1):
        user_ids.append(row["user_id"])
        answers = get_answers(row["user_id"], "dating")
        nick = answers.get("display_name") or answers.get("game_nick")
        nick_text = nick["value_text"] if nick and nick["value_text"] else f"user_{row['user_id']}"
        lines.append(f"{idx}. {nick_text}")

    await context.bot.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        reply_markup=random_profiles_keyboard(user_ids),
    )


async def show_dating_profile_by_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, target_user_id: int) -> None:
    submission = get_submission(target_user_id, "dating")
    if not submission or submission["status"] != "approved":
        await context.bot.send_message(chat_id=chat_id, text="У этого пользователя нет одобренной анкеты знакомств.")
        return

    text = format_dating_application_text(target_user_id)
    answers = get_answers(target_user_id, "dating")
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    await send_answer_attachments(context.bot, chat_id, answers, field_keys=["profile_screenshot", "extra_optional"])


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_private_chat(update):
        return

    user = update.effective_user
    ensure_user(user.id, user.username, user.full_name)
    set_role_if_admin(user.id)

    text = (update.message.text or "").strip()
    row = get_user(user.id)
    if row and row["current_form"] and row["current_step"] is not None:
        await update.message.reply_text(
            "Сейчас ты заполняешь анкету. Сначала заверши её или используй /cancel.",
            reply_markup=bottom_menu_keyboard(),
        )
        raise ApplicationHandlerStop

    if text == "Помощь":
        await update.message.reply_text(SEARCH_HELP_TEXT, parse_mode="HTML", reply_markup=bottom_menu_keyboard())
        raise ApplicationHandlerStop

    if text == "Поиск анкет":
        await update.message.reply_text(SEARCH_HELP_TEXT, parse_mode="HTML", reply_markup=bottom_menu_keyboard())
        raise ApplicationHandlerStop

    if text == "Профиль":
        await update.message.reply_text(
            PROFILE_TEXT,
            reply_markup=profile_keyboard(form_has_saved_data(user.id, "profile")),
        )
        raise ApplicationHandlerStop

    if text == "Анкета знакомств":
        await update.message.reply_text(
            "Раздел анкеты знакомств:",
            reply_markup=dating_keyboard(form_has_saved_data(user.id, "dating")),
        )
        raise ApplicationHandlerStop


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(SEARCH_HELP_TEXT, parse_mode="HTML", reply_markup=bottom_menu_keyboard() if is_private_chat(update) else None)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ensure_user(user.id, user.username, user.full_name)
    set_current_form(user.id, None, 0, None)
    await update.message.reply_text(
        "Текущее заполнение остановлено. Данные, уже сохранённые в базу, не пропали.",
        reply_markup=bottom_menu_keyboard() if is_private_chat(update) else None,
    )


async def debug_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    row = get_user(user.id)
    if not row:
        await update.message.reply_text("Пользователь не найден в базе.")
        return
    await update.message.reply_text(
        f"current_form={row['current_form']}\ncurrent_step={row['current_step']}\nrole={row['role']}\npoints={row['points']}"
    )
async def chat_id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"chat_id этой беседы: {update.effective_chat.id}")

def main() -> None:
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("state", debug_state))
    application.add_handler(CommandHandler("chatid", chat_id_cmd))


    application.add_handler(CallbackQueryHandler(handle_callbacks))

    application.add_handler(
        MessageHandler(
            filters.Regex(r"^(Профиль|Анкета знакомств|Поиск анкет|Помощь)$"),
            handle_menu_buttons,
        ),
        group=0,
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_commands),
        group=0,
    )
    application.add_handler(
        MessageHandler(
            (
                (filters.TEXT & ~filters.Regex(r"^(Профиль|Анкета знакомств|Поиск анкет|Помощь)$"))
                | filters.PHOTO
                | filters.Document.ALL
            ) & ~filters.COMMAND,
            handle_form_input,
        ),
        group=1,
    )

    print("FriendsTime bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()