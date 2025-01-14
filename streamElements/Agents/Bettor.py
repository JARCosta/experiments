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

def send_message(message:str=None, notification:bool=False) -> None:

    global TELEGRAM_MESSAGE
    if not message:
        message = TELEGRAM_MESSAGE
        TELEGRAM_MESSAGE = ""
    if message == "":
        print("No message to send")
        return

    telegramBot.sendMessage_threaded(message, notification)
    print(message, end="\n\n")

def sleep_until(end:datetime.datetime, kill_thread:threading.Event) -> None:
    now = datetime.datetime.now() + datetime.timedelta(hours=time.localtime().tm_isdst)
    if now < end:
        sleep_time = (end - now).total_seconds()
        print(f"Sleeping for {sleep_time} seconds")
        sleep_interrupt(int(sleep_time), kill_thread)
        time.sleep(sleep_time % 1)
        return True
    else:
        # print("Time has already passed")
        # print("Now: ", now)
        # print("End: ", end)
        return False

def sleep_interrupt(duration:int, kill_thread:threading.Event):
    for i in range(duration):
        time.sleep(1)
        if kill_thread.is_set():
            break

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

def contest_found(bettor_username:str, channel:str, kill_thread:threading.Event):
    runah_contests, el_pipow_contests = "5a2ae33308308f00016e684e", "5e46e43e8d514cea9ae5bfb4"
    contests = runah_contests if channel.lower() == "runah" else el_pipow_contests

    response_json = requests.get(f"https://api.streamelements.com/kappa/v2/contests/{contests}/active", timeout=10).json()
    try:
        end = datetime.datetime.strptime(response_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst) + datetime.timedelta(minutes=response_json["contest"]["duration"])
    except TypeError:
        print(f"https://api.streamelements.com/kappa/v2/contests/{contests}/active")
        print(response_json)
        return contest_found(bettor_username, channel, kill_thread)

    telegram_message = "Contest found\n"
    telegram_message += f"Follow it through: https://streamelements.com/{channel}/contest/{response_json['contest']['_id']}\n"
    telegram_message += f"You have {get_balance(bettor_username)} points\n"
    # print(datetime.datetime.now(), end)
    if datetime.datetime.now() < end:
        telegramBot.sendMessage(telegram_message, notification=True)

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
    
    b = options[bet_option] / options[oposite_option] if options[oposite_option] > 0 else False

    if bet_amount > 0:
        pot_ratio = bet_amount / (options[bet_option] + bet_amount)
        bet_profit = pot_ratio * options[oposite_option]
        bet_return = bet_amount + bet_profit
        bet_odd = bet_return / bet_amount
        global LAST_BET
        LAST_BET = [bet_option, bet_amount, options, [b, pot_ratio, bet_profit, bet_return, bet_odd]]
        return b, pot_ratio, bet_profit, bet_return, bet_odd
    return b, None, None, None, None

def calculate_bet(options:dict, balance:int) -> tuple[str, int]:

    global TELEGRAM_MESSAGE
    TELEGRAM_MESSAGE += f"The pot is at {options['win']+options['lose']} points\n"
    for i in options.keys():
        TELEGRAM_MESSAGE += f"\tOption {i}: {options[i]} points\n"
    TELEGRAM_MESSAGE += "\n"
    TELEGRAM_MESSAGE += f"You have {balance} points\n"
    TELEGRAM_MESSAGE += "\n"

    bet_option, opt_bet_amount = optimal_bet(options)

    b, opt_pot_ratio, opt_bet_profit, opt_bet_return, opt_bet_odd = bet_stats(options, opt_bet_amount, bet_option)

    if b:
        TELEGRAM_MESSAGE += f"b = {round(b, 3)}\n\n"

    if opt_bet_amount > 0:
        TELEGRAM_MESSAGE += f"The optimal bet is {round(opt_bet_amount)} points\n"
        TELEGRAM_MESSAGE += f"Which represents {round(100*opt_pot_ratio)}% of the winning pot\n"
        TELEGRAM_MESSAGE += f"Profits {round(opt_bet_profit)} points\n"
        TELEGRAM_MESSAGE += f"Returns {round(opt_bet_return)} points\n"
        TELEGRAM_MESSAGE += f"Has an odd of {round(opt_bet_odd, 2)}\n"

    bet_amount = opt_bet_amount

    return bet_option, bet_amount

def bet(ws, username, channel, kill_thread):
    succ, _, _ = contest_found(username, channel.lower(), kill_thread=kill_thread)
    if succ:

        global TELEGRAM_MESSAGE, BALANCE
        TELEGRAM_MESSAGE += "Time to place your bets\n"
        now = datetime.datetime.now()
        
        runah_contests, el_pipow_contests = "5a2ae33308308f00016e684e", "5e46e43e8d514cea9ae5bfb4"
        contests = runah_contests if channel.lower() == "runah" else el_pipow_contests

        contest_json = requests.get(f"https://api.streamelements.com/kappa/v2/contests/{contests}/active", timeout=10).json()
        end = datetime.datetime.strptime(contest_json["contest"]["startedAt"],"%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=time.localtime().tm_isdst) + datetime.timedelta(minutes=contest_json["contest"]["duration"])
        if (end - now).total_seconds() > 5:
            return bet(ws, username, channel, kill_thread)
        TELEGRAM_MESSAGE += f"There is still {round((end - now).total_seconds(), 2)} seconds left\n\n"

        BALANCE = get_balance(username) if BALANCE == None else BALANCE
        options = {option["command"]: int(option["totalAmount"]) for option in contest_json["contest"]["options"]}
        bet_option, bet_amount = calculate_bet(options, BALANCE)

        balance_checkpoints = [0, 13500, 32500, 62500, 120000, 230000, 550000]
        bet_amount = BALANCE if bet_amount > BALANCE else bet_amount

        for checkpoint in balance_checkpoints:
            temp_bet:int = bet_amount - checkpoint
            if temp_bet > 0:
                temp_bet = "all" if temp_bet >= BALANCE else str(int(temp_bet))
                send(ws, channel.lower(), f"!bet {bet_option} {temp_bet.replace('.0', '')}")
                break

        now = datetime.datetime.now()

        TELEGRAM_MESSAGE += f"There is still {round((end - datetime.datetime.now()).total_seconds(), 2)} seconds left\n\n"
        if (end - now).total_seconds() > REFERENCE_DELAY: # betting too early
            decrease_variable_delay(((end - now).total_seconds() - REFERENCE_DELAY)/4)
        if (end - now).total_seconds() < REFERENCE_DELAY: # betting too late
            increase_variable_delay((REFERENCE_DELAY - (end - now).total_seconds())/4)

        send_message()



############################################################
# NETWORK CONNECTION
############################################################

# WST, WS = None, None

# def reconnect(wst:threading.Thread, ws:websocket.WebSocketApp, username:str, oauth_key:str, counters:list, kill_thread:threading.Event):
#     global telegram_message
#     twitch_message_sender.close(wst, ws)
#     wst, ws = Bettor.launch_bettor("Runah", username, oauth_key, counters, kill_thread)
#     telegram_message += "Reconnected to Twitch\n"
#     return wst, ws

# def check_websocket(wst:threading.Thread, ws:websocket.WebSocketApp, username:str, oauth_key:str, counters:list, kill_thread:threading.Event):
#     try:
#         twitch_message_sender.ping(ws)
#     except (websocket._exceptions.WebSocketConnectionClosedException, ):
#         print("Handled exception:\n", traceback.format_exc())
#         return reconnect(wst, ws, username, oauth_key, counters, kill_thread)
#     return wst, ws

class Bettor:

    def on_open(ws:websocket.WebSocketApp, oauth_key:str, username:str, counters:list, kill_thread:threading.Event, channel:str):
        WebSocket.on_open(ws, oauth_key, username, counters)

    def on_message(ws:websocket.WebSocketApp, message:str, username:str, channel:str, counters:list, connection_open_event:threading.Event, kill_thread:threading.Event):
        WebSocket.connect(ws, message, username, channel, counters, connection_open_event, launch_bettor)
        try:
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]
            mention = message.split("@")[-1].split(" ")[0].replace(",", "")
            # print(user, ":", msg.replace("\n", "").replace("\r", ""))
            # print(user.lower(), user.lower() == "StreamElements".lower())
            # print(mention.lower(), username.lower(), mention.lower() == username.lower())
            # print()
        except IndexError:
            return

        if user.lower() == "StreamElements".lower():
            print(msg)

            if "a new contest has started" in msg: # New bet
                print("betting")
                bet(ws=ws, username=username, channel=channel, kill_thread=kill_thread)

            elif "no longer accepting bets for" in msg:
                print(datetime.datetime.now())

            elif f", there is no contest currently running." in msg: # Bet placed too late
                print(user, ":", msg.replace("\n", "").replace("\r", ""))
                print(user.lower(), user.lower() == "StreamElements".lower())
                print(mention.lower(), username.lower(), mention.lower() == username.lower())
                print()
                if user.lower() == "StreamElements".lower():
                    print("StreamElements")
                if mention.lower() == username.lower():
                    print(mention.lower(), mention.lower() == username.lower())

            elif "won the contest" in msg:
                winner_option = msg.split('"')[1]
                # print(winner_option)
                global LAST_BET

                if LAST_BET:
                    if winner_option.lower() == LAST_BET[0]:
                        telegram_message = f"Won a bet of {LAST_BET[1]} points\n"
                        telegram_message += f"b value was {LAST_BET[3][0]}\n"
                        telegram_message += f"profited {LAST_BET[3][2]} points\n"
                        telegramBot.sendMessage(telegram_message, True)
                    else:
                        telegram_message += f"Lost a bet of {LAST_BET[1]} points\n"
                        telegram_message += f"b value was {LAST_BET[3][0]}\n"
                        telegramBot.sendMessage(telegram_message, True)
        
        elif f"@{username.lower()}" in message.lower() and not f":{username.lower()}" in message: # I was mentioned
            print("Got mentioned")
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]

            if "an error occured while placing your bet: No contest found" in msg or "there is no contest currently running" in msg:
                if user.lower() == "StreamElements".lower():
                    print("I bet too late")
                    increase_variable_delay()

            telegram_message = user + ": " + msg
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)


def launch_bettor(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    try:
        ws = websocket.WebSocketApp(
            websocket_url,
            on_message=partial(Bettor.on_message, username=username, channel=channel, counters=counters, connection_open_event=connection_open_event, kill_thread=kill_thread_event),
            on_error=WebSocket.on_error,
            on_open=partial(Bettor.on_open, oauth_key=oauth_key, username=username, counters=counters, kill_thread=kill_thread_event, channel=channel)
            )
    except Exception as e:
        print(e)
    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()
    counters[1] += 1

    print("checking contest open")
    bet(ws=ws, username=username, channel=channel, kill_thread=kill_thread_event)


    kill_thread_event.wait()
    print("massive quitting 1")
    ws.close()
    print("massive quitting 2")
    # wst.join()
    # print("massive quitting 3")

    return wst, ws