-- Local Docker credentials only. Replace before any deployment beyond localhost.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE ROLE copilot_reader LOGIN PASSWORD 'local_reader';
CREATE ROLE copilot_audit LOGIN PASSWORD 'local_audit';
GRANT CONNECT ON DATABASE copilot TO copilot_reader, copilot_audit;
GRANT USAGE ON SCHEMA public TO copilot_reader, copilot_audit;
ALTER ROLE copilot_reader SET default_transaction_read_only = on;
