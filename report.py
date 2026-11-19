"""Fetch the complete library and write a UTF-8 report on a worker thread."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Thread

from client import RequestError, request_json


REPORT_PATH = Path(__file__).with_name("game_report.txt")


def write_report(games, path, result):
    # Finish the new file before replacing a previously saved report.
    temporary_path = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                delete=False) as output:
            temporary_path = Path(output.name)
            output.write(f"Game Library Tracker\nTotal games: {len(games)}\n\n")
            for game in games:
                output.write(f"{game['title']} | {game['genre']} | {game['rating']}/5\n")
            if not games:
                output.write("Your library is empty.\n")
        temporary_path.replace(path)
    except OSError as error:
        result["error"] = str(error)
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError as error:
                result["error"] = str(error)


def main():
    try:
        games = request_json("/games")["games"]
    except RequestError as error:
        print(error)
        return 1
    result = {}
    worker = Thread(target=write_report, args=(games, REPORT_PATH, result))
    worker.start()
    worker.join()
    if "error" in result:
        print(f"Could not save the report: {result['error']}")
        return 1
    print(f"Saved {len(games)} game(s) to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
