# Account and Counterparty Review
Synthetic portfolio procedure, version 1.0.

## 6.1 Previous transactions and velocity
Account history and transaction velocity must use earlier time steps only. Exclude current-step rows because ordering within a PaySim step is unknown. Report transaction count, total amount, average amount, maximum amount and unique destinations over the prior 24 steps. Results cover only the loaded dataset, which may be incomplete.

## 6.2 Counterparties and similarity
For counterparty analysis, retrieve earlier transactions to the same destination and inspect their origin accounts. Similar transactions may share a transaction type and amount within 20 percent; similarity alone does not mean they are suspicious. Do not assume common ownership from shared counterparties.
