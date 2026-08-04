class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.available = True

    def borrow(self):
        if self.available:
            self.available = False
            print(f'📚 "{self.title}" has been borrowed.')
        else:
            print(f'❌ "{self.title}" is already borrowed.')

    def return_book(self):
        if not self.available:
            self.available = True
            print(f'✅ "{self.title}" has been returned.')
        else:
            print(f'ℹ️ "{self.title}" is already available.')