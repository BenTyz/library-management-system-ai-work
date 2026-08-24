# =============================================================================
# view.py  —  The View layer (Tkinter GUI)
#
# OOP CONCEPTS USED HERE:
#   - Inheritance         : LibraryApp extends tk.Tk; each Panel extends tk.Frame
#   - Encapsulation       : each Panel manages its own widgets internally
#   - Composition         : LibraryApp "has" multiple Panel objects
#   - Callbacks / events  : buttons call self.controller.some_action(...)
#
# THE VIEW'S ONLY JOB:
#   - Display data given to it by the Controller
#   - Capture user input (button clicks, form fields)
#   - Call the Controller — never the Model directly
#
# If you see any business logic here (e.g. checking loan limits),
# that is a sign something is wrong — move it to model.py or controller.py.
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from controller import LibraryController


# ---------------------------------------------------------------------------
# Colour / style constants — change these to restyle the whole app
# ---------------------------------------------------------------------------
BG        = "#0f1117"   # dark navy background
SURFACE   = "#1a1d27"   # card surface
SURFACE2  = "#22263a"   # slightly lighter card
ACCENT    = "#6c63ff"   # purple accent
ACCENT2   = "#4ade80"   # green for "available"
DANGER    = "#f87171"   # red for errors / overdue
TEXT      = "#e2e8f0"   # primary text
MUTED     = "#8892a4"   # secondary text
BORDER    = "#2e3347"

FONT_H1   = ("Segoe UI", 20, "bold")
FONT_H2   = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_MONO = ("Consolas",  10)
FONT_SMALL= ("Segoe UI",   9)


# ---------------------------------------------------------------------------
# Helper: styled button factory
# ---------------------------------------------------------------------------
def make_button(parent, text, command, primary=False, danger=False):
    bg  = ACCENT  if primary else (DANGER if danger else SURFACE2)
    fg  = "#ffffff"
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=ACCENT2, activeforeground="#000",
        relief="flat", padx=12, pady=6,
        font=FONT_BODY, cursor="hand2", bd=0
    )


# ---------------------------------------------------------------------------
# StatsPanel  —  top bar showing live counts
# ---------------------------------------------------------------------------
class StatsPanel(tk.Frame):
    """
    Inherits from tk.Frame.
    Displays 5 stat cards updated whenever refresh() is called.
    """

    LABELS = ["Total Books", "Available", "On Loan", "Overdue", "Members"]

    def __init__(self, parent, controller: LibraryController):
        super().__init__(parent, bg=BG)    # call parent __init__ first
        self.controller = controller
        self._cards = {}
        self._build()

    def _build(self):
        for col, label in enumerate(self.LABELS):
            frame = tk.Frame(self, bg=SURFACE, padx=16, pady=12)
            frame.grid(row=0, column=col, padx=6, sticky="ew")
            self.columnconfigure(col, weight=1)

            tk.Label(frame, text=label, bg=SURFACE, fg=MUTED,
                     font=FONT_SMALL).pack(anchor="w")
            val = tk.Label(frame, text="0", bg=SURFACE, fg=TEXT,
                           font=("Segoe UI", 22, "bold"))
            val.pack(anchor="w")
            self._cards[label] = val

    def refresh(self):
        stats = self.controller.get_stats()
        mapping = {
            "Total Books":  stats["total_books"],
            "Available":    stats["available"],
            "On Loan":      stats["on_loan"],
            "Overdue":      stats["overdue"],
            "Members":      stats["total_members"],
        }
        for label, widget in self._cards.items():
            widget.config(text=str(mapping[label]))
            if label == "Overdue" and mapping[label] > 0:
                widget.config(fg=DANGER)
            elif label == "Available":
                widget.config(fg=ACCENT2)
            else:
                widget.config(fg=TEXT)


# ---------------------------------------------------------------------------
# BooksPanel
# ---------------------------------------------------------------------------
class BooksPanel(tk.Frame):
    """
    Shows the full book list with search + checkout/return controls.
    Inherits from tk.Frame — this is OOP inheritance in action.
    """

    COLUMNS = ("ID", "Title", "Author", "Genre", "Status", "Due Date")

    def __init__(self, parent, controller: LibraryController):
        super().__init__(parent, bg=BG, padx=16, pady=12)
        self.controller = controller
        self._build()

    def _build(self):
        # --- search bar ---
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(0, 10))

        tk.Label(top, text="Search:", bg=BG, fg=MUTED,
                 font=FONT_BODY).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh())
        search_entry = tk.Entry(top, textvariable=self._search_var,
                                bg=SURFACE2, fg=TEXT, insertbackground=TEXT,
                                relief="flat", font=FONT_BODY, width=30)
        search_entry.pack(side="left", padx=8, ipady=5)

        # --- action buttons ---
        btn_frame = tk.Frame(top, bg=BG)
        btn_frame.pack(side="right")
        make_button(btn_frame, "+ Add Book",   self._open_add_dialog,  primary=True ).pack(side="left", padx=4)
        make_button(btn_frame, "Checkout",     self._checkout          ).pack(side="left", padx=4)
        make_button(btn_frame, "Return",       self._return            ).pack(side="left", padx=4)
        make_button(btn_frame, "Remove",       self._remove,  danger=True).pack(side="left", padx=4)

        # --- treeview table ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Library.Treeview",
                         background=SURFACE, foreground=TEXT,
                         fieldbackground=SURFACE, rowheight=28,
                         font=FONT_BODY, borderwidth=0)
        style.configure("Library.Treeview.Heading",
                         background=SURFACE2, foreground=MUTED,
                         font=FONT_SMALL, relief="flat")
        style.map("Library.Treeview", background=[("selected", ACCENT)])

        frame = tk.Frame(self, bg=SURFACE, bd=0)
        frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(frame, columns=self.COLUMNS,
                                   show="headings", style="Library.Treeview")
        widths = [60, 220, 160, 110, 90, 100]
        for col, w in zip(self.COLUMNS, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")

        scroll = ttk.Scrollbar(frame, orient="vertical",
                               command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # --- public ---
    def refresh(self):
        query = self._search_var.get()
        books = self.controller.get_books(query)
        self._tree.delete(*self._tree.get_children())
        for b in books:
            status   = "Available" if b.is_available else ("Overdue" if b.is_overdue() else "On Loan")
            due      = str(b.due_date) if b.due_date else "—"
            tag      = "avail" if b.is_available else ("overdue" if b.is_overdue() else "loan")
            self._tree.insert("", "end",
                              values=(b.book_id, b.title, b.author, b.genre, status, due),
                              tags=(tag,))
        self._tree.tag_configure("avail",   foreground=ACCENT2)
        self._tree.tag_configure("loan",    foreground=TEXT)
        self._tree.tag_configure("overdue", foreground=DANGER)

    # --- private helpers ---
    def _selected_book_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a book first.")
            return None
        return self._tree.item(sel[0])["values"][0]

    def _open_add_dialog(self):
        AddBookDialog(self, self.controller)

    def _checkout(self):
        book_id = self._selected_book_id()
        if not book_id:
            return
        members = self.controller.get_members()
        if not members:
            messagebox.showwarning("No members", "Add a member first.")
            return
        choices = [f"{m.member_id} — {m.name}" for m in members]
        choice  = simpledialog.askstring(
            "Checkout", "Enter member ID:\n" + "\n".join(choices),
            parent=self
        )
        if choice:
            self.controller.checkout(book_id, choice.strip().split("—")[0].strip())

    def _return(self):
        book_id = self._selected_book_id()
        if book_id:
            self.controller.return_book(book_id)

    def _remove(self):
        book_id = self._selected_book_id()
        if book_id and messagebox.askyesno("Confirm", f"Remove book {book_id}?"):
            self.controller.remove_book(book_id)


# ---------------------------------------------------------------------------
# MembersPanel
# ---------------------------------------------------------------------------
class MembersPanel(tk.Frame):

    COLUMNS = ("ID", "Name", "Email", "Loans")

    def __init__(self, parent, controller: LibraryController):
        super().__init__(parent, bg=BG, padx=16, pady=12)
        self.controller = controller
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Library Members", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(side="left")
        btn_frame = tk.Frame(top, bg=BG)
        btn_frame.pack(side="right")
        make_button(btn_frame, "+ Add Member", self._open_add_dialog, primary=True).pack(side="left", padx=4)
        make_button(btn_frame, "Remove",       self._remove, danger=True).pack(side="left", padx=4)

        style = ttk.Style()
        style.configure("Members.Treeview",
                         background=SURFACE, foreground=TEXT,
                         fieldbackground=SURFACE, rowheight=28,
                         font=FONT_BODY, borderwidth=0)
        style.configure("Members.Treeview.Heading",
                         background=SURFACE2, foreground=MUTED,
                         font=FONT_SMALL, relief="flat")
        style.map("Members.Treeview", background=[("selected", ACCENT)])

        frame = tk.Frame(self, bg=SURFACE)
        frame.pack(fill="both", expand=True)
        self._tree = ttk.Treeview(frame, columns=self.COLUMNS,
                                   show="headings", style="Members.Treeview")
        widths = [80, 200, 260, 80]
        for col, w in zip(self.COLUMNS, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")

        scroll = ttk.Scrollbar(frame, orient="vertical",
                               command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def refresh(self):
        members = self.controller.get_members()
        self._tree.delete(*self._tree.get_children())
        for m in members:
            tag = "heavy" if m.loan_count() == m.MAX_LOANS else "normal"
            self._tree.insert("", "end",
                              values=(m.member_id, m.name, m.email, m.loan_count()),
                              tags=(tag,))
        self._tree.tag_configure("heavy",  foreground=DANGER)
        self._tree.tag_configure("normal", foreground=TEXT)

    def _selected_member_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a member first.")
            return None
        return self._tree.item(sel[0])["values"][0]

    def _open_add_dialog(self):
        AddMemberDialog(self, self.controller)

    def _remove(self):
        mid = self._selected_member_id()
        if mid and messagebox.askyesno("Confirm", f"Remove member {mid}?"):
            self.controller.remove_member(mid)


# ---------------------------------------------------------------------------
# Dialog helpers — small pop-up windows
# ---------------------------------------------------------------------------
class _BaseDialog(tk.Toplevel):
    """
    Abstract-ish base class for our add-book / add-member dialogs.
    OOP concept: shared behaviour in a base class, subclasses override _submit().
    """

    def __init__(self, parent, title: str, controller: LibraryController):
        super().__init__(parent)
        self.controller = controller
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()              # modal — blocks parent until closed
        self._fields: dict[str, tk.StringVar] = {}
        self._build()
        self.wait_window()

    def _add_field(self, frame, label: str, row: int):
        tk.Label(frame, text=label, bg=BG, fg=MUTED,
                 font=FONT_BODY).grid(row=row, column=0, sticky="w", pady=6)
        var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=var, bg=SURFACE2, fg=TEXT,
                         insertbackground=TEXT, relief="flat",
                         font=FONT_BODY, width=28)
        entry.grid(row=row, column=1, padx=12, sticky="ew")
        self._fields[label] = var

    def _build(self):
        raise NotImplementedError("Subclasses must implement _build()")

    def _submit(self):
        raise NotImplementedError("Subclasses must implement _submit()")

    def _make_footer(self, parent):
        footer = tk.Frame(parent, bg=BG)
        footer.pack(fill="x", pady=(16, 0))
        make_button(footer, "Cancel", self.destroy).pack(side="right", padx=4)
        make_button(footer, "Save",   self._submit, primary=True).pack(side="right")


class AddBookDialog(_BaseDialog):
    def __init__(self, parent, controller):
        super().__init__(parent, "Add New Book", controller)

    def _build(self):
        frame = tk.Frame(self, bg=BG, padx=20, pady=16)
        frame.pack()
        tk.Label(frame, text="Add New Book", bg=BG, fg=TEXT,
                 font=FONT_H2).grid(row=0, columnspan=2, sticky="w", pady=(0, 12))
        for i, label in enumerate(("Book ID", "Title", "Author", "Genre"), start=1):
            self._add_field(frame, label, i)
        self._make_footer(frame)

    def _submit(self):
        ok = self.controller.add_book(
            self._fields["Book ID"].get(),
            self._fields["Title"].get(),
            self._fields["Author"].get(),
            self._fields["Genre"].get(),
        )
        if ok:
            self.destroy()


class AddMemberDialog(_BaseDialog):
    def __init__(self, parent, controller):
        super().__init__(parent, "Add New Member", controller)

    def _build(self):
        frame = tk.Frame(self, bg=BG, padx=20, pady=16)
        frame.pack()
        tk.Label(frame, text="Add New Member", bg=BG, fg=TEXT,
                 font=FONT_H2).grid(row=0, columnspan=2, sticky="w", pady=(0, 12))
        for i, label in enumerate(("Member ID", "Name", "Email"), start=1):
            self._add_field(frame, label, i)
        self._make_footer(frame)

    def _submit(self):
        ok = self.controller.add_member(
            self._fields["Member ID"].get(),
            self._fields["Name"].get(),
            self._fields["Email"].get(),
        )
        if ok:
            self.destroy()


# ---------------------------------------------------------------------------
# LibraryApp — the main window  (top-level View)
# ---------------------------------------------------------------------------
class LibraryApp(tk.Tk):
    """
    Main application window.
    Extends tk.Tk (Tkinter's root window class) — pure inheritance.
    Owns the controller, stats panel, and tabbed content panels.
    """

    def __init__(self):
        super().__init__()
        self.title("CADT Library System")
        self.geometry("1000x680")
        self.configure(bg=BG)
        self.minsize(800, 580)

        # --- create controller, register self as view ---
        self.controller = LibraryController()
        self.controller.set_view(self)

        self._build()
        self.refresh()   # initial draw

    def _build(self):
        # Header
        header = tk.Frame(self, bg=SURFACE, padx=20, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="📚  CADT Library System",
                 bg=SURFACE, fg=TEXT, font=FONT_H1).pack(side="left")
        self._status_label = tk.Label(header, text="", bg=SURFACE,
                                       fg=ACCENT2, font=FONT_BODY)
        self._status_label.pack(side="right")

        # Stats bar
        self._stats = StatsPanel(self, self.controller)
        self._stats.pack(fill="x", padx=20, pady=(16, 0))

        # Notebook (tabs)
        style = ttk.Style()
        style.configure("App.TNotebook",        background=BG, borderwidth=0)
        style.configure("App.TNotebook.Tab",    background=SURFACE2, foreground=MUTED,
                         padding=(14, 8), font=FONT_BODY)
        style.map("App.TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#ffffff")])

        nb = ttk.Notebook(self, style="App.TNotebook")
        nb.pack(fill="both", expand=True, padx=20, pady=16)

        self._books_panel   = BooksPanel(nb, self.controller)
        self._members_panel = MembersPanel(nb, self.controller)
        nb.add(self._books_panel,   text="  Books  ")
        nb.add(self._members_panel, text="  Members  ")

    # ------------------------------------------------------------------
    # These two methods are called BY the controller to update the UI
    # ------------------------------------------------------------------
    def refresh(self, message: str = "") -> None:
        """Redraw all panels and optionally show a success message."""
        self._stats.refresh()
        self._books_panel.refresh()
        self._members_panel.refresh()
        if message:
            self._status_label.config(text=f"✓  {message}", fg=ACCENT2)
            self.after(3000, lambda: self._status_label.config(text=""))

    def show_error(self, message: str) -> None:
        """Display an error — called by the Controller, not by Model."""
        messagebox.showerror("Error", message)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()
