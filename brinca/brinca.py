import csv
import numpy as np

dataset = []
with open('brinca.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        dataset.append(row)
dataset = np.array(dataset)[2:]
dataset = dataset[100:].astype(float)

train, test = np.split(dataset, [int(0.8 * len(dataset))])
# print(train.shape, test.shape)

# train = dataset

dates, premium, size, risk_free, short_term, long_term, value, momentum = train[:, 0], train[:, 1], train[:, 2], train[:, 3], train[:, 4], train[:, 5], train[:, 6], train[:, 7]


def SR(returns):
    return (12 * np.average(returns)) / (np.sqrt(12) * np.std(returns))

aim = np.vstack([value, momentum]).T
aim = (aim @ np.array([[0.5], [0.5]])).flatten()
aim = SR(aim)

play = np.vstack([size, risk_free, short_term, long_term]).T
play = np.vstack([size, short_term, long_term]).T


results = np.zeros((play.shape[1], play.shape[1], 101))

for col1_idx in range(play.shape[1]):
    for col2_idx in range(col1_idx + 1, play.shape[1]):
        col1, col2 = play[:, col1_idx], play[:, col2_idx]
        
        for ratio1 in np.arange(0, 1.01, 0.01):
            ratio1, ratio2 = round(ratio1, 2), round(1 - ratio1, 2)
            weighted_sum = (col1 * ratio1) + (col2 * ratio2)
            result = SR(weighted_sum)
            results[col1_idx, col2_idx, int(ratio1 * 100)] = result - aim
        
max = np.max(results)
# print(max)
# print(np.unravel_index(np.argmax(results), results.shape))
col1_idx, col2_idx, ratio1 = np.unravel_index(np.argmax(results), results.shape)
col_name1 = ['size', 'short_term', 'long_term'][col1_idx]
col_name2 = ['size', 'short_term', 'long_term'][col2_idx]
ratio1 = ratio1 / 100
ratio2 = 1 - ratio1
print(f"Best combination: {col_name1} and {col_name2} with ratios {ratio1:.2f} and {ratio2:.2f}")
max_aim, max_result = np.max(aim), max + np.max(aim)
print(f"Max difference: {max:.2f} (max.aim: {max_aim:.2f}, max.result: {max_result:.2f})")








