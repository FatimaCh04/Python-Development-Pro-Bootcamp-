from library import Library

library = Library()

library.add_book("Python Basics", "Angela Yu")
library.add_book("Clean Code", "Robert C. Martin")
library.add_book("Atomic Habits", "James Clear")

while True:

    print("\n========== Library Menu ==========")
    print("1. Show Books")
    print("2. Borrow Book")
    print("3. Return Book")
    print("4. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        library.show_books()

    elif choice == "2":
        library.show_books()

        try:
            number = int(input("Enter book number: "))

            if 1 <= number <= len(library.books):
                library.books[number - 1].borrow()
            else:
                print("Invalid book number.")

        except ValueError:
            print("Please enter a valid number.")

    elif choice == "3":
        library.show_books()

        try:
            number = int(input("Enter book number: "))

            if 1 <= number <= len(library.books):
                library.books[number - 1].return_book()
            else:
                print("Invalid book number.")

        except ValueError:
            print("Please enter a valid number.")

    elif choice == "4":
        print("👋 Thank you for using the Library Management System!")
        break

    else:
        print("❌ Invalid choice. Please try again.")