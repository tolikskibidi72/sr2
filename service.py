from concurrent.futures import ThreadPoolExecutor, as_completed
from models import LibraryError
from patterns import LibraryRepository


class LibraryService:
    """Сервісний шар для одночасного виконання запитів у потоках."""

    def __init__(self, repo: LibraryRepository):
        self.repo = repo

    def run_concurrent_requests(self, requests: list[tuple], max_workers: int = 4) -> list[str]:
        """
        Приймає список кортежів запитів:
          ("search", query)
          ("borrow", card_id, isbn)
          ("return", card_id, isbn)
        """
        results: list[str] = []

        def handle_one(req: tuple) -> str:
            action = req[0]
            if action == "search":
                _, query = req
                found = self.repo.search_books(query)
                return f"[ПОШУК '{query}'] знайдено: {len(found)}"
            elif action == "borrow":
                _, card_id, isbn = req
                self.repo.borrow_book(card_id, isbn)
                return f"[ВИДАЧА] квиток={card_id}, isbn={isbn} -> успішно"
            elif action == "return":
                _, card_id, isbn = req
                self.repo.return_book(card_id, isbn)
                return f"[ПОВЕРНЕННЯ] квиток={card_id}, isbn={isbn} -> успішно"
            else:
                return f"[ПОМИЛКА] невідомий тип запиту: {action}"

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(handle_one, r) for r in requests]
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except LibraryError as exc:
                    results.append(f"[ВІДМОВА] {exc}")
                except Exception as exc:
                    results.append(f"[ЗБІЙ] {exc}")

        return results