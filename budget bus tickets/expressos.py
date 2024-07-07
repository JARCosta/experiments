import requests
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By



trips = [
    { "start": "Coimbra", "end": "Lisboa (Sete Rios)", "prices": []},
    { "start": "Lisboa (Sete Rios)", "end": "Coimbra", "prices": []},
]

for trip in trips:

    driver = webdriver.Chrome()
    driver.get("https://rede-expressos.pt/pt/horarios-bilhetes")
    time.sleep(1)

    origem = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/main/div/div[1]/section/div/div[2]/div[1]/div[1]/div/div/div/div/div/input")
    origem.clear()
    origem.send_keys(trip["start"])
    origem.send_keys(Keys.RETURN)
    origem.send_keys(Keys.DOWN)
    origem.send_keys(Keys.RETURN)

    destino = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/main/div/div[1]/section/div/div[2]/div[1]/div[3]/div/div/div/div/div/input")
    destino.clear()
    destino.send_keys(trip["end"])
    destino.send_keys(Keys.RETURN)
    destino.send_keys(Keys.DOWN)
    destino.send_keys(Keys.RETURN)

    drop_down = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/main/div/div[1]/section/div/div[2]/div[3]/div[1]/div[1]/div")
    drop_down.click()

    time.sleep(1)

    increase_jovem = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/main/div/div[1]/section/div/div[2]/div[3]/div[1]/div[2]/div[2]/div[2]/span").find_elements(By.TAG_NAME, "svg")[1]
    increase_jovem.screenshot("screenshot.png")
    increase_jovem.click()

    decrease_adulto = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/main/div/div[1]/section/div/div[2]/div[3]/div[1]/div[2]/div[1]/div[2]/span").find_elements(By.TAG_NAME, "svg")[0]
    decrease_adulto.click()

    search = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/main/div/div[1]/section/div/div[2]/div[3]/div[2]/button")
    search.click()

    time.sleep(10)

    prices_elements = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div/main/div/div[2]/section/div/div[2]/div/div/div[2]/div/div[2]").find_elements(By.XPATH, "*")
    prices = []
    for element in prices_elements:
        departure = element.find_element(By.TAG_NAME, "p").text
        price = element.find_element(By.TAG_NAME, "h2").text
        prices.append({
            "departure": departure,
            "price": float(price[:-1].replace(",", "."))
            })
    trip["prices"] = prices

    driver.close()

def look(last_message: str):

    token = "6731395929:AAE0uPmr90EvjO1qIyVcJ6Lt6dec3F0NldA"
    url = f"https://api.telegram.org/bot{token}"
    params = {"chat_id": "6449165312", "text": "Hello World"}


    cheap = {}
    for trip in trips:
        temp_trip = []
        for price in trip["prices"]:
            if price["price"] < 10:
                temp_trip.append([price["departure"], price["price"]])
        if len(temp_trip) > 0:
            cheap[trip["start"] + " - " + trip["end"]] = temp_trip

    if len(cheap) > 0:
        message = "Found cheap tickets for:\n" 
        for trip in cheap:
            message += trip + "\n"
            for price in cheap[trip]:
                message += "    " + price[0] + " - " + str(price[1]) + "€\n"

        if message != last_message:
            params = {"chat_id": "6449165312", "text": message}
            r = requests.get(url + "/sendMessage", params=params)
            print(r.text)
            return message
    else:
        print("No cheap tickets found")
        return last_message

def main():
    
    last_message = ""
    while True:
        last_message =  look(last_message)
        time.sleep(60*15)


main()
        
