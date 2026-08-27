# 🐍 Day 76 — NATO Phonetic Alphabet

This project is part of **Angela Yu's 100 Days of Code: The Complete Python Pro Bootcamp**.

## 📌 Project Overview

This project is part of **Day 76** of Angela Yu's **100 Days of Code: The Complete Python Pro Bootcamp**.

The goal of this project is to create a **NATO Phonetic Alphabet Converter**. The program takes a word entered by the user and converts each letter into its corresponding NATO phonetic code word.

For example:

```text
Input:
HELLO

Output:
Hotel Echo Lima Lima Oscar
````

## 🧠 What I Learned

Through this project, I practiced:

* Reading data from a CSV file using Pandas
* Working with Pandas DataFrames
* Creating dictionaries from CSV data
* Dictionary Comprehension
* List Comprehension
* Accessing dictionary values
* Taking user input
* Converting user input to uppercase
* Handling invalid input with `try` and `except`

## ⚙️ How It Works

The program reads the `nato_phonetic_alphabet.csv` file and creates a dictionary containing each alphabet letter and its NATO code word.

For example:

```python
{
    "A": "Alfa",
    "B": "Bravo",
    "C": "Charlie"
}
```

The program then takes a word from the user and converts every letter into its corresponding NATO phonetic word.

## 📂 Project Structure

```text
Day_76_NATO_Phonetic_Alphabet/
│
├── main.py
├── nato_phonetic_alphabet.csv
└── README.md
```

## 🛠️ Technologies Used

* Python
* Pandas
* CSV

## 📦 Installation

Install Pandas using:

```bash
pip install pandas
```

## ▶️ How to Run

Run the program using:

```bash
python main.py
```

Enter any word when prompted.

### Example

```text
Enter a word: PYTHON
```

Output:

```text
['Papa', 'Yankee', 'Tango', 'Hotel', 'Oscar', 'November']
```

## ⚠️ Error Handling

The program also handles invalid characters.

For example, if the user enters:

```text
HELLO123
```

the program displays:

```text
Sorry, only letters of the alphabet are allowed.
```

## 🎯 Key Learning Outcome

This project helped me understand how external CSV data can be converted into a useful Python dictionary and then used to build a practical program.

It also strengthened my understanding of **Pandas, Dictionary Comprehension, List Comprehension, and Exception Handling**.

## 📚 Course

**100 Days of Code: The Complete Python Pro Bootcamp**

---

🐍 **Day 76 Completed!**

Continuing my journey toward completing **100 Days of Code** 🚀

#100DaysOfCode #Day76 #Python #Pandas #PythonProgramming #NATOPhoneticAlphabet

