#!/usr/bin/env bash
# Start/stop/reset a local Postgres 16 cluster for dev + tests.
#
# There is no Docker in this environment, but real Postgres 16 server
# binaries are installed at /usr/lib/postgresql/16/bin and can be run as
# the `postgres` system user. This script drives that directly: it
# initializes a cluster under $PROJECT_ROOT/.pgdata (owned by the
# `postgres` user, as initdb requires), starts/stops it with pg_ctl, and
# creates the `outcome_dating` role + database on first start.
#
# Usage:
#   scripts/pg-dev.sh start   # idempotent: init if needed, start if not running
#   scripts/pg-dev.sh stop    # idempotent: no-op if not running
#   scripts/pg-dev.sh reset   # stop + wipe data dir + start fresh
#   scripts/pg-dev.sh status
#
# Must be run as root (so it can chown the data dir to `postgres` and
# `su postgres` to run the server as an unprivileged user).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PG_BIN="/usr/lib/postgresql/16/bin"
PGDATA_DIR_NAME="${PGDATA_DIR:-.pgdata}"
PGDATA="$PROJECT_ROOT/$PGDATA_DIR_NAME"
PGPORT="${PGPORT:-55433}"
PGHOST="127.0.0.1"
PG_LOG="$PROJECT_ROOT/.pglog"
DB_NAME="outcome_dating"
DB_ROLE="outcome_dating"
PG_USER="postgres"

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "scripts/pg-dev.sh must be run as root (it chowns .pgdata to 'postgres' and runs 'su postgres')." >&2
    exit 1
  fi
}

as_pg() {
  su "$PG_USER" -c "$1"
}

is_running() {
  # pg_ctl status exits 0 if running, 3 if stopped, 4 if data dir missing/unreadable.
  as_pg "$PG_BIN/pg_ctl status -D '$PGDATA'" >/dev/null 2>&1
}

do_init() {
  if [[ -s "$PGDATA/PG_VERSION" ]]; then
    return 0
  fi
  echo "Initializing Postgres cluster at $PGDATA ..."
  mkdir -p "$PGDATA"
  chown -R "$PG_USER":"$PG_USER" "$PGDATA"
  chmod 700 "$PGDATA"
  touch "$PG_LOG"
  chown "$PG_USER":"$PG_USER" "$PG_LOG"
  as_pg "$PG_BIN/initdb -D '$PGDATA' -U '$PG_USER' -A trust --locale=C --encoding=UTF8" >>"$PG_LOG" 2>&1
  # Force IPv4 loopback listening + our fixed dev port.
  as_pg "cat >> '$PGDATA/postgresql.conf'" <<EOF
listen_addresses = '127.0.0.1'
port = $PGPORT
EOF
  as_pg "cat >> '$PGDATA/pg_hba.conf'" <<EOF
host    all             all             127.0.0.1/32            trust
EOF
}

do_start() {
  require_root
  do_init
  if is_running; then
    echo "Postgres already running on port $PGPORT (data dir: $PGDATA)."
  else
    echo "Starting Postgres on port $PGPORT ..."
    as_pg "$PG_BIN/pg_ctl -D '$PGDATA' -l '$PG_LOG' -o '-p $PGPORT' -w start"
  fi
  wait_ready
  ensure_role_and_db
  echo "Postgres ready: postgres://$DB_ROLE@$PGHOST:$PGPORT/$DB_NAME"
}

wait_ready() {
  for _ in $(seq 1 30); do
    if as_pg "$PG_BIN/pg_isready -h $PGHOST -p $PGPORT" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  echo "Postgres did not become ready in time; see $PG_LOG" >&2
  exit 1
}

ensure_role_and_db() {
  local role_exists
  role_exists=$(as_pg "$PG_BIN/psql -h $PGHOST -p $PGPORT -U $PG_USER -d postgres -tAc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_ROLE'\"")
  if [[ "$role_exists" != "1" ]]; then
    as_pg "$PG_BIN/psql -h $PGHOST -p $PGPORT -U $PG_USER -d postgres -c \"CREATE ROLE $DB_ROLE LOGIN SUPERUSER\""
  fi
  local db_exists
  db_exists=$(as_pg "$PG_BIN/psql -h $PGHOST -p $PGPORT -U $PG_USER -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\"")
  if [[ "$db_exists" != "1" ]]; then
    as_pg "$PG_BIN/psql -h $PGHOST -p $PGPORT -U $PG_USER -d postgres -c \"CREATE DATABASE $DB_NAME OWNER $DB_ROLE\""
  fi
}

do_stop() {
  require_root
  if [[ ! -d "$PGDATA" ]]; then
    echo "No data dir at $PGDATA; nothing to stop."
    return 0
  fi
  if is_running; then
    echo "Stopping Postgres ..."
    as_pg "$PG_BIN/pg_ctl -D '$PGDATA' -w stop -m fast"
  else
    echo "Postgres is not running."
  fi
}

do_reset() {
  require_root
  do_stop || true
  echo "Wiping $PGDATA ..."
  rm -rf "$PGDATA"
  do_start
}

do_status() {
  if [[ -d "$PGDATA" ]] && is_running; then
    echo "running (port $PGPORT, data dir $PGDATA)"
  else
    echo "stopped"
  fi
}

case "${1:-}" in
  start) do_start ;;
  stop) do_stop ;;
  reset) do_reset ;;
  status) do_status ;;
  *)
    echo "Usage: $0 {start|stop|reset|status}" >&2
    exit 1
    ;;
esac
