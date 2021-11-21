
# A list of SQL statements to exclude from publishing to Slack
# https://dev.mysql.com/doc/refman/8.0/en/sql-server-administration-statements.html
SQL_STATEMENTS = [
    "show",
    "use",
    "set",
    "describe",
    "explain",
    "help" "analyze",
    "check",
    "checksum",
    "install",
    "uninstall",
    "binlog",
    "cache",
    "flush",
    "load",
    "commit",
    "rollback",
    "tables"
]

# A list of keywords situated in the middle of SQL statements
SQL_KEYWORDS = [
    "routine_schema",
    "information_schema",
    "database()",
    "count(1)",
    "@@session.tx_isolation",
    "@@session.auto_increment_increment",
    "@@global.character_set_server,@@global.collation_server",
    "@@global.max_allowed_packet",
    "@@sql_mode",
    "@@event_scheduler",
    "@@default_storage_engine",
    "@@default_tmp_storage_engine",
    "@@GLOBAL.lower_case_table_names"
]
