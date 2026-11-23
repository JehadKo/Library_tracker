"""Local Flask server. Start this before opening the Tkinter window."""

from pathlib import Path
import sqlite3

from flask import Flask, g, jsonify, request

from game_fields import RATINGS, UNRATED_STATUSES


app = Flask(__name__)
app.config["DATABASE"] = Path(__file__).with_name("games.sqlite3")


def get_db():
    """Reuse one connection within a request. Flask closes it at teardown."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        # Keep the schema check and any migration in one transaction.
        db.execute("BEGIN IMMEDIATE")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(games)")}
        migrate = bool(columns) and "status" not in columns
        if migrate:
            db.execute("ALTER TABLE games RENAME TO games_legacy")
        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Rated',
                rating INTEGER,
                CHECK (
                    (status = 'Rated' AND typeof(rating) = 'integer' AND rating BETWEEN 1 AND 5)
                    OR (status IN ('Not started', 'Dropped') AND rating IS NULL)
                )
            )
        """)
        if migrate:
            db.execute("""
                INSERT INTO games (id, title, genre, rating)
                SELECT id, title, genre, rating FROM games_legacy
            """)
            # Preserve the ID counter even if the highest old ID was deleted.
            db.execute("""
                UPDATE sqlite_sequence SET seq = MAX(seq, COALESCE(
                    (SELECT seq FROM sqlite_sequence WHERE name = 'games_legacy'), 0))
                WHERE name = 'games'
            """)
            db.execute("DROP TABLE games_legacy")
        db.commit()


@app.errorhandler(sqlite3.Error)
def database_error(error):
    app.logger.error("SQLite error: %s", error)
    return jsonify(error="Could not access the game database. Please try again."), 500


def read_game_form():
    title = request.form.get("title", "").strip()
    genre = request.form.get("genre", "").strip()
    rating = request.form.get("rating", "").strip()
    status = request.form.get("status", "Rated").strip()
    if not title or not genre:
        raise ValueError("Enter both a title and a genre.")
    if status in UNRATED_STATUSES:
        if rating:
            raise ValueError(f"A game marked {status} cannot have a rating.")
        return title, genre, status, None
    if status != "Rated":
        raise ValueError("Choose a rating, Not started, or Dropped.")
    if rating not in RATINGS:
        raise ValueError("Choose a whole-number rating from 1 to 5, Not started, or Dropped.")
    return title, genre, status, int(rating)


@app.get("/games")
def list_games():
    minimum = request.args.get("min_rating")
    query = "SELECT id, title, genre, status, rating FROM games"
    parameters = ()
    if minimum is not None:
        if minimum not in RATINGS:
            return jsonify(error="Minimum rating must be from 1 to 5."), 400
        query += " WHERE rating >= ?"
        parameters = (int(minimum),)
    rows = get_db().execute(query + " ORDER BY title COLLATE NOCASE, id", parameters)
    return jsonify(games=[dict(row) for row in rows])


@app.post("/games/add")
def add_game():
    try:
        values = read_game_form()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    db = get_db()
    cursor = db.execute("INSERT INTO games (title, genre, status, rating) VALUES (?, ?, ?, ?)", values)
    db.commit()
    return jsonify(id=cursor.lastrowid, message="Game added."), 201


@app.post("/games/<int:game_id>/edit")
def edit_game(game_id):
    try:
        values = read_game_form()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    db = get_db()
    cursor = db.execute(
        "UPDATE games SET title = ?, genre = ?, status = ?, rating = ? WHERE id = ?",
        (*values, game_id),
    )
    db.commit()
    if cursor.rowcount == 0:
        return jsonify(error="This game no longer exists. Refresh your library."), 404
    return jsonify(message="Changes saved.")


@app.post("/games/<int:game_id>/delete")
def delete_game(game_id):
    db = get_db()
    cursor = db.execute("DELETE FROM games WHERE id = ?", (game_id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify(error="This game no longer exists. Refresh your library."), 404
    return jsonify(message="Game deleted.")


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5050)
