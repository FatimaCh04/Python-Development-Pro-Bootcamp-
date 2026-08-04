from book import Book


class Library:
    def __init__(self):
        self.books = []

    def add_book(self, title, author):
        self.books.append(Book(title, author))
        print(f'📖 "{title}" added successfully.')

    def show_books(self):
        print("\n========== Library Books ==========")

        if len(self.books) == 0:
            print("No books available.")
            return

        for index, book in enumerate(self.books, start=1):
            status = "Available" if book.available else "Borrowed"
            print(f"{index}. {book.title} - {book.author} ({status})")