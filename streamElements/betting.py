import datetime
from functools import partial
from math import sqrt
import threading
import time
import traceback
import credentials
import requests
import telegramBot
import websocket

from .Agents.WebSocket import WebSocket, ping, close, send

BALANCE = None
LAST_BET = None

DEFAULT_DELAY = 2.05
REFERENCE_DELAY = 1

def get_streamelements_id(channel:str) -> str:
    streamElements_ids = {
        "runah": "5a2ae33308308f00016e684e",
        "prcs": "604ccb6ffc51b34f88198de3",
        "el_pipow": "5e46e43e8d514cea9ae5bfb4",
        "nopeej": "602f143f4e93066392d5dcb0",
    }
    try:
        return streamElements_ids[channel.lower()]
    except ValueError:
        telegramBot.sendMessage_threaded(f"ValueError:\n No StreamElements id found for {channel}", notification=True)

############################################################
# UTILITIES
############################################################

def get_balance(channel:str, username:str) -> int:
    channel_id = get_streamelements_id(channel)
    response = requests.get(f"https://api.streamelements.com/kappa/v2/points/{channel_id}/{username.lower()}")
    if response.status_code != 200:
        return get_balance(channel, username)
    response_json = response.json()
    global BALANCE
    BALANCE = int(response_json['points'])
    return response_json['points']

def sleep_until(end:datetime.datetime, kill_thread:threading.Event) -> None:
    
    # it is summer time, and time.localtime().tm_isdst is 1
    now = datetime.datetime.now() #+ datetime.timedelta(hours=time.localtime().tm_isdst)
    
    if now < end:
        sleep_time = (end - now).total_seconds()
        log = f"Sleeping for {sleep_time} seconds\n\n"
        print(log)
        telegramBot.add_telegram_log(log)
        for _ in range(int(sleep_time)//10):
            time.sleep(10)
            if kill_thread.is_set():
                break
        time.sleep(sleep_time % 10)
        return True
    else:
        log = f"Time has already passed\nNow: {now}\nEnd: {end}\n\n"
        print(log)
        telegramBot.add_telegram_log(log)
        return False

############################################################
# VARIABLE DELAY 
############################################################

def get_variable_delay() -> float:
    try:
        with open('streamElements/resources/variable_delay.txt', 'r') as f:
            return float(f.read())
    except FileNotFoundError:
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(DEFAULT_DELAY))
        return DEFAULT_DELAY

def set_variable_delay(delay:float) -> None:
    with open('streamElements/resources/variable_delay.txt', 'w') as f:
        f.write(str(round(delay, 2)))

def update_variable_delay() -> None:
    global REFERENCE_DELAY
    REFERENCE_DELAY = get_variable_delay()

def add_variable_delay(amount:float=0.1) -> None:
    if round(amount, 2) != 0:
        variable_delay = round(get_variable_delay() + amount, 2)
        set_variable_delay(variable_delay)
        sign = "+" if amount > 0 else "-"
        log = f"Variable delay changed to {get_variable_delay()}({sign}{round(abs(amount), 2)})\n\n"
        print(log)
        telegramBot.add_telegram_log(log)
    update_variable_delay()

############################################################
# BETTING
############################################################

def check_contest(bettor_username:str, channel:str, kill_thread:threading.Event):
    
    channel_id = get_streamelements_id(channel)
    
    response_json = requests.get(f"https://api.streamelements.com/kappa/v2/contests/{channel_id}/active", timeout=10).json()
    # print(response_json.status_code, response_json)
    try:
        end = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst) + datetime.timedelta(minutes=response_json["contest"]["duration"])
    except TypeError:
        print(f"https://api.streamelements.com/kappa/v2/contests/{channel_id}/active")
        print("No contest Found")
        return False, None, None

    if datetime.datetime.now() < end:
        telegramBot.add_telegram_log("Open contest found\n")
        telegramBot.add_telegram_log(f"Follow it through: https://streamelements.com/{channel}/contest/{response_json['contest']['_id']}\n")
        telegramBot.add_telegram_log(f"You have {get_balance(channel, bettor_username)} points\n\n")
        return sleep_until(end - datetime.timedelta(seconds=get_variable_delay()), kill_thread=kill_thread), response_json, end
    else:
        telegramBot.add_telegram_log("Closed contest found\n")
        telegramBot.add_telegram_log(f"Follow it through: https://streamelements.com/{channel}/contest/{response_json['contest']['_id']}\n\n")
        return sleep_until(end - datetime.timedelta(seconds=get_variable_delay()), kill_thread=kill_thread), response_json, end
        

def optimal_bet(options:dict, min_bet:int=1) -> tuple[str, int]:
    little_option = "lose" if options["lose"] < options["win"] else "win"
    big_option = "win" if little_option == "lose" else "lose"
    little_option_amount = options[little_option]
    big_option_amount = options[big_option]
    if options["win"] + options["lose"] == 0:
        return little_option, 0
    if little_option_amount == 0 and big_option_amount > min_bet*2:
        return little_option, min_bet

    oposite_option = "lose" if little_option == "win" else "win"
    oposite_option_amount = options[oposite_option]

    b = little_option_amount / oposite_option_amount

    # opt_bet_ratio = -b + sqrt(b)
    opt_bet_ratio = (sqrt(2*b)-2*b)/2
    if opt_bet_ratio < 0:
        return little_option, 0
    
    opt_bet_amount = round(opt_bet_ratio * oposite_option_amount, -1)
    return little_option, opt_bet_amount

def bet_stats(options:dict, bet_amount:int, bet_option:str):
    oposite_option = "lose" if bet_option == "win" else "win"
    
    b = options[bet_option] / options[oposite_option] if options[oposite_option] > 0 else None

    pot_ratio = bet_amount / (options[bet_option] + bet_amount)
    bet_profit = pot_ratio * options[oposite_option]
    bet_return = bet_amount + bet_profit
    bet_odd = bet_return / bet_amount if bet_amount > 0 else None
    
    global LAST_BET
    LAST_BET = [bet_option, bet_amount, options, [b, pot_ratio, bet_profit, bet_return, bet_odd]] if bet_amount > 0 else None
    
    return b, pot_ratio, bet_profit, bet_return, bet_odd

def bet(ws, username, channel, kill_thread):

    global BALANCE
    BALANCE = get_balance(channel, username) if BALANCE == None else BALANCE
    
    # test connection:
    try:
        ping(ws)
    except Exception as e:
        telegramBot.send_telegram_notification(f"Error: {e}\n{traceback.format_exc()}")
    
    # Check if there is a contest open to bet, if so, wait until it's time to bet
    succ, _, _ = check_contest(username, channel.lower(), kill_thread=kill_thread) 
    # print(succ)

    if succ:

        telegram_log = ""
        now = datetime.datetime.now()

        while True:
            try:
                contest_json = requests.get(f"https://api.streamelements.com/kappa/v2/contests/{get_streamelements_id(channel)}/active", timeout=10).json()
                end = datetime.datetime.strptime(contest_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst) + datetime.timedelta(minutes=contest_json["contest"]["duration"])
                min_bet = int(contest_json["contest"]["minBet"])
                break
            except TypeError as e:
                # Contest was probabily canceled
                telegramBot.send_telegram_notification(f"TypeError:\n {contest_json}")
                time.sleep(3)
        # check if contest got restarted
        time_left = (end - now).total_seconds()
        if time_left > 5:
            return bet(ws, username, channel, kill_thread)
        
        # get best bet, if not enough, or too close to checkpoint, make it the maximum we can bet
        options = {option["command"]: int(option["totalAmount"]) for option in contest_json["contest"]["options"]}
        # Get the most profitable bet option and amount
        bet_option, bet_amount = optimal_bet(options, min_bet)
        bet_amount = BALANCE if bet_amount > BALANCE else bet_amount
        for checkpoint in [0, 13500, 32500, 62500, 120000, 230000, 550000]:
            temp_bet:int = bet_amount - checkpoint
            if temp_bet > 0:
                temp_bet = "all" if temp_bet >= BALANCE else str(int(temp_bet))
                send(ws, channel.lower(), f"!bet {bet_option} {temp_bet.replace('.0', '')}")
                # now = datetime.datetime.now()
                break

        # Get the stats for a given bet on a given contest
        if options["win"] + options["lose"] != 0:
            b, pot_ratio, bet_profit, bet_return, bet_odd = bet_stats(options, bet_amount, bet_option)
        else:
            b, bet_odd = 0, 0
        
        if bet_amount > 0:
            telegram_log += f"The optimal bet is {round(bet_amount)} points, {round(100*pot_ratio)}% of the winning pot\n"
            telegram_log += f"b value is {round(b,3)}\n"
            # for i in options.keys:
                # telegram_log += ""
            telegram_log += options.__str__() + "\n"
            telegram_log += f"Profits {round(bet_profit)} points\n"
            telegram_log += f"Has an odd of {round(bet_odd, 2)}\n\n" if bet_amount > 0 else "\n"
            
            telegram_log += f"Betting {round(bet_amount)} points\n"
            telegram_log += f"b: {round(b,3)}\n"
            telegram_log += f"odd: {round(bet_odd, 2)}\n"
            telegram_log += "\n"
        else:
            telegram_log += f"Skipping bet\n"
            if not b is None:
                telegram_log += f"b: {round(b,3)}\n\n"
            if bet_odd:
                telegram_log += f"odd: {round(bet_odd, 2)}\n"
            telegram_log += "\n"

        if now:
            telegram_log += f"Placed bet with {round(time_left, 2)} seconds left\n\n"
        
        add_variable_delay(((REFERENCE_DELAY - time_left)/4))

        telegramBot.add_telegram_log(telegram_log)
    telegramBot.send_telegram_log()
