import websocket
import json
import threading
import time
import os
import random

import matplotlib.pyplot as plt

# Event to signal that the connection is open
connection_open_event = threading.Event()

ITEMS_INFO = {}
CASE_INFO = {}
POSSIBLE_ITEMS = {}
SUCCESSFUL_ITEMS = []

SUCCESS_RATE = []
SUCCESS_BALANCE = []
SUCCESS_COUNTER = []

class WebSocket:

    def on_message(ws, message):
        global ITEMS_INFO, CASE_INFO
        print(f"Received message: {message}")

        if "pf_case_ranges" in message:
            ITEMS_INFO = json.loads(message)
        
        if "cases" in message:
            CASE_INFO = json.loads(message)
        
        if "ready" in message:
            ws.close()

    def on_error(ws, error):
        print(f"Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket connection closed with status: {close_status_code}, message: {close_msg}")

    def on_open(ws):
        print("WebSocket connection opened")
        
        ws.send(json.dumps({"msg":"connect","version":"1","support":["1","pre2","pre1"]}))
        connection_open_event.set()  # Signal that the connection is open

def save():
    with open("resources/case_info.json", "w") as f:
        f.write(json.dumps(CASE_INFO, indent=4))

    with open("resources/items_info.json", "w") as f:
        f.write(json.dumps(ITEMS_INFO, indent=4))
    
    with open("resources/possible_items.json", "w") as f:
        f.write(json.dumps(POSSIBLE_ITEMS, indent=4))
    
    with open("resources/successful_items.json", "w") as f:
        f.write(json.dumps(SUCCESSFUL_ITEMS, indent=4))

def simulate(balance, case_price):
    global POSSIBLE_ITEMS, SUCCESSFUL_ITEMS, SUCCESS_RATE, SUCCESS_BALANCE
    
    counter = 0
    success = False

    while balance >= case_price:
        balance -= case_price
        counter += 1

        item = random.choices(list(POSSIBLE_ITEMS.keys()), [POSSIBLE_ITEMS[i]["prob"] for i in POSSIBLE_ITEMS.keys()])[0]


        if item in SUCCESSFUL_ITEMS:
            success = True
            break
        else:
            balance += round(POSSIBLE_ITEMS[item]["price_eur"], 2)

    
    if success:
        # print(f"Success after {counter} cases, balance: {balance}€")
        SUCCESS_RATE.append(success)
        SUCCESS_BALANCE.append(balance)
        SUCCESS_COUNTER.append(counter)
    else:
        # print(f"Failure after {counter} cases, balance: {balance}€")
        SUCCESS_RATE.append(success)
    
    return success
    
    


use_saved = input("Use saved data? (y/n): ") == "y"

if __name__ == "__main__":

    if not use_saved:

        websocket_url = "wss://csgo.net/websocket"
        ws = websocket.WebSocketApp(
            websocket_url,
            on_message=WebSocket.on_message,
            on_error=WebSocket.on_error,
            on_close=WebSocket.on_close,
            on_open=WebSocket.on_open
        )
        
        # Get the case name from the user
        case = input("Enter the case name: ")
        
        # Run the WebSocket connection in a separate thread to avoid blocking
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()

        # Wait for the connection to be open before sending the message
        connection_open_event.wait()

        # Send the message
        ws.send(json.dumps({"msg":"sub","id":"Q5HdLG9KxWoq7M9ux","name":"case","params":[case]}))

        wst.join()  # Wait for the WebSocket thread to finish

        for i in ITEMS_INFO["fields"]["items"]:
            POSSIBLE_ITEMS[i["name"]] = {"prob": i["prob"], "price_eur": i["price_eur"], "upper_range": i["range"][1]}
        
        for i in range(len(POSSIBLE_ITEMS)):
            print(f"Item {i+1}: {list(POSSIBLE_ITEMS.keys())[i]}, Probability: {round(list(POSSIBLE_ITEMS.values())[i]['prob'], 3)}%, Price: {list(POSSIBLE_ITEMS.values())[i]['price_eur']}€")

        success = input("Identify the goal items: ")

        if "-" in success:
            success = list(range(int(success.split("-")[0]), int(success.split("-")[1])+1))
        else:
            success = success.split()

        for i in success:
            SUCCESSFUL_ITEMS.append(list(POSSIBLE_ITEMS.keys())[int(i)-1])
        
        print(f"Successful items: {SUCCESSFUL_ITEMS}")

        save()
    
    else:
        with open("resources/case_info.json", "r") as f:
            CASE_INFO = json.load(f)

        with open("resources/items_info.json", "r") as f:
            ITEMS_INFO = json.load(f)
        
        with open("resources/possible_items.json", "r") as f:
            POSSIBLE_ITEMS = json.load(f)
        
        with open("resources/successful_items.json", "r") as f:
            SUCCESSFUL_ITEMS = json.load(f)
    
    print("Starting the simulation...")

    simulations = int(input("Enter the number of simulations to run: "))
    balances = input("Enter the balances to run: ").split()

    for b in balances:
        balance = float(b)
        case_price = CASE_INFO["fields"]["price_eur"]

        threads = []

        for i in range(simulations):
            # use threading to avoid blocking the main thread
            t = threading.Thread(target=simulate, args=(balance,case_price, ))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f"Success rate: {round(SUCCESS_RATE.count(True)/simulations*100, 2)}%")
        print(f"Average balance: {round(sum(SUCCESS_BALANCE)/len(SUCCESS_BALANCE), 2)}€")

        plt.hist(SUCCESS_BALANCE, bins=20, color="skyblue", edgecolor="black")
        plt.xlabel("Balance")
        plt.ylabel("Frequency")
        plt.title("Balance distribution")
        plt.savefig(f"resources/{CASE_INFO['id']}-{balance}.png")
        plt.clf()

        plt.hist(SUCCESS_COUNTER, bins=20, color="skyblue", edgecolor="black")
        plt.xlabel("Cases")
        plt.ylabel("Frequency")
        plt.title("Cases distribution")
        plt.savefig(f"resources/{CASE_INFO['id']}-{balance}-cases.png")
        plt.clf()

        SUCCESS_BALANCE = []
        SUCCESS_RATE = []
        SUCCESS_COUNTER = []

    
    









