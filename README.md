# Game Library Tracker

Record the games you have played, their genres, and your ratings from 1 to 5. Select a minimum rating to find your favorites. The Tkinter desktop window sends requests to a local Flask server. Flask owns the SQLite database and returns JSON.

## Run on Windows

Install a standard desktop build of Python 3.10 or later with Tkinter. Extract the project and open PowerShell in the folder containing `server.py`. Run the following commands once to create an environment and install Flask.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Terminal 1** starts Flask. Startup creates `games.sqlite3` and its table if missing. Subsequent starts keep existing games. Leave this terminal open.

```powershell
.\.venv\Scripts\python.exe server.py
```

**Terminal 2** opens the desktop window. Start it in the same project folder. The window connects automatically to `127.0.0.1:5050`.

```powershell
.\.venv\Scripts\python.exe app.py
```

Choose **Add game**, enter a title and genre, choose a rating, and click **Save**. To edit or delete, first select a row. **All** clears the minimum-rating filter. **Refresh** reloads the current list.

**Terminal 3** exports the whole library, including games hidden by the current filter. With Flask running, use the following command in the project folder.

```powershell
.\.venv\Scripts\python.exe report.py
```

Open `game_report.txt` beside `report.py`. The helper prints its output path or the reason it failed. To stop the application, close the desktop window and press Ctrl+C in the Flask terminal.

## Trace one Save click

1. In `app.py`, the Save callback inside `GameLibrary.open_editor` collects the three field values in a dictionary.
2. In `client.py`, `request_json` encodes the dictionary as form bytes. Passing those bytes to `urlopen` sends a POST to `/games/add` with a five-second timeout.
3. In `server.py`, `add_game` calls `read_game_form` to check the title, genre and rating. Valid data goes into an INSERT with three SQL placeholders. The route commits and returns the new ID and a message with HTTP 201.
4. Tkinter closes the editor and requests the list again. Flask reads SQLite, then Tkinter displays the returned records. The current minimum rating still applies.

The row's database ID stays the same if its title or rating changes. The edit and delete routes use that ID in their WHERE clauses. Two games can share a title.

## Course topics

| Topic | File and function or class |
| --- | --- |
| Functions, conditions, loops, lists and dictionaries | `server.py`, `read_game_form` and `list_games`, validate fields and return a list of game dictionaries. `app.py`, `GameLibrary.refresh`, loops over that list. |
| Classes and Tkinter | `app.py`, `GameLibrary`, owns the table, selection, filter, and add/edit dialog. |
| Client/server and exceptions | `client.py`, `request_json`, sends GET or form-encoded POST, decodes JSON, and handles HTTP errors before connection errors. A refused connection or timeout produces feedback in the open window. |
| Flask | `server.py`, `list_games`, `add_game`, `edit_game`, and `delete_game`, implement the JSON routes. Invalid fields return 400. An edit or delete of a missing ID returns 404. |
| SQLite | `server.py`, `init_db`, creates the schema. `get_db` gives each request its own connection. `close_db` closes it on teardown. The writing routes commit their changes. |
| Threads, files and exceptions | `report.py`, `main`, fetches all games, starts one writer thread and waits with `join()`. `write_report` uses a UTF-8 file with a context manager and handles file errors. |

## Test results

The checks below exercised real Tkinter widgets and a temporary SQLite database. An in-process adapter passed the desktop client's encoded requests to Flask's test client. Connection failures and timeouts were simulated for the recovery checks.

| Check | Observed result |
| --- | --- |
| Add and list games | Three games appeared with distinct IDs. |
| Edit or delete a selected game | Editing a title and rating changed only that ID. Cancel kept the row. Confirm removed only the selected ID. |
| Invalid fields and ratings | Empty fields, 0, 6, 4.5 and nonnumeric input returned 400. The editor stayed open with an error after an invalid Save. |
| Stale record in two windows | Deleting a game in the first window and saving an edit in the second returned 404 and displayed the missing-record message. |
| Minimum rating and empty states | Choosing 4 showed games rated 4 or 5. Empty libraries and filters with no matches displayed different messages. |
| Persistence | Reopening the database and creating a new window retained the surviving games. |
| Failure and recovery | A refused request and a timeout showed errors. Refresh worked again in the same window when the test connection recovered. |
| Text export | The report contained the titles, genres, and ratings, including an accented title. Empty data produced an empty-library report. An unavailable output directory produced a file error. |

**Live check before presenting.** Start both programs using the commands above. Add a game and close both programs. Restart them and verify that it is still there. Stop only Flask, click Refresh, then restart Flask and click Refresh in the same window. This checks the actual localhost connection on the presentation machine.

## Presentation and submission

Use `GameLibraryTracker_slides.pdf` alongside the running app. Allow about one minute each for the idea and architecture, six minutes for the live demo, and two minutes to explain a route, class, query, and Git commits. Practice tracing Save and explaining why a stale edit returns 404.

Publish the local repository to your GitHub account. If private, invite the instructor's GitHub account `majedoh` and verify access. Make the ZIP match the final repository files. Name it `Project_StudentID.zip` with your actual ID. In Blackboard, include your name, student ID, and GitHub URL. Check Blackboard for your deadline and presentation slot.

## Credits

The Advanced Programming 462 individual project brief provided the application requirements and the client/server communication pattern. OpenAI Codex assisted with implementation, testing, documentation, and presentation materials.
