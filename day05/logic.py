def calc_response(secret, guess, number_of_digits):
    exact_match_location = 0
    value_in_both_match = 0
    hist_secret = [0] * 10
    hist_guess = [0] * 10
    for i in range(number_of_digits):
        exact_match_location += secret % 10 == guess % 10
        hist_secret[secret % 10] += 1
        hist_guess[guess % 10] += 1
        guess //= 10
        secret //= 10

    for i in range(10):
        value_in_both_match += min(hist_secret[i], hist_guess[i])

    # We will count in our calculation the exact matches again
    value_in_both_match -= exact_match_location

    return "*" * exact_match_location + "+" * value_in_both_match
