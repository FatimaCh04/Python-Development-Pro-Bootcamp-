def show_winner(votes):
    winner = max(votes, key=votes.get)
    print("\n========== RESULT ==========")
    print(f"Winner: {winner}")
    print(f"Votes: {votes[winner]}")


votes = {}

print("===== Student Voting System =====")

while True:
    name = input("\nEnter candidate name: ")

    if name in votes:
        votes[name] += 1
    else:
        votes[name] = 1

    choice = input("Add another vote? (yes/no): ").lower()

    if choice == "no":
        break

show_winner(votes)

print("\nAll Votes")

for candidate, total in votes.items():
    print(f"{candidate}: {total}")