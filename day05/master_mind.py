import random
from logic import calc_response


INSTRUCTIONS = """
The computer "thinks" a number with 4 different digits.
The user guesses which digits.
For every digit that matched both in value, and in location the computer gives a *.
For every digit that matches in value, but not in space the computer gives you a +.
The user tries to guess the given number in as few guesses as possible.
"""


MAIN_HELP = """
Master Mind game!
s - start a new game
i - print instructions
h - print this menu
q - quit
"""


GAME_HELP = """
q - resign game
h - print this menu
number - a guess
"""

NUMBER_0F_DIGITS = 4


def run_game(number_of_digits):
    max_val = 10**number_of_digits
    secret = random.randrange(max_val)
    # Initial value that for sure will be different than the computer number
    guess = max_val
    resign = False
    guess_number = 0

    print("The computer got a number!")
    while guess != secret and not resign:
        guess_number += 1
        raw_in = input(f"{guess_number}\t>>> ").strip()
        try:
            guess = int(raw_in)
            if guess < 0 or guess >= max_val:
                print(f"Please enter a number between 0 and {max_val - 1}")
                continue
        except ValueError:
            if raw_in == "h":
                print(GAME_HELP)
            elif raw_in == "q":
                resign = True
            else:
                print("Invalid option, use h for help")
                print(GAME_HELP)
            continue


        response = calc_response(secret, guess, number_of_digits)
        format_ = f"{{guess:0{number_of_digits}}} {{response:{number_of_digits}}}"
        print(format_.format(guess=guess, response=response))
    secret_format = f"{{secret:0{number_of_digits}}}"
    response = f"{'Succeeded' if guess == secret else 'Resigned'} after {guess_number} guesses, secret was {secret_format.format(secret=secret)}"
    print(response)
    return guess_number if not resign else None


def main():
    best_score = None
    game_on = True
    print("Welcome to Master Mind!")

    while game_on:
        choice = input("Please enter your input: (h for help)\n>> ").strip()
        new_score = None
        if choice == "s":
            new_score = run_game(NUMBER_0F_DIGITS)
            if new_score is not None:
                if best_score is None or new_score < best_score:
                    best_score = new_score
                    print(f"New best score: {best_score} guesses!")
                else:
                    print(f"Best score remains: {best_score} guesses.")
        elif choice == "i":
            print(INSTRUCTIONS)
        elif choice == "h":
            print(MAIN_HELP)
        elif choice == "q":
            print("Thank you for playing Master Mind! Goodbye!")
            game_on = False
            break
        else:
            print("Invalid choice. Please try again.")
            print(MAIN_HELP)


if __name__ == "__main__":
    main()
