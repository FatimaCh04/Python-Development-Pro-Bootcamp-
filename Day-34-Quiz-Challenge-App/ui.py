from tkinter import *


class QuizUI:

    def __init__(self, quiz):

        self.quiz = quiz

        self.window = Tk()
        self.window.title("Quiz Challenge")
        self.window.config(padx=20, pady=20)

        self.score_label = Label(text="Score: 0", font=("Arial", 14))
        self.score_label.pack()

        self.question_label = Label(
            text="",
            width=40,
            height=5,
            font=("Arial", 16),
            wraplength=300
        )
        self.question_label.pack(pady=20)

        self.true_button = Button(
            text="True",
            width=15,
            command=lambda: self.answer("True")
        )
        self.true_button.pack()

        self.false_button = Button(
            text="False",
            width=15,
            command=lambda: self.answer("False")
        )
        self.false_button.pack(pady=10)

        self.get_next_question()

        self.window.mainloop()

    def get_next_question(self):

        if self.quiz.has_questions():
            self.current_question = self.quiz.next_question()

            self.question_label.config(
                text=self.current_question.text
            )
        else:
            self.question_label.config(
                text=f"Quiz Finished!\nFinal Score: {self.quiz.score}"
            )

            self.true_button.config(state="disabled")
            self.false_button.config(state="disabled")

    def answer(self, user_answer):

        self.quiz.check_answer(
            user_answer,
            self.current_question.answer
        )

        self.score_label.config(
            text=f"Score: {self.quiz.score}"
        )

        self.get_next_question()