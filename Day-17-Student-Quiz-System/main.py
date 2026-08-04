class Quiz:

    def __init__(self, questions):
        self.question_number = 0
        self.score = 0
        self.questions = questions

    def next_question(self):
        current = self.questions[self.question_number]

        answer = input(
            f"Q{self.question_number + 1}: {current.question} "
        ).strip().upper()

        if answer == current.answer:
            print("✅ Correct!\n")
            self.score += 1
        else:
            print(f"❌ Wrong! Correct answer: {current.answer}\n")

        self.question_number += 1

    def still_has_questions(self):
        return self.question_number < len(self.questions)