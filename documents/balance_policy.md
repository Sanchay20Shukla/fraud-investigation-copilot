# Balance Anomaly Review
Synthetic portfolio policy, version 1.0.

## 5.1 Balance reconciliation
For outgoing TRANSFER, CASH_OUT, PAYMENT and DEBIT transactions, compare the origin balance before minus amount with the balance after. For CASH_IN, compare the origin balance before plus amount with the balance after. A nonzero reconciliation error is an indicator for investigation, not proof of fraud. Some PaySim balances are missing or zero by design.

## 5.2 Account depletion
Review a transaction that leaves the origin account with a zero balance when its prior balance was positive. Account depletion can also be legitimate. Compare the amount-to-balance ratio with prior behavior when history is available.
