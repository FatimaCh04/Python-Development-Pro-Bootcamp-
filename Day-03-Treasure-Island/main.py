print(r'''
*******************************************************************************
          |                   |                  |                     |
 _________|________________.=""_;=.______________|_____________________|_______
|                   |  ,-"_,=""     `"=.|                  |
|___________________|__"=._o`"-._        `"=.______________|___________________
          |                `"=._o`"=._      _`"=._                     |
 _________|_____________________:=._o "=._."_.-="'"=.__________________|_______
|                   |    __.--" , ; `"=._o." ,-"""-._ ".   |
|___________________|_."  ,. .` ` `` ,  `"-._"-._   ". '__|___________________
          |           |o`"=._` , "` `; .". ,  "-._"-._; ;              |
 _________|___________| ;`-.o`"=._; ."` ` '.`\\` . "-._ /_______________|_______
|                   | |o;    `"-.o`"=._``  '` " ,__.--o;   |
|___________________|_| ;     (#) `-.o `"=.`_.--"_o.-; ;___|___________________
*******************************************************************************
''')

print("Welcome to Treasure Island.")
print("Your mission is to find the treasure.\n")

choice1 = input('You are at a crossroad. Type "left" or "right": ').lower()

if choice1 == "left":
    choice2 = input('You arrive at a lake. Type "wait" to wait for a boat or "swim" to swim across: ').lower()

    if choice2 == "wait":
        choice3 = input('You arrive at a house with 3 doors. Choose "red", "yellow", or "blue": ').lower()

        if choice3 == "yellow":
            print("🎉 Congratulations! You found the treasure. You Win!")
        elif choice3 == "red":
            print("🔥 Burned by fire. Game Over.")
        elif choice3 == "blue":
            print("🐍 Eaten by beasts. Game Over.")
        else:
            print("🚪 Wrong door. Game Over.")

    else:
        print("🐊 Attacked by a crocodile. Game Over.")

else:
    print("🕳️ You fell into a hole. Game Over.")