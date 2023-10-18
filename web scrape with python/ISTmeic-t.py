import json
import requests
from bs4 import BeautifulSoup
import math

def return_mid_and_after(full_string: str, left_limit: str, right_limit: str):
    after = full_string.split(left_limit, 1)[1]
    mid, after = after.split(right_limit, 1)
    return mid, after



def load_UCs():

    api_url = f"https://fenix.tecnico.ulisboa.pt/cursos/meic-t/curriculo"

    response = requests.get(api_url)

    soup = BeautifulSoup(response.content, "html.parser")

    level = soup.find("div", class_="tab-pane fade in active")
    
    for i in range(3):
        level = level.find("div", class_="level")
    level = level.find_all("div", class_="level")[1]

    level = level.prettify()
    rest = level

    with open(f"data/ISTmeic-t/UCs.html", "w") as outfile:
        outfile.write(rest)

    subjects = {}

    while True:
        next_subject = len(rest.split('<h4>\n  ')[0])
        next_CU = len(rest.split('style="font-size: 120%">\n     ')[0])

        if next_subject == next_CU:
            with open(f"data/ISTmeic-t/UCs.json", "w") as outfile:
                outfile.write(json.dumps(subjects, indent=4, ensure_ascii=False).encode('utf8').decode())
            with open(f"data/ISTmeic-t/UCs.txt", "w") as outfile:
                for i in subjects:
                    outfile.write(f"{i}:\n")
                    for j in subjects[i]:
                        print(subjects[i][j])
                        time = subjects[i][j][1].split(", ")[1].replace(" ", "").replace("Sem.", "S")
                        outfile.write(f"\t{time} {j}\n")
                    outfile.write("\n")
            break

        if next_subject < next_CU:
            subject, rest = return_mid_and_after(rest, '<h4>\n  ', '\n </h4>')
            subjects[subject] = {}

        else:
            href, rest = return_mid_and_after(rest, 'href="', '" style="font-')
            name, rest = return_mid_and_after(rest, 'size: 120%">\n     ', '\n    </a>')
            time, rest = return_mid_and_after(rest, 'div>\n     ', '\n    </div>')
            subjects[subject][name] = []
            subjects[subject][name].extend([href, time])


def filter_time(times: list = [], courses: list = [], UCs: list = []):

    with open(f"data/ISTmeic-t/UCs.json", "r") as infile:
        data = json.load(infile)

    filtered_data = {}

    # Iterate through each key (course) and its values (course details)
    for course, details_list in data.items():
        filtered_details = {}
        
        
        if course not in courses and courses != []:
            continue

        for i in UCs:
            if i in details_list:
                filtered_details[i] = details_list[i]

        # Iterate through each detail in the details_list
        for detail in details_list:
            # if times == []:
            #     filtered_details[detail] = details_list[detail]
            # else:
                for time in times:
                    if time in details_list[detail]:
                        filtered_details[detail] = details_list[detail]

        if filtered_details:
            filtered_data[course] = filtered_details

    for i in filtered_data:
        found = len(filtered_data[i])
        total = len(data[i])
        filtered_data[i]["found"] = f"{found}/{total}"
    
    # Convert the filtered_data to JSON format
    filtered_json = json.dumps(filtered_data, indent=4, ensure_ascii=False).encode('utf8').decode()

    # Write the filtered_data to a file
    with open(f"data/ISTmeic-t/UCs_filtered.json", "w") as outfile:
        
        outfile.write(filtered_json)


    with open(f"data/ISTmeic-t/UCs_filtered.txt", "w") as outfile:
        for i in filtered_data:
            outfile.write(f"{i}:\n")
            for j in filtered_data[i]:
                if j != "found":
                    outfile.write(f"\t{j}\n")
            outfile.write("\n")

load_UCs()
filter_time([], [])

times = ["Ano 1, P 4"]
courses = ["Engenharia e Ciência de Dados", "Robótica Inteligente", "Inteligência Artificial", "Engenharia de Software"]
UCs = ["Computação em Nuvem e Virtualização"]


filter_time([], courses, [])
filter_time(times, courses, [])
filter_time([], [], UCs)
filter_time(times, [], [])


