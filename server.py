"""Local Flask server. Start this before opening the Tkinter window."""

from pathlib import Path
import sqlite3

from flask import Flask, g, jsonify, request


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
        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5)
            )
        """)
        db.commit()


@app.errorhandler(sqlite3.Error)
def database_error(error):
    app.logger.error("SQLite error: %s", error)
    return jsonify(error="Could not access the game database. Please try again."), 500


def read_game_form():
    title = request.form.get("title", "").strip()
    genre = request.form.get("genre", "").strip()
    rating = request.form.get("rating", "").strip()
    if not title or not genre:
        raise ValueError("Enter both a title and a genre.")
    if rating not in ("1", "2", "3", "4", "5"):
        raise ValueError("Choose a whole-number rating from 1 to 5.")
    return title, genre, int(rating)


@app.get("/games")
def list_games():
    minimum = request.args.get("min_rating", "1")
    if minimum not in ("1", "2", "3", "4", "5"):
        return jsonify(error="Minimum rating must be from 1 to 5."), 400
    rows = get_db().execute(
        "SELECT id, title, genre, rating FROM games WHERE rating >= ? "
        "ORDER BY title COLLATE NOCASE, id", (int(minimum),)
    )
    return jsonify(games=[dict(row) for row in rows])


@app.post("/games/add")
def add_game():
    try:
        values = read_game_form()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    db = get_db()
    cursor = db.execute("INSERT INTO games (title, genre, rating) VALUES (?, ?, ?)", values)
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
        "UPDATE games SET title = ?, genre = ?, rating = ? WHERE id = ?",
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
