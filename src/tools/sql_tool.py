import re
from sqlalchemy import select, and_, or_, func
from src.db import transactions, engine_for


def validate_id(transaction_id):
    if not re.fullmatch(r'TXN_\d{7}', transaction_id):
        raise ValueError('Use TXN_ followed by exactly seven digits, e.g. TXN_0000002')
    return transaction_id


class SQLTool:
    """Only fixed, parameterized SELECTs. There is deliberately no execute-SQL method."""
    def __init__(self, settings):
        self.engine = engine_for(settings.read_database_url or settings.database_url, readonly=True)

    def transaction(self, transaction_id):
        validate_id(transaction_id)
        with self.engine.connect() as conn:
            row = conn.execute(select(transactions).where(
                transactions.c.transaction_id == transaction_id)).mappings().first()
        if row is None:
            raise LookupError(f'Transaction {transaction_id} was not found')
        return dict(row)

    def _before(self, tx):
        # Same-step ordering is unknown in PaySim; exclude the whole current step.
        return transactions.c.step < tx['step']

    def history(self, tx, limit=50, counterparties=False):
        account = (transactions.c.destination_account == tx['destination_account'] if counterparties
                   else transactions.c.origin_account == tx['origin_account'])
        with self.engine.connect() as conn:
            rows = conn.execute(select(transactions).where(account, self._before(tx)).order_by(
                transactions.c.step.desc(), transactions.c.row_number.desc()).limit(max(1, min(limit, 100)))).mappings()
            return [dict(r) for r in rows]

    def velocity(self, tx, window=24):
        if not 1 <= window <= 168:
            raise ValueError('Velocity window must be between 1 and 168 steps')
        with self.engine.connect() as conn:
            row = conn.execute(select(func.count().label('count'),
                func.coalesce(func.sum(transactions.c.amount), 0).label('total_amount'),
                func.avg(transactions.c.amount).label('average_amount'),
                func.max(transactions.c.amount).label('maximum_amount'),
                func.count(func.distinct(transactions.c.destination_account)).label('unique_destinations'))
                .where(transactions.c.origin_account == tx['origin_account'], self._before(tx),
                       transactions.c.step >= max(0, tx['step'] - window))).mappings().one()
        return dict(row, window_steps=window, scope='Loaded rows only; excludes current step')

    def similar(self, tx, limit=20):
        with self.engine.connect() as conn:
            rows = conn.execute(select(transactions).where(self._before(tx),
                transactions.c.transaction_type == tx['transaction_type'],
                transactions.c.amount.between(tx['amount']*.8, tx['amount']*1.2)).order_by(
                func.abs(transactions.c.amount - tx['amount'])).limit(min(max(limit, 1), 50))).mappings()
            return [dict(r) for r in rows]
