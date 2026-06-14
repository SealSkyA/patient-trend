import os
import glob
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

MIGRATIONS_DIR = os.path.dirname(__file__)


def run_migrations(conn):
    """Run all SQL migration files in order. Skips duplicate indexes gracefully."""
    files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    executed = 0
    for f in files:
        filename = os.path.basename(f)
        with open(f, "r") as fh:
            sql = fh.read()
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                executed += 1
            except OperationalError as e:
                code = e.orig.args[0] if e.orig and e.orig.args else 0
                if code == 1061:
                    pass
                else:
                    raise
    if executed:
        print(f"[migration] Executed {executed} new statement(s) from {len(files)} migration file(s)")
