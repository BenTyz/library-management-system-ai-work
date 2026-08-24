# =============================================================================
# controller.py  —  The Controller layer
#
# OOP CONCEPTS USED HERE:
#   - Dependency injection  : Controller receives the model and view, not hard-coded
#   - Single responsibility : Controller only translates actions — no logic, no drawing
#   - Error handling        : catches Model exceptions, tells the View what to show
#
# THE CONTROLLER'S ONLY JOB:
#   1. Receive an action from the View (e.g. "user clicked Checkout")
#   2. Call the right Model method
#   3. Tell the View to refresh or show an error message
#
# It never draws anything itself, and never stores domain data itself.
# =============================================================================

from model import Library, Book, Member, create_sample_library


class LibraryController:
    """
    Mediates between the Model (Library) and the View (LibraryApp).

    The View calls methods on this controller.
    The Controller calls methods on the Model, then calls view.refresh().
    """

    def __init__(self):
        # Build the model with sample data so the app starts populated
        self.library: Library = create_sample_library()
        self.view = None   # set by the View after it constructs itself

    def set_view(self, view) -> None:
        """Called by the View so the Controller can trigger refreshes."""
        self.view = view

    # ------------------------------------------------------------------
    # Book actions
    # ------------------------------------------------------------------

    def add_book(self, book_id: str, title: str, author: str, genre: str) -> bool:
        """Returns True on success, False on failure (error shown to view)."""
        try:
            book = Book(book_id.strip(), title.strip(), author.strip(), genre.strip())
            self.library.add_book(book)
            self._refresh("Book added successfully.")
            return True
        except (ValueError, KeyError) as e:
            self._error(str(e))
            return False

    def remove_book(self, book_id: str) -> bool:
        try:
            book = self.library.remove_book(book_id)
            self._refresh(f"Removed '{book.title}'.")
            return True
        except (ValueError, KeyError) as e:
            self._error(str(e))
            return False

    def get_books(self, query: str = "") -> list:
        """Return all books, or filtered by query string."""
        if query.strip():
            return self.library.search_books(query.strip())
        return self.library.get_all_books()

    # ------------------------------------------------------------------
    # Member actions
    # ------------------------------------------------------------------

    def add_member(self, member_id: str, name: str, email: str) -> bool:
        try:
            member = Member(member_id.strip(), name.strip(), email.strip())
            self.library.add_member(member)
            self._refresh("Member added successfully.")
            return True
        except (ValueError, KeyError) as e:
            self._error(str(e))
            return False

    def remove_member(self, member_id: str) -> bool:
        try:
            member = self.library.remove_member(member_id)
            self._refresh(f"Removed member '{member.name}'.")
            return True
        except (ValueError, KeyError) as e:
            self._error(str(e))
            return False

    def get_members(self) -> list:
        return self.library.get_all_members()

    # ------------------------------------------------------------------
    # Checkout / Return actions
    # ------------------------------------------------------------------

    def checkout(self, book_id: str, member_id: str) -> bool:
        try:
            due = self.library.checkout(book_id, member_id)
            self._refresh(f"Checked out. Due date: {due}.")
            return True
        except (ValueError, KeyError) as e:
            self._error(str(e))
            return False

    def return_book(self, book_id: str) -> bool:
        try:
            self.library.return_book(book_id)
            self._refresh("Book returned successfully.")
            return True
        except (ValueError, KeyError) as e:
            self._error(str(e))
            return False

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        return self.library.stats()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _refresh(self, message: str = "") -> None:
        """Tell the View to redraw itself and optionally show a success message."""
        if self.view:
            self.view.refresh(message)

    def _error(self, message: str) -> None:
        """Tell the View to display an error."""
        if self.view:
            self.view.show_error(message)
