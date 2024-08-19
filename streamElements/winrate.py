import matplotlib


with open('resources/bets.txt') as f:
    bets = f.readlines()

bets_n = []
for i in bets:
    if "won the contest" in i:
        bets_n.append(i)
bets = bets_n

bets = [float(i.split("of all bets and ")[1].split("% of the total pot!")[0]) for i in bets]
winrate = [1 if i < 50 else 0 for i in bets]
rolling_average = [sum(bets[:i])/i for i in range(1, len(bets))] 
winrate_rolling_average = [sum(winrate[:i])/i for i in range(1, len(winrate))]

win = [1 if i < 50 else 0 for i in bets]

print(win.count(1)/len(win))

# line chart
import matplotlib.pyplot as plt
import numpy as np

# plt.plot(bets)
# plt.plot(rolling_average)
# plt.plot(winrate)
plt.plot(winrate_rolling_average)

# bar chart with average in batches of 5

x = np.arange(0, len(bets), 5)
print([sum(winrate[i:i+5])/5 for i in x])
y = [(sum(winrate[i:i+5])/5) for i in x]

plt.bar(x, y, width=4.5)





plt.show()

