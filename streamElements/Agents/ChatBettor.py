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

from .WebSocket import WebSocket, ping, close, send

TELEGRAM_MESSAGE = ""
BALANCE = None
REFERENCE_DELAY = 1.75
LAST_BET = None

############################################################
# UTILITIES
############################################################

def get_balance(username:str) -> int:
    response = requests.get(f"https://api.streamelements.com/kappa/v2/points/5a2ae33308308f00016e684e/{username.lower()}")
    if response.status_code != 200:
        return get_balance(username)
    response_json = response.json()
    global BALANCE
    BALANCE = int(response_json['points'])
    return response_json['points']

def send_message(message:str=None, log:bool=True, notification:bool=False) -> None:

    global TELEGRAM_MESSAGE
    if not message:
        message = TELEGRAM_MESSAGE
        TELEGRAM_MESSAGE = ""
    if message == "":
        print("No message to send")
        return

    telegramBot.sendMessage_threaded(message, log, notification)
    print(message, end="\n\n")

def sleep_until(end:datetime.datetime, kill_thread:threading.Event) -> None:
    now = datetime.datetime.now() + datetime.timedelta(hours=time.localtime().tm_isdst)
    if now < end:
        sleep_time = (end - now).total_seconds()
        print(f"Sleeping for {sleep_time} seconds")
        telegramBot.sendMessage(f"Sleeping for {sleep_time} seconds")
        for _ in range(int(sleep_time)//10):
            time.sleep(10)
            if kill_thread.is_set():
                break
        time.sleep(sleep_time % 10)
        return True
    else:
        # print("Time has already passed")
        # print("Now: ", now)
        # print("End: ", end)
        return False

############################################################
# VARIABLE DELAY 
############################################################

def get_variable_delay() -> float:
    with open('streamElements/resources/variable_delay.txt', 'r') as f:
        return float(f.read())

def decrease_variable_delay(amount:float=0.1) -> None:
    amount = round(amount, 2)
    if amount > 0:
        variable_delay = round(get_variable_delay() - amount, 2)
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(variable_delay) + "\n")
        telegram_message = f"Variable delay decreased by {amount} to {variable_delay}\n"
        telegramBot.sendMessage(telegram_message)

def increase_variable_delay(amount:float=0.1) -> None:
    amount = round(amount, 2)
    if amount > 0:
        variable_delay = round(get_variable_delay() + amount, 2)
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(variable_delay) + "\n")
        telegram_message = f"Variable delay increased by {amount} to {variable_delay}\n"
        telegramBot.sendMessage(telegram_message)

############################################################
# BETTING
############################################################

def check_contest(bettor_username:str, channel:str, kill_thread:threading.Event):
    runah_contests, el_pipow_contests = "5a2ae33308308f00016e684e", "5e46e43e8d514cea9ae5bfb4"
    contests = runah_contests if channel.lower() == "runah" else el_pipow_contests

    response_json = requests.get(f"https://api.streamelements.com/kappa/v2/contests/{contests}/active", timeout=10).json()
    print(response_json)
    try:
        end = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst) + datetime.timedelta(minutes=response_json["contest"]["duration"])
    except TypeError:
        print(f"https://api.streamelements.com/kappa/v2/contests/{contests}/active")
        print("No contest Found")
        return False, None, None

    if datetime.datetime.now() < end:
        telegram_message = "Open contest found\n"
        telegram_message += f"Follow it through: https://streamelements.com/{channel}/contest/{response_json['contest']['_id']}\n"
        telegram_message += f"You have {get_balance(bettor_username)} points\n"
        telegramBot.sendMessage(telegram_message)
    else:
        telegram_message = "Closed contest found\n"
        telegram_message += f"Follow it through: https://streamelements.com/{channel}/contest/{response_json['contest']['_id']}\n"
        print(telegram_message)

    return sleep_until(end - datetime.timedelta(seconds=get_variable_delay()), kill_thread=kill_thread), response_json, end

def optimal_bet(options:dict) -> tuple[str, int]:
    little_option = "lose" if options["lose"] < options["win"] else "win"
    little_option_amount = options[little_option]
    if little_option_amount == 0:
        return little_option, 1

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
    BALANCE = get_balance(username) if BALANCE == None else BALANCE
    
    # test connection:
    try:
        ping(ws)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        telegramBot.sendMessage_threaded(traceback.format_exc())
    
    # Check if there is a contest open to bet, if so, wait until it's time to bet
    succ, _, _ = check_contest(username, channel.lower(), kill_thread=kill_thread) 

    if succ:

        telegram_notification = ""
        telegram_log = ""
        now = datetime.datetime.now()
        
        # Contest info
        streamElements_ids = {
            "runah": "5a2ae33308308f00016e684e",
            "el_pipow": "5e46e43e8d514cea9ae5bfb4"
        }
        try:
            contests = streamElements_ids[channel.lower()]
        except ValueError:
            telegramBot.sendMessage_threaded(f"ValueError:\n No StreamElements id found", notification=True)
        while True:
            try:
                contest_json = requests.get(f"https://api.streamelements.com/kappa/v2/contests/{contests}/active", timeout=10).json()
                end = datetime.datetime.strptime(contest_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst) + datetime.timedelta(minutes=contest_json["contest"]["duration"])
                break
            except TypeError as e:
                # Contest was probabily canceled
                telegramBot.sendMessage_threaded(f"TypeError:\n {contest_json}", notification=True)
                time.sleep(3)
        # check if contest got restarted
        if (end - now).total_seconds() > 5:
            return bet(ws, username, channel, kill_thread)
        
        # get best bet, if not enough, or too close to checkpoint, make it the maximum we can bet
        options = {option["command"]: int(option["totalAmount"]) for option in contest_json["contest"]["options"]}
        # Get the most profitable bet option and amount
        bet_option, bet_amount = optimal_bet(options)
        bet_amount = BALANCE if bet_amount > BALANCE else bet_amount
        for checkpoint in [0, 13500, 32500, 62500, 120000, 230000, 550000]:
            temp_bet:int = bet_amount - checkpoint
            if temp_bet > 0:
                temp_bet = "all" if temp_bet >= BALANCE else str(int(temp_bet))
                send(ws, channel.lower(), f"!bet {bet_option} {temp_bet.replace('.0', '')}")
                # now = datetime.datetime.now()
                break

        # Get the stats for a given bet on a given contest
        b, pot_ratio, bet_profit, bet_return, bet_odd = bet_stats(options, bet_amount, bet_option)
        if bet_amount > 0:
            telegram_notification += f"Betting {round(bet_amount)} points\n\n"
            telegram_notification += f"b: {round(b,3)}\n"
            telegram_notification += f"odd: {round(bet_odd, 2)}\n"
            telegram_log += f"The optimal bet is {round(bet_amount)} points, {round(100*pot_ratio)}% of the winning pot\n"
            telegram_log += f"b value is {round(b,3)}\n"
            # for i in options.keys:
                # telegram_log += ""
            telegram_log += options.__str__() + "\n"
            telegram_log += f"Profits {round(bet_profit)} points\n"
            telegram_log += f"Has an odd of {round(bet_odd, 2)}\n\n" if bet_amount > 0 else "\n"
        elif b:
            telegram_notification += f"Skipping bet\n"
            telegram_notification += f"b: {round(b,3)}\n\n"
            if bet_odd:
                telegram_notification += f"odd: {round(bet_odd, 2)}\n"

        if now:
            telegram_log += f"Placed bet with {round((end - now).total_seconds(), 2)} seconds left\n\n"
        if (end - now).total_seconds() > REFERENCE_DELAY: # betting too early
            decrease_variable_delay(((end - now).total_seconds() - REFERENCE_DELAY)/4)
        if (end - now).total_seconds() < REFERENCE_DELAY: # betting too late
            increase_variable_delay((REFERENCE_DELAY - (end - now).total_seconds())/4)

        telegramBot.sendMessage(telegram_log)
        telegramBot.sendMessage(telegram_notification, False, True)

class Bettor:

    def on_message(ws:websocket.WebSocketApp, message:str, username:str, channel:str, oauth_key:str, counters:list, connection_open_event:threading.Event, kill_thread_event:threading.Event):
        WebSocket.connect(ws, message, username, channel, oauth_key, counters, connection_open_event, kill_thread_event, launch_bettor)
        try:
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1].replace('ACTION ', '')
            mention = message.split("@")[-1].split(" ")[0].replace(",", "")
            # print(user, ":", msg.replace("\n", "").replace("\r", ""))
            # print(user.lower(), user.lower() == "StreamElements".lower())
            # print(mention.lower(), username.lower(), mention.lower() == username.lower())
            # print()
        except IndexError:
            return

        # StreamElements talked to someone
        if user.lower() == "StreamElements".lower():
            telegram_message = user + ": " + msg.replace("\r", "")
            print(telegram_message)
            # telegramBot.sendMessage(telegram_message)

            if "a new contest has started" in msg: # New bet
                threading.Thread(target=bet, args=[ws, username, channel, kill_thread_event]).start()

            elif "no longer accepting bets for" in msg:
                pass

            elif f", there is no contest currently running." in msg or "an error occured while placing your bet: No contest found" in msg: # Bet placed too late
                # We were the one who bet late
                if mention.lower() == username.lower():
                    telegramBot.sendMessage("Betting too late!", notification=True)
                    increase_variable_delay()

            elif "won the contest" in msg:
                global LAST_BET
                if LAST_BET:
                    winner_option = msg.split('"')[1]
                    if winner_option.lower() == LAST_BET[0]:
                        telegram_message = f"Won a bet of {LAST_BET[1]} points\n"
                        telegram_message += f"b value was {round(LAST_BET[3][0], 3)}\n"
                        telegram_message += f"profited {round(LAST_BET[3][2])} points\n"
                        telegramBot.sendMessage(telegram_message, notification=True)
                    else:
                        telegram_message = f"Lost a bet of {LAST_BET[1]} points\n"
                        telegram_message += f"b value was {round(LAST_BET[3][0], 3)}\n"
                        telegramBot.sendMessage(telegram_message, notification=True)
        
        # We were mentioned
        if f"@{username.lower()}" in msg.lower():
            telegram_message = user + ": " + msg.replace("\r", "")
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)


def launch_bettor(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=partial(Bettor.on_message, username=username, channel=channel, oauth_key=oauth_key, counters=counters, connection_open_event=connection_open_event, kill_thread_event=kill_thread_event),
        on_error=partial(WebSocket.on_error, channel=channel, username=username, oauth_key=oauth_key, counters=counters, kill_thread_event=kill_thread_event, creator_function=launch_bettor),
        on_open=partial(WebSocket.on_open, username=username, oauth_key=oauth_key, counters=counters)
        )

    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()
    counters[1] += 1

    print("checking for open contest")
    bet(ws=ws, username=username, channel=channel, kill_thread=kill_thread_event)


    kill_thread_event.wait()
    ws.close()
    # wst.join()
    print(f"{launch_bettor.__name__.replace('launch_', '').capitalize()} left")

    return wst, ws