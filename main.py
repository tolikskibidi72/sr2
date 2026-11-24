from models import Author, Book, Reader, LibraryError
from patterns import LibraryDatabase, ConsoleNotifier, LibraryRepository
from service import LibraryService


def seed_data(repo: LibraryRepository):
    a1 = Author("Роберт Мартін", "США")
    a2 = Author("Алан Доуні", "США")
    a3 = Author("Леся Українка", "Україна")

    repo.add_book(Book("Чистий код", a1, 2008, "ISBN-01", copies=2))
    repo.add_book(Book("Think Python", a2, 2015, "ISBN-02", copies=1))
    repo.add_book(Book("Лісова пісня", a3, 1911, "ISBN-03", copies=2))

    repo.register_reader(Reader("Іван Коваленко", "R-01"))
    repo.register_reader(Reader("Олена Ткач", "R-02"))
    repo.register_reader(Reader("Максим Савчук", "R-03"))


def run_multithread_demo(service: LibraryService):
    print("\n--- Тест паралельних запитів (ThreadPoolExecutor) ---")
    batch = [
        ("borrow", "R-01", "ISBN-01"),
        ("borrow", "R-02", "ISBN-01"),
        ("borrow", "R-03", "ISBN-01"),  # 3-й запит на книгу з 2 примірниками -> коректна відмова
        ("search", "код"),
        ("search", "Python"),
        ("return", "R-01", "ISBN-01"),
        ("borrow", "R-03", "ISBN-01"),  # після повернення знову є вільний примірник
    ]
    for line in service.run_concurrent_requests(batch, max_workers=4):
        print(line)


def main():
    db = LibraryDatabase()
    notifier = ConsoleNotifier()
    db.subscribe(notifier)

    repo = LibraryRepository(db)
    service = LibraryService(repo)
    seed_data(repo)

    while True:
        print("\n=== Бібліотека (СР №2) ===")
        print("1 - Показати книги")
        print("2 - Додати книгу")
        print("3 - Видати книгу читачу")
        print("4 - Повернути книгу")
        print("5 - Запустити тест мультипоточності")
        print("6 - Показати журнал подій (Observer)")
        print("0 - Вихід")

        choice = input("> ").strip()
        try:
            if choice == "0":
                break
            elif choice == "1":
                for b in db.books.values():
                    print(" ", b)
            elif choice == "2":
                title = input("Назва: ")
                author_name = input("Автор: ")
                year = int(input("Рік: "))
                isbn = input("ISBN: ")
                copies = int(input("Кількість примірників: "))
                book = Book(title, Author(author_name), year, isbn, copies)
                repo.add_book(book)
                print("Книгу додано.")
            elif choice == "3":
                card_id = input("Квиток читача (наприклад R-01): ").strip()
                isbn = input("ISBN книги (наприклад ISBN-01): ").strip()
                repo.borrow_book(card_id, isbn)
                print("Книгу видано.")
            elif choice == "4":
                card_id = input("Квиток читача: ").strip()
                isbn = input("ISBN книги: ").strip()
                repo.return_book(card_id, isbn)
                print("Книгу повернуто.")
            elif choice == "5":
                run_multithread_demo(service)
            elif choice == "6":
                for ev in notifier.events:
                    print(" ", ev)
            else:
                print("Невідома команда.")
        except ValueError:
            print("Помилка вводу: очікувалося ціле число.")
        except LibraryError as exc:
            print(f"Помилка бібліотеки: {exc}")


if __name__ == "__main__":
    main()