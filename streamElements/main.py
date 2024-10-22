
import datetime
from math import sqrt
import random
import traceback
import requests
import time
import threading

import websocket

from streamElements import telegramBot
from streamElements import twitch_message_sender

balance_url = "https://api.streamelements.com/kappa/v2/points/5a2ae33308308f00016e684e/el_pipow?providerId=462756951"
bets_url = "https://api.streamelements.com/kappa/v2/contests/5a2ae33308308f00016e684e/active"

CHAT_ID = "6449165312"
telegram_message = ""

def get_balance():
    response = requests.get(balance_url)
    if response.status_code != 200:
        return get_balance()
    response_json = response.json()
    global BALANCE
    BALANCE = int(response_json['points'])
    return response_json['points']

def send_message(message = None):
    if message != None:
        threading.Thread(target=telegramBot.sendMessage, args=(message,)).start()
        print(message, end="\n\n")
    else:
        global telegram_message
        if telegram_message in [None, ""]:
            print("No message to send")
        threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
        print(telegram_message, end="\n\n")
        telegram_message = ""

def decrease_variable_delay(amount=0.1):
    amount = round(amount, 2)
    if amount > 0:
        global VARIABLE_DELAY, telegram_message
        VARIABLE_DELAY = round(VARIABLE_DELAY - amount, 2)
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(VARIABLE_DELAY) + "\n")
        telegram_message += "Variable delay decreased by {} to {}\n".format(amount, VARIABLE_DELAY)

def increase_variable_delay(amount=0.1):
    amount = round(amount, 2)
    if amount > 0:
        global VARIABLE_DELAY, telegram_message
        VARIABLE_DELAY = round(VARIABLE_DELAY + amount, 2)
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(VARIABLE_DELAY) + "\n")
        telegram_message += "Variable delay increased by {} to {}\n".format(amount, VARIABLE_DELAY)

BALANCE = get_balance()
REFERENCE_DELAY = 1
with open('streamElements/resources/variable_delay.txt', 'r') as f:
    VARIABLE_DELAY = float(f.read())
with open('streamElements/resources/test.txt', 'w') as f:
    pass

def opt_bet(options, balance):
    little_option = "win" if options["win"] < options["lose"] else "lose"
    little_option_ammount = options[little_option]
    if little_option_ammount == 0:
        return little_option, 1

    oposite_option = "lose" if little_option == "win" else "win"
    oposite_option_ammount = options[oposite_option]

    b = little_option_ammount / oposite_option_ammount

    # opt_bet_ratio = -b + sqrt(b)
    opt_bet_ratio = (sqrt(2*b)-2*b)/2
    if opt_bet_ratio < 0:
        return little_option, 0
    
    opt_bet_ammount = round(opt_bet_ratio * oposite_option_ammount, -1)
    return little_option, opt_bet_ammount

def calculate_bet(options, balance):

    global telegram_message
    telegram_message += "The pot is at {} points\n".format(options["win"] + options["lose"])
    for i in options.keys():
        telegram_message += "\tOption {}: {} points\n".format(i, options[i])
    telegram_message += "\n"
    telegram_message += "You have {} points\n".format(balance)
    telegram_message += "\n"

    bet_option, opt_bet_ammount = opt_bet(options, balance)
    oposite_option = "lose" if bet_option == "win" else "win"

    b = options[bet_option] / options[oposite_option]
    telegram_message += "b = {}\n\n".format(round(b, 3))
    
    if opt_bet_ammount > 0:
        telegram_message += "The optimal bet is {} points\n".format(round(opt_bet_ammount))
        opt_pot_ratio = opt_bet_ammount/(options[bet_option]+opt_bet_ammount)
        telegram_message += "Which represents {}% of the winning pot\n".format(round(100*opt_pot_ratio))
        opt_bet_profit = opt_pot_ratio * options[oposite_option]
        telegram_message += "Profits {} points\n".format(round(opt_bet_profit))
        opt_bet_return = opt_bet_ammount + opt_bet_profit
        telegram_message += "Returns {} points\n".format(round(opt_bet_return))
        opt_bet_odd = opt_bet_return / opt_bet_ammount
        telegram_message += "Has an odd of {}\n".format(round(opt_bet_odd, 2))

    bet_ammount = opt_bet_ammount

    return bet_option, bet_ammount

WST, WS = None, None

def reconnect(wst, ws):
    global telegram_message
    twitch_message_sender.close(wst, ws)
    wst, ws = twitch_message_sender.launch()
    telegram_message += "Reconnected to Twitch\n"
    return wst, ws

def check_websocket(wst, ws):
    try:
        twitch_message_sender.ping(ws)
    except (websocket._exceptions.WebSocketConnectionClosedException, ):
        print("Handled exception:\n", traceback.format_exc())
        return reconnect(wst, ws)
    return wst, ws

def get_bets():
    global WST, WS
    WST, WS = twitch_message_sender.launch()

    try:
        global VARIABLE_DELAY, telegram_message
        while True:
            response = requests.get(bets_url)
            while response.status_code != 200:
                response = requests.get(bets_url)
            response_json = response.json()
            
            if response_json["contest"] == None:
                print(datetime.datetime.now().strftime('%H:%M')+" - No contest found")
                print("\n")

                time.sleep(60)
                continue
            
            start = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=1)
            end = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=1, minutes=response_json["contest"]["duration"])
            now = datetime.datetime.now()

            # print(start)
            # print(end)
            # print(now)

            if start < now < end: # Bets are open
                if (end - now).total_seconds() < 5: # Time to bet
                    
                    global BALANCE, telegram_message
                    telegram_message += "Time to place your bets\n"
                    telegram_message += "There were still {} seconds left\n\n".format(round((end - now).total_seconds(), 2))
                    
                    options = {option["command"]: int(option["totalAmount"]) for option in response_json["contest"]["options"]}
                    bet_option, bet_ammount = calculate_bet(options, BALANCE)
                    if bet_ammount > 0:
                        bet_ammount = BALANCE if bet_ammount > BALANCE else bet_ammount
                        twitch_message_sender.send(WS, "runah", f"!bet {bet_option} {str(int(bet_ammount)) if BALANCE > bet_ammount else 'all'}")
                        
                        if (end - now).total_seconds() > REFERENCE_DELAY: # betting too early
                            decrease_variable_delay(((end - now).total_seconds() - REFERENCE_DELAY)/4)
                        if (end - now).total_seconds() < REFERENCE_DELAY: # betting too late
                            increase_variable_delay((REFERENCE_DELAY - (end - now).total_seconds())/4)

                    send_message()

                    with open('streamElements/resources/pots.txt', 'a') as f:
                        f.write(str(options) + "\n")

                    time.sleep(10)
                    continue
                
                else: # Not time to bet yet
                    telegram_message += "Contest found\n"
                    # telegram_message += "Time left: {} seconds\n".format(round((end - now).total_seconds()))
                    telegram_message += "Follow it through: {}\n".format("https://streamelements.com/runah/contest/" + response_json["contest"]["_id"])
                    telegram_message += "You have {} points\n".format(get_balance())
                    # time.sleep(10)
                    # players = faceit.get_latest_match_players_list("DaddyRunah")
                    # for team in players:
                    #     telegram_message += "Team: {}\n".format(players.index(team)+1)
                    #     for player in team:
                    #         telegram_message += "{}\n".format(player)
                    WST, WS = check_websocket(WST, WS)
                    send_message()

                    if (end - now).total_seconds() - VARIABLE_DELAY > 0:
                        time.sleep((end - now).total_seconds() - VARIABLE_DELAY)
                    else:
                        print( end , "-", now, "-", VARIABLE_DELAY)
                        decrease_variable_delay((VARIABLE_DELAY - (end - now).total_seconds())/4)
                    continue
            
            elif start < end < now: # Bets are closed
                if (now - end).total_seconds() < 5: # Bets just closed (trying to bet too late)
                    increase_variable_delay((now - end).total_seconds())
                    telegram_message += f"Bets closed {round((now - end).total_seconds(), 2)} s ago\n"
                    send_message()

                print("Bets closed {}:{}:{} ago ({} s)".format( int((now - end).total_seconds()//3600),int((now - end).total_seconds()//60), int((now - end).total_seconds()%60), round((now - end).total_seconds(), 2)))
                print("The pot is at {} points".format(response_json["contest"]["totalAmount"]))
                for option in response_json["contest"]["options"]:
                    print("{} points were bet on {}".format(option["totalAmount"], option["title"]))
                print("\n")

                time.sleep(120)
                continue

            else: # This should never happen
                telegram_message += "Bets are not open yet\n"
                telegram_message += "Something is off\n"
                telegram_message += "Check out what's going on"
                send_message()

                time.sleep(1)
                continue
    except KeyboardInterrupt:
        with open('streamElements/resources/latest_error.txt', 'w') as f:
            pass
    except Exception as e:
        telegram_message += "Error:\n"
        telegram_message += datetime.datetime.now().strftime('%H:%M') + "\n"
        telegram_message += traceback.format_exc()
        send_message()
        with open('streamElements/resources/latest_error.txt', 'w') as f:
            f.write(telegram_message)



if __name__ == "__main__":
    get_bets()

