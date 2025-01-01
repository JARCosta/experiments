import csv


header = ['name', 'url', 'username', 'email', 'password', 'note', 'totp', 'vault']


PASSWORDS = []
with open("Avira_Export-2024_12_18.csv", "r") as f:
    logins = list(csv.reader(f))
    # print(logins[0])
    logins = logins[1:]
    
    for i in logins:
        if "@" in i[2]:
            i[3] = i[2]
            i[2] = ""
    
        i[1] = i[1].replace("www.", "")

    # print(repr(logins[1]))
    PASSWORDS.extend(logins)
# print(len(PASSWORDS))



with open("Vivaldi Passwords.csv", "r") as f:
    logins = list(csv.reader(f))
    # logins[0].insert(3, "email")
    # print(logins[0])
    logins = logins[1:]

    for i in logins:
        i.insert(3, "")
        i[0] = ""
        i[1] = i[1].replace("https://", "")
        i[1] = i[1].replace("http://", "")
        if "//" not in i[1]:
            i[1] = i[1].split("/")[0]
        i[1] = i[1].replace("www.", "")

        
        if "@" in i[2]:
            i[3] = i[2]
            i[2] = ""

    
    # print(repr(logins[1]))
    PASSWORDS.extend(logins)
# print(len(PASSWORDS))

PASSWORDS.sort()

logins = []
for i in PASSWORDS:
    duplicate = False
    for j in logins:
        
        if i[1] == j[1]:
            if i[2] == j[2] and i[3] == j[3] and i[4] == j[4]: # complete duplicates, ignote
                # print("complite duplicated", i, j)
                duplicate = True
                break
            if i[2] == j[2] and i[3] == j[3]: # different passwords, keep both
                # print("different passwords", i, j)
                break
            if ((i[2] == j[2] != "") or (i[3] == j[3] != "") and i[4] == j[4]): # one of the login creds is different
                # print("somewhat duplicate", i, j) 

                if (i[2] == "" and j[2] != ""):
                    # print("keep j")
                    logins.pop(logins.index(i))
                    break
                if (i[2] != "" and j[2] == ""):
                    # print("keep i")
                    duplicate = True
                    break
                if (i[3] == "" and j[3] != ""):
                    # print("keep j")
                    logins.pop(logins.index(i))
                    break
                if (i[3] != "" and j[3] == ""):
                    # print("keep i")
                    duplicate = True
                    break
                else:
                    print(i,j)
        #     if i[2] == j[2]:
        #         if i[3] == j[3]:
        #             if i[4] == j[4]: # complete duplicate, skip
        #                 duplicate = True
        #             else: # different passwords, keep both
        #                 print("different passwords", i, j)
        #         else: # different emails, keep both
        #             pass
        #     else:
        #         print(i, j)
    if not duplicate:
        logins.append(i)





with open("output.csv", "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(logins)