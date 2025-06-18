from math import floor




win = 10000
lose = 7500
# b = lose/(win+lose)

pot = {"win": win, "lose": lose}
odds = {"win": 0.6, "lose": 0.4}
bet = {
    "option": "lose",
    "ammount": 1000
}

def ret(pot:dict, bet:dict):
    pot_percentage = bet["ammount"]/(pot[bet["option"]]+bet["ammount"])
    return pot_percentage*(sum(pot.values()) + bet["ammount"])

def profit(pot:dict, bet:dict):
    return ret(pot, bet) - bet["ammount"]

def bet_odd(pot:dict, bet:dict):
    return ret(pot, bet)/bet["ammount"]

def predicted_odd(bet:dict, odds:dict):
    return 1/odds[bet["option"]]

def expected_value(pot:dict, bet:dict, odds:dict):
    return ret(pot, bet) * odds[bet["option"]] - bet["ammount"] * (1-odds[bet["option"]])


print(f"ret: {ret(pot, bet)}(-{bet['ammount']}), bet_odd: {bet_odd(pot, bet)}, predicted_odd: {predicted_odd(bet, odds)}")
print(f"expected_value: {expected_value(pot, bet, odds)}")

