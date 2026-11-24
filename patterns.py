import threading
from models import Book, Reader, LibraryError, ValidationError, BookNotAvailableError


class LibraryDatabase:
    """Singleton-сховище даних бібліотеки з потокобезпечним блокуванням."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst.books: dict[str, Book] = {}
                    inst.readers: dict[str, Reader] = {}
                    inst.io_lock = threading.RLock()
                    inst._observers = []
                    cls._instance = inst
        return cls._instance

    def subscribe(self, observer):
        with self.io_lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def notify(self, event: str, payload: str):
        with self.io_lock:
            observers_copy = list(self._observers)
        for obs in observers_copy:
            obs.update(event, payload)


class ConsoleNotifier:
    """Спостерігач (Observer) для фіксації подій бібліотеки."""

    def __init__(self):
        self.events: list[str] = []
        self._lock = threading.Lock()

    def update(self, event: str, payload: str):
        line = f"[{event}] {payload}"
        with self._lock:
            self.events.append(line)


class LibraryRepository:
    """Патерн Repository / Facade для безпечних операцій над книгами та читачами."""

    def __init__(self, db: LibraryDatabase):
        self.db = db

    def add_book(self, book: Book):
        with self.db.io_lock:
            if book.isbn in self.db.books:
                self.db.books[book.isbn].copies += book.copies
                self.db.notify("ADD_COPIES", f"{book.title} (+{book.copies})")
            else:
                self.db.books[book.isbn] = book
                self.db.notify("ADD_BOOK", f"{book.title} ({book.isbn})")

    def register_reader(self, reader: Reader):
        with self.db.io_lock:
            if reader.card_id in self.db.readers:
                raise ValidationError(f"Читач із квитком '{reader.card_id}' уже зареєстрований.")
            self.db.readers[reader.card_id] = reader
            self.db.notify("NEW_READER", f"{reader.name} ({reader.card_id})")

    def borrow_book(self, card_id: str, isbn: str):
        with self.db.io_lock:
            reader = self.db.readers.get(card_id)
            if not reader:
                raise LibraryError(f"Читача з квитком '{card_id}' не знайдено.")

            book = self.db.books.get(isbn)
            if not book:
                raise LibraryError(f"Книгу з ISBN '{isbn}' не знайдено.")

            if book.copies <= 0:
                raise BookNotAvailableError(f"Немає вільних примірників книги '{book.title}'.")

            book.copies -= 1
            reader.borrowed_isbns.append(isbn)
            self.db.notify("BORROW", f"{reader.name} взяв '{book.title}'")

    def return_book(self, card_id: str, isbn: str):
        with self.db.io_lock:
            reader = self.db.readers.get(card_id)
            if not reader:
                raise LibraryError(f"Читача з квитком '{card_id}' не знайдено.")

            book = self.db.books.get(isbn)
            if not book:
                raise LibraryError(f"Книгу з ISBN '{isbn}' не знайдено.")

            if isbn not in reader.borrowed_isbns:
                raise LibraryError(f"У читача '{reader.name}' немає книги з ISBN '{isbn}'.")

            reader.borrowed_isbns.remove(isbn)
            book.copies += 1
            self.db.notify("RETURN", f"{reader.name} повернув '{book.title}'")

    def search_books(self, query: str) -> list[Book]:
        q = query.strip().lower()
        with self.db.io_lock:
            return [
                b for b in self.db.books.values()
                if q in b.title.lower() or q in b.author.name.lower() or q in b.isbn.lower()
            ]