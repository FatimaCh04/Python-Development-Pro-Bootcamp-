from question_model import Question
from quiz_brain import QuizBrain
from ui import QuizUI
from data import question_data

question_bank = []

for item in question_data:
    question = Question(item["question"], item["answer"])
    question_bank.append(question)

quiz = QuizBrain(question_bank)

QuizUI(quiz)