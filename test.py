#!/bin/python3

import math
import os
import random
import re
import sys



#
# Complete the 'game_value' function below.
#
# The function is expected to return a DOUBLE.
# The function accepts INTEGER deck_size as parameter.
# deck_size is an even non-negative integer
#


def optimal_value(N, red_count, green_count, current_value):
    if red_count == 0 and green_count == 0:
        return current_value

    if red_count > 0:
        value_if_red = optimal_value(N, red_count - 1, green_count, current_value + 1)
    else:
        value_if_red = 0

    if green_count > 0:
        value_if_green = optimal_value(N, red_count, green_count - 1, current_value - 1)
    else:
        value_if_green = 0

    return max(value_if_red, value_if_green)



def game_value(deck_size):
    # Write your code here
    # deck_size = int(input("Enter the size of the deck (even number): "))
    initial_value = 0
    red_cards = deck_size // 2
    green_cards = deck_size // 2

    result = optimal_value(deck_size, red_cards, green_cards, initial_value)
    print("Optimal value of the game:", result)


if __name__ == '__main__':
    # fptr = open(os.environ['OUTPUT_PATH'], 'w')

    deck_size = int(input())

    result = game_value(deck_size)

    # fptr.write(str(result) + '\n')

    # fptr.close()
