from sqlalchemy import text
from src.config import Settings
from src.db import engine_for


def main():
    engine = engine_for(Settings().database_url)
    if engine.dialect.name != 'postgresql':
        return
    with engine.begin() as conn:
        conn.execute(text('GRANT SELECT ON transactions, policy_chunks TO copilot_reader'))
        conn.execute(text('GRANT SELECT, INSERT ON investigations, fraud_predictions TO copilot_audit'))
        conn.execute(text('GRANT SELECT, INSERT, UPDATE ON sessions TO copilot_audit'))
        if conn.scalar(text("SELECT to_regclass('public.policy_vectors')")):
            conn.execute(text('GRANT SELECT ON policy_vectors TO copilot_reader'))


if __name__ == '__main__':
    main()
