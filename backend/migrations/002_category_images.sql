-- 在当前记账数据库执行，为类别新增图片内容字段，可重复执行。
SET @category_image_column_exists = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'categories' AND column_name = 'icon_data'
);
SET @category_image_sql = IF(
    @category_image_column_exists = 0,
    'ALTER TABLE categories ADD COLUMN icon_data MEDIUMBLOB NULL',
    'SELECT 1'
);
PREPARE category_image_statement FROM @category_image_sql;
EXECUTE category_image_statement;
DEALLOCATE PREPARE category_image_statement;
