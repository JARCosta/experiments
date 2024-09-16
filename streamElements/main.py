
import datetime
from math import sqrt
import traceback
import requests
import time
import threading

from streamElements import telegramBot
from streamElements import twitch_message_sender

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
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(VARIABLE_DELAY) + "\n")
        telegram_message = "Variable delay decreased by {} to {}".format(amount, VARIABLE_DELAY)
        telegramBot.sendMessage(telegram_message)
        print(telegram_message, end="\n\n")

def increase_variable_delay(amount=0.1):
    amount = round(amount, 2)
    if amount > 0:
        global VARIABLE_DELAY
        VARIABLE_DELAY = round(VARIABLE_DELAY + amount, 2)
        with open('streamElements/resources/variable_delay.txt', 'w') as f:
            f.write(str(VARIABLE_DELAY) + "\n")
        telegram_message = "Variable delay increased by {} to {}".format(amount, VARIABLE_DELAY)
        telegramBot.sendMessage(telegram_message)
        print(telegram_message, end="\n\n")

BALANCE = get_balance()
REFERENCE_DELAY = 1
with open('streamElements/resources/variable_delay.txt', 'r') as f:
    VARIABLE_DELAY = float(f.read())
with open('streamElements/resources/test.txt', 'w') as f:
    pass

def calculate_bet(options, balance, notifications=True):

    for i in options.keys(): # Remove the edge case where one of the options is 0
        options[i] += 1

    bet_option = "win" if options["win"] < options["lose"] else "lose"
    oposite_option = "lose" if bet_option == "win" else "win"

    telegram_message = "The pot is at {} points\n".format(options["win"] + options["lose"])
    for i in options.keys():
        telegram_message += "\tOption {}: {} points\n".format(i, options[i]-1)
    telegram_message += "\n"
    telegram_message += "You have {} points\n".format(balance)
    telegram_message += "\n"

    b = options[bet_option] / options[oposite_option]

    opt_bet_ratio = -b + sqrt(b)
    opt_bet_ammount = round(opt_bet_ratio * options[oposite_option], -1)
    opt_bet_ammount = opt_bet_ammount if opt_bet_ammount != 0 else 1

    opt_pot_ratio = opt_bet_ammount/(options[bet_option]+opt_bet_ammount)
    opt_bet_profit = opt_pot_ratio * options[oposite_option]
    opt_bet_return = opt_bet_ammount + opt_bet_profit
    opt_bet_odd = opt_bet_return / opt_bet_ammount

    telegram_message += "The optimal bet is {} points\n".format(round(opt_bet_ammount))
    telegram_message += "Which represents {}% of the winning pot\n".format(round(100*opt_pot_ratio))
    telegram_message += "Returns {} points\n".format(round(opt_bet_return))
    telegram_message += "Profits {} points\n".format(round(opt_bet_profit))
    telegram_message += "Has an odd of {}\n".format(round(opt_bet_odd, 2))

    bet_ammount = opt_bet_ammount

    if opt_bet_odd < 3: # The optimal odd is too low
        reference_odd = 3
        ref_bet_ration = (1/(reference_odd-1))-b
        ref_bet_ammount = round(ref_bet_ration * options[oposite_option], -1)
        ref_bet_ammount = ref_bet_ammount if ref_bet_ammount != 0 else 1
        
        ref_pot_ratio = ref_bet_ammount/(options[bet_option]+ref_bet_ammount)
        ref_bet_profit = ref_pot_ratio * options[oposite_option]
        ref_bet_return = ref_bet_ammount + ref_bet_profit
        ref_bet_odd = ref_bet_return / ref_bet_ammount

        telegram_message += "\n"
        telegram_message += "The reference bet is {} points\n".format(round(ref_bet_ammount))
        telegram_message += "Which represents {}% of the winning pot\n".format(round(100*ref_pot_ratio))
        telegram_message += "Returns {} points\n".format(round(ref_bet_return))
        telegram_message += "Profits {} points\n".format(round(ref_bet_profit))
        telegram_message += "Has an odd of {}\n".format(round(ref_bet_odd, 2))

        bet_ammount = ref_bet_ammount
    
    bet_ammount = 0 if bet_ammount < 10 else bet_ammount

    if notifications:
        threading.Thread(target=telegramBot.sendMessage, args=(telegram_message,)).start()
        print(telegram_message, end="\n\n")
    else:
        print(telegram_message)
    return bet_option, bet_ammount

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
                    global BALANCE
                    with open('streamElements/resources/pots.txt', 'a') as f:
                        f.write(str(options) + "\n")
                    bet_option, bet_ammount = calculate_bet(options, BALANCE)
                    if bet_ammount > 0:
                        bet_ammount = BALANCE if bet_ammount > BALANCE else bet_ammount
                        twitch_message_sender.bet(WS, bet_option, str(int(bet_ammount)) if BALANCE > bet_ammount else "all")

                        if (end - now).total_seconds() > REFERENCE_DELAY: # betting too early
                            decrease_variable_delay(((end - now).total_seconds() - REFERENCE_DELAY)/4)
                        if (end - now).total_seconds() < REFERENCE_DELAY: # betting too late
                            increase_variable_delay((REFERENCE_DELAY - (end - now).total_seconds())/4)
                        
                        oposite_option = "lose" if bet_option == "win" else "win"
                        bet_profit = options[oposite_option] * (bet_ammount/(options[bet_option]+bet_ammount))
                        bet_return = bet_ammount + bet_profit
                        bet_odd = bet_return/bet_ammount
                        pot_ratio = bet_ammount/(options[bet_option]+bet_ammount)

                        telegram_message = "Time to place your bets\n"
                        telegram_message += "There were still {} seconds left\n".format(round((end - now).total_seconds(), 2))
                        telegram_message += "\n"
                        telegram_message += "The official bet is {} points on {}\n".format(bet_ammount, bet_option)
                        telegram_message += "Which represents {}% of the winning pot\n".format(round(100*pot_ratio))
                        telegram_message += "Returns {} points\n".format(round(bet_return))
                        telegram_message += "Profits {} points\n".format(round(bet_profit))
                        telegram_message += "Has an odd of {}\n".format(round(bet_odd, 2))
                        telegramBot.sendMessage(telegram_message)
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
                telegramBot.sendMessage(telegram_message)
                print(telegram_message, end="\n\n")

                time.sleep(120)
                continue

    except KeyboardInterrupt:
        twitch_message_sender.close(WST, WS)
    except Exception as e:
        with open('streamElements/resources/test.txt', 'a') as f:
            f.write("aaaaaaaaaaaaa\n")
            f.write(str(datetime.datetime.now()) + "\n")
            f.write(str(e) + "\n")
        telegram_message = "Error:\n"
        telegram_message += traceback.format_exc()
        telegramBot.sendMessage(telegram_message)



if __name__ == "__main__":
    get_bets()

