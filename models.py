import logging
import functools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("library")


class LibraryError(Exception):
    """Базовий виняток системи бібліотеки."""


class ValidationError(LibraryError):
    """Помилка некоректних даних."""


class BookNotAvailableError(LibraryError):
    """Книга недоступна для видачі."""


class EntityMeta(type):
    """Метаклас для логування створення об'єктів моделей."""

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        logger.info("Створено об'єкт %s: %s", cls.__name__, instance)
        return instance


def validate_non_empty_str(*field_names):
    """Декоратор для перевірки, що вказані текстові поля не порожні."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Підтримуємо і методи екземпляра (self), і звичайні функції
            sig_names = func.__code__.co_varnames[: func.__code__.co_argcount]
            bound = {}
            for name, val in zip(sig_names, args):
                bound[name] = val
            bound.update(kwargs)

            for fname in field_names:
                if fname in bound:
                    val = bound[fname]
                    if not isinstance(val, str) or not val.strip():
                        raise ValidationError(f"Поле '{fname}' не може бути порожнім.")
            return func(*args, **kwargs)

        return wrapper

    return decorator


class Author(metaclass=EntityMeta):
    @validate_non_empty_str("name")
    def __init__(self, name: str, country: str = "Невідомо"):
        self.name = name.strip()
        self.country = country.strip() if country else "Невідомо"

    def __str__(self):
        return f"Автор({self.name}, {self.country})"


class Book(metaclass=EntityMeta):
    @validate_non_empty_str("title", "isbn")
    def __init__(self, title: str, author: Author, year: int, isbn: str, copies: int = 1):
        if not isinstance(year, int) or year < 1000 or year > 2100:
            raise ValidationError("Некоректний рік видання книги.")
        if not isinstance(copies, int) or copies < 0:
            raise ValidationError("Кількість примірників не може бути від'ємною.")

        self.title = title.strip()
        self.author = author
        self.year = year
        self.isbn = isbn.strip()
        self.copies = copies

    def __str__(self):
        return f"Книга('{self.title}', {self.author.name}, {self.year}, прим.: {self.copies})"


class Reader(metaclass=EntityMeta):
    @validate_non_empty_str("name", "card_id")
    def __init__(self, name: str, card_id: str):
        self.name = name.strip()
        self.card_id = card_id.strip()
        self.borrowed_isbns: list[str] = []

    def __str__(self):
        return f"Читач({self.name}, квиток: {self.card_id})"