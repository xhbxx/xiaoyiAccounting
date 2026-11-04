-- 在现有记账数据库执行，仅新增按账本和月份保存的预算表。
CREATE TABLE IF NOT EXISTS monthly_budgets (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ledger_id INT UNSIGNED NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    CONSTRAINT uq_budget_period UNIQUE (ledger_id, year, month),
    CONSTRAINT fk_budget_ledger FOREIGN KEY (ledger_id) REFERENCES ledgers(id)
);
