
import datetime
import json
from math import sqrt
import random
import traceback
import requests
import time
import threading

import websocket

from streamElements import telegramBot
from streamElements import twitch_message_sender

CHAT_ID = "6449165312"
telegram_message = ""

def get_balance(username:str="El_Pipow") -> int:
    response = requests.get(f"https://api.streamelements.com/kappa/v2/points/5a2ae33308308f00016e684e/{username.lower()}")
    if response.status_code != 200:
        return get_balance()
    response_json = response.json()
    global BALANCE
    BALANCE = int(response_json['points'])
    return response_json['points']

def send_message(message:str=None) -> None:
    if message != None:
        threading.Thread(target=telegramBot.sendMessage, args=(message,)).start()
        print(message, end="\n\n")
    else:
        global telegram_message
        if telegram_message == "":
            print("No message to send")
        threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
        print(telegram_message, end="\n\n")
        telegram_message = ""

def sleep_until(end:datetime.datetime) -> None:
    now = datetime.datetime.now() + datetime.timedelta(hours=time.localtime().tm_isdst)
    if now < end:
        sleep_time = (end - now).total_seconds()
        print(f"Sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)
    else:
        print("Time has already passed")
        print("Now: ", now)
        print("End: ", end)

def get_variable_delay() -> float:
    with open('streamElements/resources/variable_delay.txt', 'r') as f:
        return float(f.read())

def decrease_variable_delay(amount:float=0.1) -> None:
    amount = round(amount, 2)
    if amount > 0:
        global telegram_message
        variable_delay = round(get_variable_delay() - amount, 2)
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(variable_delay) + "\n")
        telegram_message += f"Variable delay decreased by {amount} to {variable_delay}\n"

def increase_variable_delay(amount:float=0.1) -> None:
    amount = round(amount, 2)
    if amount > 0:
        global telegram_message
        variable_delay = round(get_variable_delay() + amount, 2)
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(variable_delay) + "\n")
        telegram_message += f"Variable delay increased by {amount} to {variable_delay}\n"

BALANCE = None
REFERENCE_DELAY = 1.75

def optimal_bet(options:dict) -> tuple[str, int]:
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

def calculate_bet(options:dict, balance:int) -> tuple[str, int]:

    global telegram_message
    telegram_message += f"The pot is at {options['win']+options['lose']} points\n"
    for i in options.keys():
        telegram_message += f"\tOption {i}: {options[i]} points\n"
    telegram_message += "\n"
    telegram_message += f"You have {balance} points\n"
    telegram_message += "\n"

    bet_option, opt_bet_ammount = optimal_bet(options)
    oposite_option = "lose" if bet_option == "win" else "win"

    b = options[bet_option] / options[oposite_option]
    telegram_message += f"b = {round(b, 3)}\n\n"
    
    if opt_bet_ammount > 0:
        telegram_message += f"The optimal bet is {round(opt_bet_ammount)} points\n"
        opt_pot_ratio = opt_bet_ammount/(options[bet_option]+opt_bet_ammount)
        telegram_message += f"Which represents {round(100*opt_pot_ratio)}% of the winning pot\n"
        opt_bet_profit = opt_pot_ratio * options[oposite_option]
        telegram_message += f"Profits {round(opt_bet_profit)} points\n"
        opt_bet_return = opt_bet_ammount + opt_bet_profit
        telegram_message += f"Returns {round(opt_bet_return)} points\n"
        opt_bet_odd = opt_bet_return / opt_bet_ammount
        telegram_message += f"Has an odd of {round(opt_bet_odd, 2)}\n"

    bet_ammount = opt_bet_ammount

    return bet_option, bet_ammount

WST, WS = None, None

def reconnect(wst:threading.Thread, ws:websocket.WebSocketApp, username:str, oauth_key:str, counters:list, first_thread_lock:threading.Event):
    global telegram_message
    twitch_message_sender.close(wst, ws)
    wst, ws = twitch_message_sender.launch_bettor("Runah", username, oauth_key, counters, first_thread_lock)
    telegram_message += "Reconnected to Twitch\n"
    return wst, ws

def check_websocket(wst:threading.Thread, ws:websocket.WebSocketApp, username:str, oauth_key:str, counters:list, first_thread_lock:threading.Event):
    try:
        twitch_message_sender.ping(ws)
    except (websocket._exceptions.WebSocketConnectionClosedException, ):
        print("Handled exception:\n", traceback.format_exc())
        return reconnect(wst, ws, username, oauth_key, counters, first_thread_lock)
    return wst, ws

def bettor_agent(channel:str, username:str, oauth_key:str, counters:list, first_thread_lock:threading.Event):
    global WST, WS
    WST, WS = twitch_message_sender.launch_bettor(channel, username, oauth_key, counters, first_thread_lock)
    time.sleep(1)

    try:
        global telegram_message
        while True:
            try:
                response = requests.get("https://api.streamelements.com/kappa/v2/contests/5a2ae33308308f00016e684e/active", timeout=10)
            except requests.exceptions.ConnectionError:
                time.sleep(10)
                continue
            response_json = response.json()
            
            now = datetime.datetime.now() + datetime.timedelta(hours=time.localtime().tm_isdst)
            
            if response_json["contest"] == None:
                print(now.strftime('%H:%M')+" - No contest found\n")
                time.sleep(60)
                continue

            start = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst)
            end = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst) + datetime.timedelta(minutes=response_json["contest"]["duration"])

            # print(start)
            # print(end)
            # print(now)

            if start < now < end: # Bets are open
                if (end - now).total_seconds() < 5: # Time to bet
                    
                    global BALANCE, telegram_message
                    telegram_message += "Time to place your bets\n"
                    telegram_message += f"There were still {round((end - now).total_seconds(), 2)} seconds left\n\n"
                    
                    BALANCE = get_balance(username) if BALANCE == None else BALANCE
                    options = {option["command"]: int(option["totalAmount"]) for option in response_json["contest"]["options"]}
                    bet_option, bet_ammount = calculate_bet(options, BALANCE)

                    balance_checkpoints = [0, 13500, 32500, 62500, 120000, 230000, 550000]
                    bet_ammount = BALANCE if bet_ammount > BALANCE else bet_ammount

                    for checkpoint in balance_checkpoints:
                        temp_bet:int = bet_ammount - checkpoint
                        if temp_bet > 0:
                            temp_bet = "all" if temp_bet >= BALANCE else str(int(temp_bet))
                            twitch_message_sender.send(WS, channel.lower(), f"!bet {bet_option} {temp_bet.replace('.0', '')}")
                            break

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
                    telegram_message += f"Follow it through: https://streamelements.com/runah/contest/{response_json['contest']['_id']}\n"
                    telegram_message += f"You have {get_balance()} points\n"

                    WST, WS = check_websocket(WST, WS, username, oauth_key, counters, first_thread_lock)
                    send_message()

                    sleep_until(end - datetime.timedelta(seconds=get_variable_delay()))
                    continue
            
            elif start < end < now: # Bets are closed
                if (now - end).total_seconds() < 5: # Bets just closed (trying to bet too late)
                    increase_variable_delay((now - end).total_seconds())
                    telegram_message += f"Bets closed {round((now - end).total_seconds(), 2)} s ago\n"
                    send_message()

                print(f"Bets closed {int((now - end).total_seconds()//3600)}:{int((now - end).total_seconds()//60)}:{int((now - end).total_seconds()%60)} ago ({round((now - end).total_seconds(), 2)} s)")
                print(f"The pot is at {response_json['contest']['totalAmount']} points")
                for option in response_json["contest"]["options"]:
                    print(f"{option['totalAmount']} points were bet on {option['title']}")
                print("\n")

                time.sleep(120)
                continue

            else: # This should never happen
                telegram_message += "Bets are not open yet\n"
                telegram_message += "Something is off\n"
                telegram_message += "Check out what's going on"
                telegram_message += "Start: " + start.strftime('%H:%M') + "\n"
                telegram_message += "End: " + end.strftime('%H:%M') + "\n"
                telegram_message += "Now: " + now.strftime('%H:%M') + "\n"
                send_message()

                time.sleep(60)
                continue
    except KeyboardInterrupt:
        with open('streamElements/resources/latest_error.txt', 'w') as f:
            pass
    except Exception as e:
        telegram_message += "Main Error:\n"
        telegram_message += datetime.datetime.now().strftime('%H:%M') + "\n"
        telegram_message += traceback.format_exc()
        send_message()
        with open('streamElements/resources/latest_error.txt', 'w') as f:
            f.write(telegram_message)



if __name__ == "__main__":
    pass
