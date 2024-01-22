import sqlite3


def dict_factory(cursor: sqlite3.Cursor) -> list[dict[str, object]]:

    """
    Converts a list of tuples to a list of dictionaries.

    :param cursor: SQLite database cursor
    :return: List of dictionaries
    """

    output = []
    for row in cursor.fetchall():
        output.append(
            {column[0]: row[index] for index, column in enumerate(cursor.description)}
        )

    return output
