from streamElements import main
import random
import matplotlib.pyplot as plt

runs = 20

# figure, axis = plt.subplots(runs,1)

B_HIST = []
ODD_HIST = []

def odd():
    for i in range(runs):
        BALANCE = 1000
        BALANCE_HISTORY = []

        while len(BALANCE_HISTORY) < 1000:
            BALANCE_HISTORY.append(BALANCE)

            options = {
                "win": random.randint(500, 3000),
                "lose": random.randint(500, 3000),
            }

            print("Options: {}".format(options))

            bet_option, bet_ammount = main.calculate_bet(options, BALANCE, False)

            print_message = ""

            if bet_ammount > 0 and bet_ammount <= BALANCE:
                print_message += "Betting {} on {}\n".format(bet_ammount, bet_option)

                BALANCE -= bet_ammount

                oposite_option = "win" if bet_option == "lose" else "lose"

                pot_ratio = bet_ammount / (options[bet_option] + bet_ammount)
                bet_profit = options[oposite_option] * pot_ratio
                bet_return = bet_ammount + bet_profit
                bet_odd = (bet_profit / bet_ammount) + 1

                print_message += "The odd for this bet is {}\n".format(bet_odd)
                print_message += "The profit for this bet is {}\n".format(bet_profit)
                print_message += "The return for this bet is {}\n".format(bet_return)
                
                win = random.random() < 0.2
                print_message += "You {}!\n".format("won" if win else "lost")

                if win:
                    BALANCE += round(bet_return)
                
                B_HIST.append(options[bet_option] / options[oposite_option])
                ODD_HIST.append(bet_odd)

                # if pot_ratio > 0.5:
                #     breakpoint()
            else:
                print_message += "You didn't bet\n"

            print_message += "You now have {} points\n".format(BALANCE)

            print(print_message)
            BALANCE += 100

        # axis[i].plot(BALANCE_HISTORY)

    plt.scatter(B_HIST, ODD_HIST)

    plt.show()

import streamElements.main as main
import random
import matplotlib.pyplot as plt
import json

import matplotlib

def winrate():
    with open('streamElements/resources/bets.txt') as f:
        bets = f.readlines()

    bets_n = []
    for i in bets:
        if "won the contest" in i:
            bets_n.append(i)
    bets = bets_n

    bets = [float(i.split("of all bets and ")[1].split("% of the total pot!")[0]) for i in bets]
    winrate = [1 if i < 50 else 0 for i in bets]
    rolling_average = [sum(bets[:i])/i for i in range(1, len(bets))] 
    winrate_rolling_average = [sum(winrate[:i])/i for i in range(1, len(winrate))]

    win = [1 if i < 50 else 0 for i in bets]

    print(win.count(1)/len(win))

    # line chart
    import matplotlib.pyplot as plt
    import numpy as np

    # plt.plot(bets)
    # plt.plot(rolling_average)
    # plt.plot(winrate)
    plt.plot(winrate_rolling_average)

    # bar chart with average in batches of 5

    x = np.arange(0, len(bets), 5)
    print([sum(winrate[i:i+5])/5 for i in x])
    y = [(sum(winrate[i:i+5])/5) for i in x]

    plt.bar(x, y, width=4.5)

    plt.show()

def scatter():
    with open("streamElements/resources/pots.txt") as f:
        pots = f.read().splitlines()

    win = []
    lose = []
    winner = []
    bet_won = []

    for i in range(len(pots)):
        try:
            pots[i] = json.loads(pots[i].replace("'", "\""))
        except json.decoder.JSONDecodeError:
            if type(pots[i-1]) == dict:
                win.append(pots[i-1]["win"])
                lose.append(pots[i-1]["lose"])
                winner.append(pots[i] == "Win")

                if pots[i-1]["win"] < pots[i-1]["lose"]:
                    if pots[i] == "Win":
                        bet_won.append(True)
                    elif pots[i] == "Lose":
                        bet_won.append(False)
                    else:
                        bet_won.append(0.5)
                elif pots[i-1]["lose"] < pots[i-1]["win"]:
                    if pots[i] == "Lose":
                        bet_won.append(True)
                    elif pots[i] == "Win":
                        bet_won.append(False)
                    else:
                        bet_won.append(0.5)
                else:
                    bet_won.append(0.5)

    plt.scatter(win, lose, c=bet_won, s=100)
    plt.scatter(win, lose, c=winner, s=50)
    plt.xlabel("Win")
    plt.ylabel("Lose")
    plt.colorbar(label="Win")
    plt.show()

