-- 小翼记账空库初始化。
-- 在数据库管理工具中先选中与 DB_NAME 对应的数据库，再以 UTF-8 编码执行本文件。
-- 表结构与已运行的本地数据库一致，字符集统一使用 utf8mb4。
-- 本文件包含月预算表及系统预设类别，可串行重复执行以恢复中断的初始化。

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    openid VARCHAR(64) NOT NULL,
    unionid VARCHAR(64) DEFAULT NULL,
    nick_name VARCHAR(64) DEFAULT NULL,
    avatar_url VARCHAR(512) DEFAULT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY openid (openid),
    UNIQUE KEY phone (phone),
    KEY idx_unionid (unionid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ledgers (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    name VARCHAR(64) DEFAULT '默认账本',
    icon VARCHAR(64) DEFAULT 'book',
    color VARCHAR(16) DEFAULT '#1677ff',
    sort INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY user_id (user_id),
    CONSTRAINT ledgers_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_settings (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    default_bill_type VARCHAR(16) DEFAULT 'expense',
    theme_color VARCHAR(16) DEFAULT '#1677ff',
    last_ledger_id INT UNSIGNED DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS categories (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED DEFAULT NULL,
    name VARCHAR(64) NOT NULL,
    type VARCHAR(16) DEFAULT NULL,
    icon VARCHAR(64) DEFAULT NULL,
    sort INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_user_type_sort (user_id, type, sort)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS bills (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    ledger_id INT UNSIGNED NOT NULL,
    type VARCHAR(16) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    bill_date DATETIME NOT NULL,
    remark VARCHAR(256) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    category VARCHAR(64) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_user_led_b (user_id, ledger_id, bill_date),
    KEY idx_user_date (user_id, bill_date),
    KEY idx_ca_user (category, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS monthly_budgets (
    id INT NOT NULL AUTO_INCREMENT,
    ledger_id INT UNSIGNED NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_budget_period UNIQUE (ledger_id, year, month),
    CONSTRAINT fk_budget_ledger FOREIGN KEY (ledger_id) REFERENCES ledgers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- user_id 为 NULL 的类别属于系统预设，沿用本地数据库的类别名、图标与顺序。
START TRANSACTION;

INSERT INTO categories (user_id, name, type, icon, sort)
SELECT NULL, preset.name, preset.type, preset.icon, preset.sort
FROM (
    SELECT '餐饮' AS name, 'expense' AS type, 'food' AS icon, 1 AS sort
    UNION ALL SELECT '交通', 'expense', 'transport', 2
    UNION ALL SELECT '购物', 'expense', 'shopping', 3
    UNION ALL SELECT '娱乐', 'expense', 'entertainment', 4
    UNION ALL SELECT '医疗', 'expense', 'medical', 5
    UNION ALL SELECT '住房', 'expense', 'house', 6
    UNION ALL SELECT '学习', 'expense', 'study', 8
    UNION ALL SELECT '工资', 'income', 'salary', 1
    UNION ALL SELECT '兼职', 'income', 'parttime', 2
    UNION ALL SELECT '理财', 'income', 'finance', 3
    UNION ALL SELECT '红包', 'income', 'redpacket', 4
) AS preset
WHERE NOT EXISTS (
    SELECT 1 FROM categories AS existing
    WHERE existing.user_id IS NULL
        AND existing.name = preset.name
        AND existing.type = preset.type
);

COMMIT;
