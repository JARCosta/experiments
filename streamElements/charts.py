import math

import numpy as np
from sklearn.decomposition import PCA
from streamElements import main
import random
import matplotlib.pyplot as plt

runs = 1

# figure, axis = plt.subplots(runs,1)

B_HIST = []
ODD_HIST = []

def odd():
    for i in range(runs):
        BALANCE = 1000
        BALANCE_HISTORY = []

        run_length = 1000

        while len(BALANCE_HISTORY) < 1000 or run_length > 0:
            BALANCE_HISTORY.append(BALANCE)

            options = {
                "win": random.randint(500, 3000),
                "lose": random.randint(500, 3000),
            }

            print("Options: {}".format(options))

            bet_option, bet_ammount = main.calculate_bet(options, BALANCE)

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
                
                win = random.random() < 0.1
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
            run_length -= 1

        # axis[i].plot(BALANCE_HISTORY)

    plt.scatter(B_HIST, ODD_HIST)

    plt.show()

import streamElements.main as main
import random
import matplotlib.pyplot as plt
import json

import matplotlib

def winrate():
    # with open('streamElements/resources/bets.txt') as f:
    #     bets = f.readlines()

    # bets_n = []
    # for i in bets:
    #     if "won the contest" in i:
    #         bets_n.append(i)
    # bets = bets_n

    # bets = [float(i.split("of all bets and ")[1].split("% of the total pot!")[0]) for i in bets]
    # chat_winrate = [1 if i < 50 else 0 for i in bets]
    
    pots = import_pots()
    win_amount = [i["win"] for i in pots]
    lose_amount = [i["lose"] for i in pots]
    result = [i["result"]=="Win" for i in pots] # 0 for lose, 1 for win
    winner_option_ratio = [i["win"]/(i["win"]+i["lose"]) if i["result"]=="Win" else i["lose"]/(i["win"]+i["lose"]) for i in pots]
    import matplotlib.pyplot as plt
    plt.hist(winner_option_ratio, bins=20)
    plt.show()

    bet_won = [1 if i < 1/3 else 0 for i in winner_option_ratio]
    rolling_average = [sum(bet_won[:i])/i for i in range(1, len(bet_won))]
    print(f"Winning on {rolling_average[-1]*100}% of the bets, on bets where the minority has less than 1/3 of the pot")
    plt.plot(rolling_average)
    bet_half = [1 if i < 0.5 else 0 for i in winner_option_ratio]
    rolling_average = [sum(bet_half[:i])/i for i in range(1, len(bet_half))]
    print(f"Winning on {rolling_average[-1]*100}% of the bets, on bets where the minority has less than 1/2 of the pot")
    plt.plot(rolling_average)
    plt.show()

    return

    

    rolling_average = [sum(bets[:i])/i for i in range(1, len(bets))] 
    winrate_rolling_average = [sum(chat_winrate[:i])/i for i in range(1, len(chat_winrate))]

    win = [1 if i < 50 else 0 for i in bets]

    print(win.count(1)/len(win))

    # line chart
    import matplotlib.pyplot as plt
    import numpy as np

    # plt.plot(bets)
    # plt.plot(rolling_average)
    # plt.plot(chat_winrate)
    plt.plot(winrate_rolling_average)

    # bar chart with average in batches of 5

    x = np.arange(0, len(bets), 5)
    print([sum(chat_winrate[i:i+5])/5 for i in x])
    y = [(sum(chat_winrate[i:i+5])/5) for i in x]

    plt.bar(x, y, width=4.5)

    plt.show()

def scatter():
    # with open("streamElements/resources/pots.txt") as f:
    #     pots = f.read().splitlines()

    # win = []
    # lose = []
    # winner = []
    # bet_won = []

    # for i in range(len(pots)):
    #     try:
    #         pots[i] = json.loads(pots[i].replace("'", "\""))
    #     except json.decoder.JSONDecodeError:
    #         if type(pots[i-1]) == dict:
    #             win.append(pots[i-1]["win"])
    #             lose.append(pots[i-1]["lose"])
    #             winner.append(pots[i] == "Win")

    #             if pots[i-1]["win"] < pots[i-1]["lose"]:
    #                 if pots[i] == "Win":
    #                     bet_won.append(True)
    #                 elif pots[i] == "Lose":
    #                     bet_won.append(False)
    #                 else:
    #                     bet_won.append(0.5)
    #             elif pots[i-1]["lose"] < pots[i-1]["win"]:
    #                 if pots[i] == "Lose":
    #                     bet_won.append(True)
    #                 elif pots[i] == "Win":
    #                     bet_won.append(False)
    #                 else:
    #                     bet_won.append(0.5)
    #             else:
    #                 bet_won.append(0.5)

    # plt.scatter(win, lose, c=bet_won, s=100)
    # plt.scatter(win, lose, c=winner, s=50)
    # plt.xlabel("Win")
    # plt.ylabel("Lose")
    # plt.colorbar(label="Win")
    # plt.show()

    pots = import_pots()
    # for i in range(len(pots)):
    #     pots[i]["win"] = math.log10(pots[i]["win"]+1)
    #     pots[i]["lose"] = math.log10(pots[i]["lose"]+1)
    
    win_amount = [i["win"] for i in pots]
    lose_amount = [i["lose"] for i in pots]
    result = [i["result"]=="Win" for i in pots] # 0 for lose, 1 for win
    # # theoretical_bet = [main.calculate_bet(i, 1000) for i in pots]

    def regerssion_line(x_axis, y_axis):
        pca = PCA(n_components=1)
        pca.fit(np.array([x_axis, y_axis]).T)
        line = pca.components_
        center = [np.mean(x_axis), np.mean(y_axis)]
        incline = line[0][1]/line[0][0]
        r = max([max(i["win"], i["lose"]) for i in pots]) - center[0]
        x_win = [0, center[0]+r]
        y_win = [center[1]-(center[0])*incline,center[1]+r*incline]
        
        return x_win, y_win

    win_amount_on_win = [i["win"] for i in pots if i["result"]=="Win"]
    lose_amount_on_win = [i["lose"] for i in pots if i["result"]=="Win"]
    x, y = regerssion_line(win_amount_on_win, lose_amount_on_win)
    plt.plot(x, y, c="green")

    win_amount_on_lose = [i["win"] for i in pots if i["result"]=="Lose"]
    lose_amount_on_lose = [i["lose"] for i in pots if i["result"]=="Lose"]
    x, y = regerssion_line(win_amount_on_lose, lose_amount_on_lose)
    plt.plot(x, y, c="red")

    x, y = regerssion_line([-2, 2], [-1, 1])
    plt.plot(x, y, c="black")
    x, y = regerssion_line([-1, 1], [-2, 2])
    plt.plot(x, y, c="black")


    plt.scatter(win_amount_on_win, lose_amount_on_win, c="green", s=50) # amount bet when result=win
    plt.scatter(win_amount_on_lose, lose_amount_on_lose, c="red", s=50) # amount bet when result=lose
    
    winning_bet_win = [i["win"] for i in pots if (i["win"] < 0.5*i["lose"] and i["result"]=="Win") or (i["lose"] < 0.5*i["win"] and i["result"]=="Lose")]
    winning_bet_lose = [i["lose"] for i in pots if (i["win"] < 0.5*i["lose"] and i["result"]=="Win") or (i["lose"] < 0.5*i["win"] and i["result"]=="Lose")]
    plt.scatter(winning_bet_win, winning_bet_lose, c="yellow", s=25)
    losing_bet_win = [i["win"] for i in pots if (i["win"] < 0.5*i["lose"] and i["result"]=="Lose") or (i["lose"] < 0.5*i["win"] and i["result"]=="Win")]
    losing_bet_lose = [i["lose"] for i in pots if (i["win"] < 0.5*i["lose"] and i["result"]=="Lose") or (i["lose"] < 0.5*i["win"] and i["result"]=="Win")]
    plt.scatter(losing_bet_win, losing_bet_lose, c="black", s=25)

    betting_percentage = (len(winning_bet_win)+len(losing_bet_win))/len(pots)
    print(f"Betting on {round(betting_percentage*100, 2)}% of the time")

    winning_bet_percentage = len(winning_bet_win)/(len(winning_bet_win)+len(losing_bet_win))
    print(f"Winning on {round(winning_bet_percentage*100, 2)}% of the bets")
    print(f"Odd needed for the break-even: {round(1/winning_bet_percentage, 2)}")

    plt.xlabel("Amount bet on Win")
    plt.ylabel("Amount bet on Lose")
    plt.show()



def import_pots():
    with open("streamElements/resources/pots.txt", "r") as f:
        pots = f.read().splitlines()
        
    # look for pairs "{'Win': x, 'Lose': y}" followed by "Win" or "Lose"
    pot = {
        "win": None,
        "lose": None,
        "result": ""
    }
    pot_list = []
    for i in range(len(pots)):
        try:
            pots[i] = json.loads(pots[i].replace("'", "\""))
            pot = pots[i]
        except json.decoder.JSONDecodeError:
            if type(pots[i-1]) == dict:
                pot["result"] = pots[i]
                if pot["win"] != None:
                    pot_list.append(pot)
    return pot_list
        
        
def simulator(distribution=None):
    if distribution == None:
        Exception("TODO: No distribution provided")

