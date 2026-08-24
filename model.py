# =============================================================================
# model.py  —  The Model layer
#
# OOP CONCEPTS USED HERE:
#   - Classes & __init__           : defining objects and their state
#   - Encapsulation                : private attributes with leading underscore
#   - Properties (@property)       : controlled read/write access to private data
#   - __str__ / __repr__           : making objects print-friendly
#   - Composition                  : Library "has-a" list of Books and Members
#   - Raise exceptions             : signalling errors back to the Controller
#
# RULE: This file must have ZERO knowledge of any GUI framework.
#       It should work perfectly if you ran it from a plain terminal script.
# =============================================================================

from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Book
# ---------------------------------------------------------------------------
class Book:
    """Represents a single book in the library collection."""

    LOAN_DAYS = 14  # class-level constant shared by all Book instances

    def __init__(self, book_id: str, title: str, author: str, genre: str):
        # Private attributes — only changed through methods or properties
        self._book_id   = book_id
        self._title     = title
        self._author    = author
        self._genre     = genre
        self._available = True          # True = on shelf, False = checked out
        self._due_date: Optional[date] = None
        self._borrower_id: Optional[str] = None

    # --- properties: read-only fields ---
    @property
    def book_id(self) -> str:
        return self._book_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def genre(self) -> str:
        return self._genre

    # --- property: available (read-only from outside; changed by checkout/return) ---
    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def due_date(self) -> Optional[date]:
        return self._due_date

    @property
    def borrower_id(self) -> Optional[str]:
        return self._borrower_id

    # --- methods that change state ---
    def checkout(self, member_id: str) -> date:
        """Mark this book as checked out. Returns the due date."""
        if not self._available:
            raise ValueError(f"'{self._title}' is already checked out.")
        self._available    = False
        self._borrower_id  = member_id
        self._due_date     = date.today() + timedelta(days=self.LOAN_DAYS)
        return self._due_date

    def return_book(self) -> None:
        """Mark this book as returned."""
        if self._available:
            raise ValueError(f"'{self._title}' is not currently checked out.")
        self._available   = True
        self._borrower_id = None
        self._due_date    = None

    def is_overdue(self) -> bool:
        """True if the book is checked out AND past its due date."""
        if self._available or self._due_date is None:
            return False
        return date.today() > self._due_date

    # --- dunder methods for nice printing ---
    def __str__(self) -> str:
        status = "Available" if self._available else f"Due {self._due_date}"
        return f"[{self._book_id}] '{self._title}' by {self._author} — {status}"

    def __repr__(self) -> str:
        return (f"Book(id={self._book_id!r}, title={self._title!r}, "
                f"author={self._author!r}, available={self._available})")


# ---------------------------------------------------------------------------
# Member
# ---------------------------------------------------------------------------
class Member:
    """Represents a library member."""

    MAX_LOANS = 3  # a member can borrow at most 3 books at once

    def __init__(self, member_id: str, name: str, email: str):
        self._member_id   = member_id
        self._name        = name
        self._email       = email
        self._loaned_ids: list[str] = []   # book_ids currently held

    @property
    def member_id(self) -> str:
        return self._member_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def loaned_ids(self) -> list[str]:
        return list(self._loaned_ids)   # return a copy — caller cannot mutate the real list

    def borrow(self, book_id: str) -> None:
        """Record that this member borrowed a book."""
        if len(self._loaned_ids) >= self.MAX_LOANS:
            raise ValueError(
                f"{self._name} already has {self.MAX_LOANS} books on loan."
            )
        if book_id in self._loaned_ids:
            raise ValueError(f"Member already holds book {book_id}.")
        self._loaned_ids.append(book_id)

    def return_book(self, book_id: str) -> None:
        """Record that this member returned a book."""
        if book_id not in self._loaned_ids:
            raise ValueError(f"Member does not hold book {book_id}.")
        self._loaned_ids.remove(book_id)

    def loan_count(self) -> int:
        return len(self._loaned_ids)

    def __str__(self) -> str:
        return f"[{self._member_id}] {self._name} ({self._email}) — {self.loan_count()} loan(s)"

    def __repr__(self) -> str:
        return f"Member(id={self._member_id!r}, name={self._name!r})"


# ---------------------------------------------------------------------------
# Library   — Composition: Library "has" Books and Members
# ---------------------------------------------------------------------------
class Library:
    """
    The central model. Owns collections of Books and Members.
    All business logic lives here — checkout rules, search, stats.
    """

    def __init__(self, name: str):
        self._name    = name
        self._books:   dict[str, Book]   = {}   # book_id -> Book
        self._members: dict[str, Member] = {}   # member_id -> Member

    @property
    def name(self) -> str:
        return self._name

    # ---- book management ----

    def add_book(self, book: Book) -> None:
        if book.book_id in self._books:
            raise ValueError(f"Book ID '{book.book_id}' already exists.")
        self._books[book.book_id] = book

    def remove_book(self, book_id: str) -> Book:
        book = self._get_book(book_id)
        if not book.is_available:
            raise ValueError("Cannot remove a book that is currently on loan.")
        return self._books.pop(book_id)

    def get_all_books(self) -> list[Book]:
        return list(self._books.values())

    def search_books(self, query: str) -> list[Book]:
        """Case-insensitive search across title, author, and genre."""
        q = query.lower()
        return [
            b for b in self._books.values()
            if q in b.title.lower()
            or q in b.author.lower()
            or q in b.genre.lower()
        ]

    # ---- member management ----

    def add_member(self, member: Member) -> None:
        if member.member_id in self._members:
            raise ValueError(f"Member ID '{member.member_id}' already exists.")
        self._members[member.member_id] = member

    def remove_member(self, member_id: str) -> Member:
        member = self._get_member(member_id)
        if member.loan_count() > 0:
            raise ValueError("Cannot remove a member who still has books on loan.")
        return self._members.pop(member_id)

    def get_all_members(self) -> list[Member]:
        return list(self._members.values())

    # ---- checkout / return ----

    def checkout(self, book_id: str, member_id: str) -> date:
        """
        Check out a book to a member.
        Both Book and Member keep their own state updated.
        Returns the due date.
        """
        book   = self._get_book(book_id)
        member = self._get_member(member_id)
        due    = book.checkout(member_id)    # Book raises if unavailable
        member.borrow(book_id)               # Member raises if at loan limit
        return due

    def return_book(self, book_id: str) -> None:
        """Return a book — updates both the Book and its Member."""
        book = self._get_book(book_id)
        if book.is_available:
            raise ValueError(f"Book '{book_id}' is not currently on loan.")
        member = self._get_member(book.borrower_id)
        book.return_book()
        member.return_book(book_id)

    # ---- statistics ----

    def stats(self) -> dict:
        books   = self.get_all_books()
        members = self.get_all_members()
        return {
            "total_books":      len(books),
            "available":        sum(1 for b in books if b.is_available),
            "on_loan":          sum(1 for b in books if not b.is_available),
            "overdue":          sum(1 for b in books if b.is_overdue()),
            "total_members":    len(members),
        }

    # ---- private helpers ----

    def _get_book(self, book_id: str) -> Book:
        if book_id not in self._books:
            raise KeyError(f"No book with ID '{book_id}'.")
        return self._books[book_id]

    def _get_member(self, member_id: str) -> Member:
        if member_id not in self._members:
            raise KeyError(f"No member with ID '{member_id}'.")
        return self._members[member_id]

    def __str__(self) -> str:
        s = self.stats()
        return (f"Library '{self._name}': "
                f"{s['total_books']} books, {s['total_members']} members")


# ---------------------------------------------------------------------------
# Seed data helper  (makes manual testing easy)
# ---------------------------------------------------------------------------
def create_sample_library() -> Library:
    lib = Library("CADT Library")

    books = [
        Book("B001", "Clean Code",               "Robert C. Martin",  "Programming"),
        Book("B002", "The Pragmatic Programmer",  "David Thomas",      "Programming"),
        Book("B003", "Design Patterns",           "Gang of Four",      "Programming"),
        Book("B004", "Dune",                      "Frank Herbert",     "Sci-Fi"),
        Book("B005", "Atomic Habits",             "James Clear",       "Self-Help"),
        Book("B006", "The Algorithm Design Manual","Steven Skiena",    "Programming"),
        Book("B007", "Deep Work",                 "Cal Newport",       "Self-Help"),
        Book("B008", "Neuromancer",               "William Gibson",    "Sci-Fi"),
    ]
    members = [
        Member("M001", "Rothio",   "rothio@cadt.edu.kh"),
        Member("M002", "Dara",     "dara@cadt.edu.kh"),
        Member("M003", "Sokha",    "sokha@cadt.edu.kh"),
    ]

    for b in books:
        lib.add_book(b)
    for m in members:
        lib.add_member(m)

    return lib
