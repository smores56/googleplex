#!/bin/bash

eval $( cat $PWD/googleplex/.env | xargs )

run_command() {
    PGPASSWORD=$DB_PASS psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "$@"
}

SELECT_TABLES="SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
TABLES=$( run_command "$SELECT_TABLES" | tail -n +4 | head -n -2 )

for t in $TABLES; do DROP_TABLES=$DROP_TABLES"DROP TABLE \"$t\" CASCADE;"; done

run_command "$DROP_TABLES"
