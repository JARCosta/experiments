import random

from matplotlib import pyplot as plt

table = list(range(0, 37))
# print(table, 1/(1/(len(table)-1))-1)

bet_dozen = list(range(13, 25))
bet_dozen = [bet_dozen, 1/(len(bet_dozen)/(len(table)-1))]
print(bet_dozen)
bet_six_line = list(range(13, 19))
bet_six_line = [bet_six_line, 1/(len(bet_six_line)/(len(table)-1))]
print(bet_six_line)
bet_column = list(range(0+2, 37, 3))
bet_column = [bet_column, 1/(len(bet_column)/(len(table)-1))]
print(bet_column)

bets = [bet_dozen, bet_column, bet_six_line]
bets_names = ['Dozen', 'Column', 'Six Line']

def strat(bet_size):
    return [4*bet_size, 4*bet_size, 2*bet_size]

def run(bank=400, bet_budget=400, bet_size=1, bet_step=1, verbose=False):

    bank_history = []
    bet_history = []
    return_history = []
    reset_point_history = []
    bet_budget_history = []
    
    reset_point = bank

    bank_history.append(bank)
    bet_history.append(0)
    return_history.append(0)
    reset_point_history.append(reset_point)
    bet_budget_history.append(bank-bet_budget)
    

    for run in range(1000):

        if verbose:
            print('Bet size:', bet_size)
            print("Bets:", strat(bet_size), sum(strat(bet_size)))
        bet_history.append(sum(strat(bet_size)))

        bank -= sum(strat(bet_size))
        if verbose:
            print('Bank:', bank)

        
        roll = random.choice(table)
        if verbose:
            print("Roll:", roll)

        return_ = []
        for bet_ix in range(len(bets)):
            if roll in bets[bet_ix][0]:
                if verbose:
                    print('Hit', bets_names[bet_ix], strat(bet_size)[bet_ix], bets[bet_ix][1], strat(bet_size)[bet_ix]*bets[bet_ix][1])
                return_.append(round(strat(bet_size)[bet_ix]*bets[bet_ix][1], 3))
            else:
                return_.append(0)
        
        if verbose:
            print("Won:", sum(return_))
        return_history.append(sum(return_))

        if bank < 0:
            if verbose:
                print('BUSTED')
            return "bank < 0", run, bank_history, bet_history, return_history, reset_point_history, bet_budget_history
        bank = round(bank + sum(return_), 3)
        bank_history.append(bank)

        if verbose:
            print("New bank:", bank)

        if sum(return_) == 0:
            bet_size = round(bet_size + bet_step, 3)

        if bank > reset_point:
            if verbose:
                print('RESET')
            reset_point = bank
            bet_size = bet_step
            bet_budget_history.append(bank-bet_budget)
        else:
            bet_budget_history.append(bet_budget_history[-1])
        reset_point_history.append(reset_point)

        if bank < bet_budget_history[-1]:
            if verbose:
                print('STOPPED')
            return "bank < bet_budget_history[-1]", run, bank_history, bet_history, return_history, reset_point_history, bet_budget_history
        if verbose:
            print()
    
    return "yo", run, bank_history, bet_history, return_history, reset_point_history, bet_budget_history




# reason, run, bank_history, bet_history, return_history, reset_point_history, bet_budget_history = run(bank=40, bet_budget=40, bet_size=0.1, bet_step=0.1)
# print(reason, run, bank_history[-1])

# plt.plot(bank_history)
# plt.plot(bet_history)
# plt.plot(return_history)
# plt.plot(reset_point_history)
# plt.plot(bet_budget_history)
# plt.legend(['Bank', 'Bet', 'Return', 'Reset Point', 'Accumulated Bet', 'Bet Budget'])
# plt.show()


col = 100
row = 100

# fig, ax = plt.subplots(row, col, figsize=(20, 10))

runs_histogram = []
bank_histogram = []
stoppages_histogram = []


reason_all = []
run_num_all = []
bank_history_all = []
bet_history_all = []
return_history_all = []
reset_point_history_all = []
bet_budget_history_all = []

for i in range(row):
    for j in range(col):
        reason, run_num, bank_history, bet_history, return_history, reset_point_history, bet_budget_history = run(bank=40, bet_budget=40, bet_size=0.1, bet_step=0.1)
        reason_all.append(reason)
        run_num_all.append(run_num)
        bank_history_all.append(bank_history)
        bank_histogram.append(bank_history[-1])
        bet_history_all.append(bet_history)
        return_history_all.append(return_history)
        reset_point_history_all.append(reset_point_history)
        bet_budget_history_all.append(bet_budget_history)
        stoppages_histogram.append(bet_budget_history[-1])
        print(i, j)

sorted_by_bank = sorted(zip(reason_all, run_num_all, bank_history_all, bet_history_all, return_history_all, reset_point_history_all, bet_budget_history_all), key=lambda x: x[6][-1])
reason_all, run_num_all, bank_history_all, bet_history_all, return_history_all, reset_point_history_all, bet_budget_history_all = zip(*sorted_by_bank)


# for i in range(len(bank_history_all)):
#     reason = reason_all[i]
#     run_num = run_num_all[i]
#     bank_history = bank_history_all[i]
#     bet_history = bet_history_all[i]
#     return_history = return_history_all[i]
#     reset_point_history = reset_point_history_all[i]
#     bet_budget_history = bet_budget_history_all[i]
#     ax[i//col, i%col].plot(bank_history)
#     ax[i//col, i%col].plot(bet_history)
#     ax[i//col, i%col].plot(return_history)
#     ax[i//col, i%col].plot(reset_point_history)
#     ax[i//col, i%col].plot(bet_budget_history)
#     # ax[i//col, i%col].legend(['Bank', 'Bet', 'Return', 'Reset Point', 'Accumulated Bet', 'Bet Budget'])
#     # ax[i//col, i%col].set_title(f"Run {run_num}")
#     runs_histogram.append(run_num)
#     bank_histogram.append(bank_history[-1])
# plt.show(block=False)

fig, ax = plt.subplots(1, 3, figsize=(30, 10))
ax[0].hist(run_num_all, bins=100)
ax[0].set_title('Runs Histogram')
ax[1].hist(bank_histogram, bins=100)
ax[1].set_title('Bank Histogram')
ax[2].hist(stoppages_histogram, bins=100)
ax[2].set_title('Stoppages Histogram')
plt.show()




