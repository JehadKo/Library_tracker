"""Desktop game library. Run server.py first, then run this file."""

import tkinter as tk
from tkinter import messagebox, ttk

from client import RequestError, request_json
from game_fields import RATINGS, UNRATED_STATUSES


class GameLibrary:
    def __init__(self, root):
        self.root = root
        root.title("Game Library Tracker")
        root.geometry("770x490")
        root.minsize(560, 360)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        header = tk.Frame(root, bg="#183c38", padx=20, pady=14)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(header, text="My game library", font=("Segoe UI", 21, "bold"),
                 bg="#183c38", fg="white").pack(side="left")
        self.add_button = ttk.Button(header, text="Add game", command=self.open_editor)
        self.add_button.pack(side="right")

        body = ttk.Frame(root, padding=(20, 14))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)
        tools = ttk.Frame(body)
        tools.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(tools, text="Minimum rating").pack(side="left", padx=(0, 8))
        self.minimum = ttk.Combobox(tools, values=("All", *RATINGS),
                                    width=5, state="readonly")
        self.minimum.set("All")
        self.minimum.pack(side="left")
        self.minimum.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        self.refresh_button = ttk.Button(tools, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side="right")

        self.table = ttk.Treeview(body, columns=("title", "genre", "rating"),
                                  show="headings", selectmode="browse")
        for key, label, width in (("title", "Game title", 300), ("genre", "Genre", 145),
                                  ("rating", "Rating (1–5) or status", 150)):
            self.table.heading(key, text=label, anchor="w")
            self.table.column(key, width=width, minwidth=65, anchor="w")
        self.table.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(body, command=self.table.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scroll.set)
        self.table.bind("<<TreeviewSelect>>", lambda _event: self.update_buttons())

        actions = ttk.Frame(body)
        actions.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.edit_button = ttk.Button(actions, text="Edit selected", command=self.edit_selected)
        self.delete_button = ttk.Button(actions, text="Delete selected", command=self.delete_selected)
        self.edit_button.pack(side="left", padx=(0, 6))
        self.delete_button.pack(side="left")
        self.status = tk.StringVar()
        ttk.Label(body, textvariable=self.status, wraplength=520).grid(
            row=3, column=0, sticky="w", pady=(10, 0))
        self.update_buttons()
        self.refresh()

    def update_buttons(self):
        state = "normal" if self.table.selection() else "disabled"
        self.edit_button.configure(state=state)
        self.delete_button.configure(state=state)

    def refresh(self, message=""):
        minimum = self.minimum.get()
        path = "/games" if minimum == "All" else f"/games?min_rating={minimum}"
        try:
            games = request_json(path)["games"]
        except RequestError as error:
            self.status.set(f"{message} List refresh failed. {error}".strip())
            return
        self.table.delete(*self.table.get_children())
        for game in games:
            choice = game["rating"] if game["rating"] is not None else game["status"]
            self.table.insert("", "end", iid=str(game["id"]),
                              values=(game["title"], game["genre"], choice))
        self.update_buttons()
        if games:
            count = len(games)
            summary = f"{count} game{'s' if count != 1 else ''} shown."
        elif minimum == "All":
            summary = "Your library is empty. Choose Add game to start."
        else:
            summary = f"No games match a minimum rating of {minimum}."
        self.status.set(f"{message} {summary}".strip())

    def edit_selected(self):
        selected = self.table.selection()
        if selected:
            self.open_editor(selected[0])

    def open_editor(self, game_id=None):
        window = tk.Toplevel(self.root)
        window.title("Edit game" if game_id else "Add game")
        window.transient(self.root)
        window.resizable(False, False)
        form = ttk.Frame(window, padding=18)
        form.pack()
        title = ttk.Entry(form, width=36)
        genre = ttk.Entry(form, width=36)
        choice = ttk.Combobox(form, values=(*RATINGS, *UNRATED_STATUSES),
                              width=16, state="readonly")
        for row, (label, widget) in enumerate((("Game title", title), ("Genre", genre),
                                               ("Rating or status", choice))):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            widget.grid(row=row, column=1, sticky="w", pady=5)
        if game_id:
            old_title, old_genre, old_choice = self.table.item(game_id, "values")
            title.insert(0, old_title)
            genre.insert(0, old_genre)
            choice.set(old_choice)

        feedback = tk.StringVar()
        ttk.Label(form, textvariable=feedback, foreground="#93391e", wraplength=330).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=4)

        def save():
            selection = choice.get()
            fields = {"title": title.get(), "genre": genre.get()}
            if selection in UNRATED_STATUSES:
                fields["status"] = selection
            else:
                fields.update(status="Rated", rating=selection)
            path = f"/games/{game_id}/edit" if game_id else "/games/add"
            try:
                result = request_json(path, fields)
            except RequestError as error:
                feedback.set(str(error))
                return
            window.destroy()
            self.refresh(result["message"])

        buttons = ttk.Frame(form)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(6, 0))
        ttk.Button(buttons, text="Cancel", command=window.destroy).pack(side="left", padx=6)
        ttk.Button(buttons, text="Save", command=save).pack(side="left")
        window.bind("<Escape>", lambda _event: window.destroy())
        window.bind("<Return>", lambda _event: save())
        window.wait_visibility()
        window.grab_set()
        title.focus_set()

    def delete_selected(self):
        selected = self.table.selection()
        if not selected:
            return
        game_id = selected[0]
        title = self.table.item(game_id, "values")[0]
        if not messagebox.askyesno("Delete game", f'Delete "{title}" from your library?',
                                   parent=self.root, default="no"):
            return
        try:
            result = request_json(f"/games/{game_id}/delete", {})
        except RequestError as error:
            self.status.set(str(error))
            return
        self.refresh(result["message"])


if __name__ == "__main__":
    root = tk.Tk()
    GameLibrary(root)
    root.mainloop()
