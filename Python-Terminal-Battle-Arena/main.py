import random

# ===============================
# Python Terminal Battle Arena
# ===============================

# -------- Player Dictionary --------
player = {
    "name": "Hero",
    "stats": {
        "health": 100,
        "max_health": 100,
        "attack": 20,
        "defense": 10,
        "potions": 3,
        "gold": 0
    },
    "log": {
        "enemies_defeated": 0,
        "potions_used": 0,
        "gold_earned": 0
    }
}

# -------- Enemy Dictionaries --------
waves = [
    [
        {
            "name": "Goblin 1",
            "stats": {
                "health": 50,
                "attack": 12,
                "defense": 5,
                "gold": 20
            }
        },
        {
            "name": "Goblin 2",
            "stats": {
                "health": 50,
                "attack": 12,
                "defense": 5,
                "gold": 20
            }
        }
    ],
    [
        {
            "name": "Orc 1",
            "stats": {
                "health": 80,
                "attack": 18,
                "defense": 8,
                "gold": 40
            }
        },
        {
            "name": "Orc 2",
            "stats": {
                "health": 80,
                "attack": 18,
                "defense": 8,
                "gold": 40
            }
        }
    ],
    [
        {
            "name": "Dragon",
            "stats": {
                "health": 180,
                "attack": 30,
                "defense": 15,
                "gold": 100
            }
        }
    ]
]


# ===============================
# Functions
# ===============================

def attack_enemy(attacker, defender):
    rand = random.randint(0, 10)

    if rand < 2:
        print(f"\n{attacker['name']} MISSED the attack!")
        return 0

    damage = (
        attacker["stats"]["attack"]
        - defender["stats"]["defense"]
        + rand
    )

    if damage < 0:
        damage = 0

    if rand > 8:
        damage *= 2
        print(">>> CRITICAL HIT! <<<")

    defender["stats"]["health"] -= damage

    if defender["stats"]["health"] < 0:
        defender["stats"]["health"] = 0

    print(f"{attacker['name']} dealt {damage} damage!")

    return damage


def use_potion():
    if player["stats"]["potions"] <= 0:
        print("No potions left!")
        return

    if player["stats"]["health"] == player["stats"]["max_health"]:
        print("Health already full!")
        return

    player["stats"]["health"] += 30

    if player["stats"]["health"] > player["stats"]["max_health"]:
        player["stats"]["health"] = player["stats"]["max_health"]

    player["stats"]["potions"] -= 1
    player["log"]["potions_used"] += 1

    print("Potion used! +30 Health")


def shop():
    while True:

        print("\n========== SHOP ==========")
        print("Gold:", player["stats"]["gold"])
        print("1. Buy Attack +5 (30 Gold)")
        print("2. Buy Potion (20 Gold)")
        print("3. Exit Shop")

        choice = input("Choose: ")

        if choice == "1":
            if player["stats"]["gold"] >= 30:
                player["stats"]["gold"] -= 30
                player["stats"]["attack"] += 5
                print("Attack increased!")
            else:
                print("Not enough gold.")

        elif choice == "2":
            if player["stats"]["gold"] >= 20:
                player["stats"]["gold"] -= 20
                player["stats"]["potions"] += 1
                print("Potion purchased!")
            else:
                print("Not enough gold.")

        elif choice == "3":
            break

        else:
            print("Invalid Input!")


def display_status(enemy):
    print("\n----------------------------")
    print(
        f"Player HP : {player['stats']['health']}/{player['stats']['max_health']}"
    )
    print("Potions  :", player["stats"]["potions"])
    print("Gold     :", player["stats"]["gold"])
    print("----------------------------")
    print(f"{enemy['name']} HP :", enemy["stats"]["health"])
    print("----------------------------")


def final_report():
    print("\n")
    print("=" * 46)
    print("             FINAL REPORT")
    print("=" * 46)
    print("+----------------------+-----------+")
    print("| Enemies Defeated     | {:9} |".format(player["log"]["enemies_defeated"]))
    print("| Potions Used         | {:9} |".format(player["log"]["potions_used"]))
    print("| Total Gold Earned    | {:9} |".format(player["log"]["gold_earned"]))
    print("| Gold Remaining       | {:9} |".format(player["stats"]["gold"]))
    print("| Final Attack Power   | {:9} |".format(player["stats"]["attack"]))
    print("+----------------------+-----------+")
    print("=" * 46)


# ===============================
# Game Start
# ===============================

print("=" * 45)
print("      THE ULTIMATE CLI BATTLE ARENA")
print("=" * 45)

wave_number = 1

for wave in waves:

    print(f"\n========== WAVE {wave_number} ==========")

    for enemy in wave:

        print(f"\nA wild {enemy['name']} appeared!")

        while enemy["stats"]["health"] > 0:

            if player["stats"]["health"] <= 0:
                print("\nGame Over!")
                final_report()
                quit()

            display_status(enemy)

            print("\n1. Attack")
            print("2. Heal")
            print("3. Run")

            choice = input("Enter choice: ")

            if choice == "1":

                attack_enemy(player, enemy)

                if enemy["stats"]["health"] <= 0:
                    print(f"{enemy['name']} defeated!")

                    gold = enemy["stats"]["gold"]

                    player["stats"]["gold"] += gold
                    player["log"]["gold_earned"] += gold
                    player["log"]["enemies_defeated"] += 1

                    print(f"You earned {gold} Gold!")

                    break

                print(f"\n{enemy['name']} attacks!")

                attack_enemy(enemy, player)

            elif choice == "2":

                use_potion()

                print(f"\n{enemy['name']} attacks!")

                attack_enemy(enemy, player)

            elif choice == "3":
                print("You escaped from battle!")
                final_report()
                quit()

            else:
                print("Invalid Input, try again.")

    if wave_number < len(waves):
        print(f"\nWave {wave_number} cleared!")
        shop()

    wave_number += 1

# ===============================
# Ending
# ===============================

if player["stats"]["health"] > 0:
    print("\nCongratulations!")
    print("You defeated the Dragon and won the game!")

final_report()