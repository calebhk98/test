// Central configuration. Credentials come from environment variables where set,
// with local-dev defaults that match db/users.sql.
module.exports = {
  db: {
    host: process.env.DB_HOST || '127.0.0.1',
    port: Number(process.env.DB_PORT || 3306),
    database: process.env.DB_NAME || 'food_hygiene',
  },
  // Loader: full privileges (DDL/DML).
  admin: {
    user: process.env.DB_ADMIN_USER || 'fhrs_admin',
    password: process.env.DB_ADMIN_PASSWORD || 'admin_pw_change_me',
  },
  // Web app: SELECT only.
  app: {
    user: process.env.DB_APP_USER || 'fhrs_app',
    password: process.env.DB_APP_PASSWORD || 'app_pw_change_me',
  },
  paths: {
    raw: __dirname + '/data/raw',
    fhrs: __dirname + '/data/raw/fhrs',
  },
};
