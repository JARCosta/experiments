
import datetime
from math import sqrt
import requests
import time
import threading

import telegramBot
import twitch_message_sender

balance_url = "https://api.streamelements.com/kappa/v2/points/5a2ae33308308f00016e684e/el_pipow?providerId=462756951"
bets_url = "https://api.streamelements.com/kappa/v2/contests/5a2ae33308308f00016e684e/active"

CHAT_ID = "6449165312"

def get_balance():
    response = requests.get(balance_url)
    response_json = response.json()
    global BALANCE
    BALANCE = int(response_json['points'])
    return response_json['points']

def decrease_variable_delay(amount=0.1):
    amount = round(amount, 2)
    if amount > 0:
        global VARIABLE_DELAY
        VARIABLE_DELAY = round(VARIABLE_DELAY - amount, 2)
        with open('resources/variable_delay.txt', 'w') as f:
            f.write(str(VARIABLE_DELAY) + "\n")
        telegram_message = "Variable delay decreased by {} to {}".format(amount, VARIABLE_DELAY)
        threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
        print(telegram_message, end="\n\n")

def increase_variable_delay(amount=0.1):
    amount = round(amount, 2)
    if amount > 0:
        global VARIABLE_DELAY
        VARIABLE_DELAY = round(VARIABLE_DELAY + amount, 2)
        with open('resources/variable_delay.txt', 'w') as f:
            f.write(str(VARIABLE_DELAY) + "\n")
        telegram_message = "Variable delay increased by {} to {}".format(amount, VARIABLE_DELAY)
        threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
        print(telegram_message, end="\n\n")

BALANCE = get_balance()
REFERENCE_DELAY = 1
with open('resources/variable_delay.txt', 'r') as f:
    VARIABLE_DELAY = float(f.read())
with open('resources/test.txt', 'w') as f:
    pass

def calculate_bet(options):

    for i in options.keys():
        options[i] += 1

    bet_option = "win" if options["win"] < options["lose"] else "lose"
    oposite_option = "lose" if bet_option == "win" else "win"

    current_balance_ratio_on_our_option = options[bet_option] / options[oposite_option]

    our_bet_ratio = -current_balance_ratio_on_our_option + sqrt(current_balance_ratio_on_our_option)

    bet_ammount = our_bet_ratio * options[oposite_option]
    bet_ammount = round(bet_ammount)

    bet_ratio = bet_ammount/(options[bet_option]+bet_ammount)

    print("Betting {} on {}, representing {}% of the winning pot".format(bet_ammount, bet_option, round(100*bet_ratio)))
    return bet_option, round(bet_ammount, -1)

WST, WS = None, None

def reconnect():
    global WST, WS
    twitch_message_sender.close(WST, WS)
    WST, WS = twitch_message_sender.launch()

def get_bets():

    WST, WS = twitch_message_sender.launch()
    try:
        global VARIABLE_DELAY
        while True:
            response = requests.get(bets_url)
            response_json = response.json()
            
            if response_json["contest"] == None:
                print("No contest found")
                print("\n")
                time.sleep(60)
                continue
            
            start = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=1)
            end = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=1, minutes=response_json["contest"]["duration"])
            now = datetime.datetime.now()

            print(start)
            print(end)
            print(now)

            if start < now < end: # Bets are open
                if (end - now).total_seconds() < 5: # Time to bet
                    options = {option["command"]: int(option["totalAmount"]) for option in response_json["contest"]["options"]}
                    bet_option, bet_ammount = calculate_bet(options)
                    global BALANCE
                    bet_ammount = BALANCE if bet_ammount > BALANCE else bet_ammount
                    oposite_option = "lose" if bet_option == "win" else "win"
                    return_ammount = options[oposite_option] * (bet_ammount/(options[bet_option]+bet_ammount))
                    odd = (return_ammount + bet_ammount)/bet_ammount
                    if bet_ammount > 0 and odd > 2.5: # and BALANCE > bet_ammount
                        twitch_message_sender.bet(WS, bet_option, str(bet_ammount) if BALANCE > bet_ammount else "all")

                    if (end - now).total_seconds() > REFERENCE_DELAY: # betting too early
                        decrease_variable_delay(((end - now).total_seconds() - REFERENCE_DELAY)/4)
                    if (end - now).total_seconds() < REFERENCE_DELAY: # betting too late
                        increase_variable_delay((REFERENCE_DELAY - (end - now).total_seconds())/4)

                    telegram_message = "Time to place your bets\n"
                    telegram_message += "There were still {} seconds left\n".format(round((end - now).total_seconds(), 2))
                    telegram_message += "The pot is at {} points\n".format(response_json["contest"]["totalAmount"])
                    for option in response_json["contest"]["options"]:
                        telegram_message += "Option {}: {} points\n".format(option["title"], option["totalAmount"])
                    telegram_message += "\n"
                    telegram_message += "Betting {} on {}, representing {}% of the winning pot\n".format(bet_ammount, bet_option, round(100*bet_ammount/(options[bet_option]+bet_ammount)))
                    telegram_message += "The odd of this bet is {}\n".format(round(odd, 2))
                    threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
                    print(telegram_message, end="\n\n")

                    time.sleep(10)
                    continue
                
                else: # Not time to bet yet
                    telegram_message = "Contest found\n"
                    # telegram_message += "Time left: {} seconds\n".format(round((end - now).total_seconds()))
                    telegram_message += "Follow it through: {}\n".format("https://streamelements.com/runah/contest/" + response_json["contest"]["_id"])
                    telegram_message += "You have {} points\n".format(get_balance())
                    # time.sleep(10)
                    # players = faceit.get_latest_match_players_list("DaddyRunah")
                    # for team in players:
                    #     telegram_message += "Team: {}\n".format(players.index(team)+1)
                    #     for player in team:
                    #         telegram_message += "{}\n".format(player)
                    threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
                    print(telegram_message, end="\n\n")

                    time.sleep((end - now).total_seconds() - VARIABLE_DELAY)
                    continue
            
            elif start < end < now: # Bets are closed
                if (now - end).total_seconds() < 5: # Bets just closed (trying to bet too late)
                    increase_variable_delay((now - end).total_seconds())
                    print((now - end).total_seconds())

                print("Bets closed {}:{}:{} ago ({} s)".format( int((now - end).total_seconds()//3600),int((now - end).total_seconds()//60), int((now - end).total_seconds()%60), round((now - end).total_seconds(), 2)))
                print("The pot is at {} points".format(response_json["contest"]["totalAmount"]))
                for option in response_json["contest"]["options"]:
                    print("{} points were bet on {}".format(option["totalAmount"], option["title"]))
                print("You have {} points".format(get_balance()))
                print("\n")

                time.sleep(120)
                continue

            else: # This should never happen
                telegram_message = "Bets are not open yet\n"
                telegram_message += "Something is off\n"
                telegram_message += "Check out what's going on"
                threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
                print(telegram_message, end="\n\n")

                time.sleep(120)
                continue

    except KeyboardInterrupt:
        twitch_message_sender.close(WST, WS)
    except Exception as e:
        with open('resources/test.txt', 'a') as f:
            f.write("aaaaaaaaaaaaa\n")
            f.write(str(datetime.datetime.now()) + "\n")
            f.write(str(e) + "\n")
        telegram_message = "Error: " + str(e)
        telegramBot.sendMessage(telegram_message)



if __name__ == "__main__":
    get_bets()

