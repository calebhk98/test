-- =============================================================================
-- Database users with least-privilege grants.
--
--   fhrs_admin : full DML/DDL on food_hygiene  -- used only by the ETL loader
--   fhrs_app   : SELECT only on food_hygiene    -- used by the web application
--
-- The web app NEVER connects with write access: a read-only account is the
-- "appropriate privilege" for a query-only application and limits the blast
-- radius of SQL injection or bugs.
-- =============================================================================

-- Loader account (used by etl/02_load.js)
CREATE USER IF NOT EXISTS 'fhrs_admin'@'localhost' IDENTIFIED BY 'admin_pw_change_me';
GRANT ALL PRIVILEGES ON food_hygiene.* TO 'fhrs_admin'@'localhost';

-- Read-only application account (used by webapp/server.js)
CREATE USER IF NOT EXISTS 'fhrs_app'@'localhost' IDENTIFIED BY 'app_pw_change_me';
CREATE USER IF NOT EXISTS 'fhrs_app'@'127.0.0.1' IDENTIFIED BY 'app_pw_change_me';
GRANT SELECT ON food_hygiene.* TO 'fhrs_app'@'localhost';
GRANT SELECT ON food_hygiene.* TO 'fhrs_app'@'127.0.0.1';

FLUSH PRIVILEGES;
