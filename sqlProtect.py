
__BANNED_WORDS = [
    "select",
    "insert",
    "update",
    "delete",
    "drop",
    "truncate",
    "alter",
    "create",
    "exec",
    "union",
    "declare",
    "cast",
    "convert",
    "information_schema",
    "sysobjects",
    "syscolumns",
    "xp_cmdshell",
    "sp_executesql",
    "sp_exec",
    "sp_",
    "sys.",
    "db_",
    "table",
    "column",
    "where",
    "or",
    "and",
    "--",
    ";",
    "/*",
    "*/",
    "@@",
    "@",
    "char",
    "nchar",
    "varchar",
    "nvarchar",
    "alter",
    "begin",
    "cast",
    "create"]
# инкапсуляция итить твою мать

def get_banned_words():
    return __BANNED_WORDS

# это выглядит жалко и от этого веет слабостью как бы сказал сайтама из ванпанчмена, но все мы так начанали