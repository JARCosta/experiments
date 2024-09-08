import streamelements
import random
import matplotlib.pyplot as plt

runs = 20

# figure, axis = plt.subplots(runs,1)

B_HIST = []
ODD_HIST = []

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

        bet_option, bet_ammount = streamelements.calculate_bet(options, BALANCE, False)

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

