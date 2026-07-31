alphabet = "abcdefghijklmnopqrstuvwxyz"


def caesar(text, shift, direction):
    result = ""

    for letter in text:
        if letter.lower() in alphabet:
            index = alphabet.index(letter.lower())

            if direction == "encode":
                new_index = (index + shift) % 26
            else:
                new_index = (index - shift) % 26

            new_letter = alphabet[new_index]

            if letter.isupper():
                result += new_letter.upper()
            else:
                result += new_letter
        else:
            result += letter

    return result


print("=== Caesar Cipher Practice ===")

while True:
    choice = input("\nType 'encode', 'decode' or 'exit': ").lower()

    if choice == "exit":
        print("Goodbye!")
        break

    if choice not in ["encode", "decode"]:
        print("Invalid choice.")
        continue

    message = input("Enter your message: ")
    shift = int(input("Enter shift number: "))

    output = caesar(message, shift, choice)

    print(f"\nResult: {output}")