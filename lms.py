import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import hashlib
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & FILE MANAGEMENT ---

DATA_FILE = "data.txt"
USERS_FILE = "users.txt"
DEFAULT_LOAN_DAYS = 14

def load_data():
    """Loads books and members from the data file."""
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read()
            if not content:
                return {'books': [], 'members': [], 'transactions': []}
            return json.loads(content)
    except FileNotFoundError:
        return {'books': [], 'members': [], 'transactions': []}
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Data file corrupted.")
        return {'books': [], 'members': [], 'transactions': []}

def save_data(data):
    """Saves books, members, and transactions to the data file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    """Hashes a password using SHA-256 for simple security."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- 2. CORE LIBRARY LOGIC (Simplified from your Java Classes) ---

class LibraryService:
    def __init__(self):
        self.data = load_data()

    def get_all_books(self):
        return self.data['books']

    def get_all_members(self):
        return self.data['members']

    def get_all_transactions(self):
        return self.data['transactions']

    def find_book(self, book_id):
        return next((b for b in self.data['books'] if b['id'] == book_id), None)

    def find_member(self, member_id):
        return next((m for m in self.data['members'] if m['id'] == member_id), None)

    def generate_id(self, prefix, items):
        """Generates a unique ID (e.g., B001, M002)"""
        if not items:
            return f"{prefix}001"
        last_id_num = int(items[-1]['id'][1:])
        new_id_num = last_id_num + 1
        return f"{prefix}{new_id_num:03d}"
    
    # --- Book Operations ---

    def add_book(self, title, author, isbn):
        book_id = self.generate_id('B', self.data['books'])
        new_book = {
            'id': book_id,
            'title': title,
            'author': author,
            'isbn': isbn,
            'status': 'Available'
        }
        self.data['books'].append(new_book)
        save_data(self.data)
        return new_book

    def delete_book(self, book_id):
        if any(t['book_id'] == book_id and t['status'] == 'Issued' for t in self.data['transactions']):
            return False, "Book is currently issued and cannot be deleted."
        
        self.data['books'] = [b for b in self.data['books'] if b['id'] != book_id]
        save_data(self.data)
        return True, "Book deleted successfully."

    # --- Member Operations ---

    def add_member(self, name, email, phone):
        member_id = self.generate_id('M', self.data['members'])
        new_member = {
            'id': member_id,
            'name': name,
            'email': email,
            'phone': phone,
            'join_date': datetime.now().strftime("%Y-%m-%d")
        }
        self.data['members'].append(new_member)
        save_data(self.data)
        return new_member

    def delete_member(self, member_id):
        if any(t['member_id'] == member_id and t['status'] == 'Issued' for t in self.data['transactions']):
            return False, "Member has outstanding books and cannot be deleted."

        self.data['members'] = [m for m in self.data['members'] if m['id'] != member_id]
        save_data(self.data)
        return True, "Member deleted successfully."

    # --- Transaction Operations ---

    def issue_book(self, book_id, member_id):
        book = self.find_book(book_id)
        if not book or book['status'] != 'Available':
            return False, "Book is not available for issue."

        member = self.find_member(member_id)
        if not member:
            return False, "Member not found."

        # Update book status
        book['status'] = 'Issued'

        # Create transaction
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=DEFAULT_LOAN_DAYS)
        
        transaction_id = self.generate_id('T', self.data['transactions'])
        new_transaction = {
            'id': transaction_id,
            'book_id': book_id,
            'member_id': member_id,
            'issue_date': issue_date.strftime("%Y-%m-%d"),
            'due_date': due_date.strftime("%Y-%m-%d"),
            'return_date': None,
            'status': 'Issued'
        }
        self.data['transactions'].append(new_transaction)
        save_data(self.data)
        return True, f"Book issued successfully. Due: {due_date.strftime('%Y-%m-%d')}"

    def return_book(self, book_id):
        book = self.find_book(book_id)
        if not book or book['status'] != 'Issued':
            return False, "Book is not currently issued."

        active_transaction = next((t for t in self.data['transactions'] if t['book_id'] == book_id and t['status'] == 'Issued'), None)
        if not active_transaction:
            return False, "Active transaction record not found."

        # Update book status
        book['status'] = 'Available'

        # Update transaction status
        active_transaction['return_date'] = datetime.now().strftime("%Y-%m-%d")
        active_transaction['status'] = 'Returned'

        save_data(self.data)
        return True, "Book returned successfully."


# --- 3. GUI (Tkinter) APPLICATION ---

class LibraryApp:
    def __init__(self, master):
        self.master = master
        master.title("Library Management System")
        master.geometry("800x600")
        
        self.service = LibraryService()
        self.current_user = None

        # Create main frames
        self.auth_frame = ttk.Frame(master, padding="10")
        self.dashboard_frame = ttk.Frame(master, padding="10")

        self.show_auth_screen()

    # --- 3.1 AUTHENTICATION SCREENS ---

    def show_auth_screen(self):
        self.dashboard_frame.pack_forget()
        self.auth_frame.pack(fill='both', expand=True)
        
        # Clear previous widgets
        for widget in self.auth_frame.winfo_children():
            widget.destroy()

        # Login/Signup Buttons
        self.login_btn = ttk.Button(self.auth_frame, text="Login", command=self.show_login_dialog)
        self.login_btn.pack(pady=10)
        
        self.signup_btn = ttk.Button(self.auth_frame, text="Sign Up", command=self.show_signup_dialog)
        self.signup_btn.pack(pady=10)

    def show_login_dialog(self):
        # Using Toplevel for modal dialogs
        dialog = tk.Toplevel(self.master)
        dialog.title("Login")
        dialog.transient(self.master)
        dialog.grab_set()

        ttk.Label(dialog, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.login_user = ttk.Entry(dialog)
        self.login_user.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.login_pass = ttk.Entry(dialog, show="*")
        self.login_pass.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(dialog, text="Login", command=lambda: self.handle_login(dialog)).grid(row=2, column=1, padx=5, pady=10)
    
    def handle_login(self, dialog):
        username = self.login_user.get()
        password = self.login_pass.get()
        hashed_password = hash_password(password)

        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            users = {}

        if username in users and users[username] == hashed_password:
            self.current_user = username
            dialog.destroy()
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password.")
            
    def show_signup_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Sign Up")
        dialog.transient(self.master)
        dialog.grab_set()

        ttk.Label(dialog, text="New Username:").grid(row=0, column=0, padx=5, pady=5)
        self.signup_user = ttk.Entry(dialog)
        self.signup_user.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="New Password:").grid(row=1, column=0, padx=5, pady=5)
        self.signup_pass = ttk.Entry(dialog, show="*")
        self.signup_pass.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(dialog, text="Sign Up", command=lambda: self.handle_signup(dialog)).grid(row=2, column=1, padx=5, pady=10)

    def handle_signup(self, dialog):
        username = self.signup_user.get()
        password = self.signup_pass.get()
        hashed_password = hash_password(password)

        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty.")
            return

        try:
            with open(USERS_FILE, 'r') as f:
                content = f.read()
                users = json.loads(content) if content else {}
        except (FileNotFoundError, json.JSONDecodeError):
            users = {}

        if username in users:
            messagebox.showerror("Error", "Username already exists.")
            return

        users[username] = hashed_password
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        
        messagebox.showinfo("Success", "Account created successfully! You can now log in.")
        dialog.destroy()


    # --- 3.2 DASHBOARD & NAVIGATION ---

    def show_dashboard(self):
        self.auth_frame.pack_forget()
        self.dashboard_frame.pack(fill='both', expand=True)

        # Main Title and Logout
        ttk.Label(self.dashboard_frame, text=f"Welcome, {self.current_user}", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Button(self.dashboard_frame, text="Logout", command=self.handle_logout).grid(row=0, column=2, sticky='e')

        # Notebook (Tabbed Interface)
        self.notebook = ttk.Notebook(self.dashboard_frame)
        self.notebook.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=10, pady=10)
        self.dashboard_frame.grid_columnconfigure(0, weight=1)
        self.dashboard_frame.grid_rowconfigure(1, weight=1)

        # Create tabs
        self.create_tab("Books", self.setup_books_tab)
        self.create_tab("Members", self.setup_members_tab)
        self.create_tab("Transactions", self.setup_transactions_tab)
        self.create_tab("Stats", self.setup_stats_tab)

    def handle_logout(self):
        self.current_user = None
        self.show_auth_screen()

    def create_tab(self, name, setup_function):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text=name)
        setup_function(tab)

    # --- 3.3 TAB SETUP FUNCTIONS ---

    def setup_books_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Controls Frame
        controls = ttk.Frame(tab)
        controls.grid(row=0, column=0, sticky='ew', pady=10)
        ttk.Button(controls, text="Add Book", command=self.open_add_book_dialog).pack(side='left', padx=5)
        ttk.Button(controls, text="Delete Selected", command=self.delete_selected_book).pack(side='left', padx=5)

        # Treeview for Books
        self.books_tree = ttk.Treeview(tab, columns=('ID', 'Title', 'Author', 'ISBN', 'Status'), show='headings')
        self.books_tree.grid(row=1, column=0, sticky='nsew')

        for col in ('ID', 'Title', 'Author', 'ISBN', 'Status'):
            self.books_tree.heading(col, text=col, anchor=tk.W)
            self.books_tree.column(col, width=100)
        
        self.books_tree.column('ID', width=50)
        self.books_tree.column('Title', width=200)

        self.update_books_list()

    def update_books_list(self):
        for i in self.books_tree.get_children():
            self.books_tree.delete(i)
        
        for book in self.service.get_all_books():
            self.books_tree.insert('', 'end', values=(
                book['id'], book['title'], book['author'], book['isbn'], book['status']
            ))

    def open_add_book_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Add New Book")
        dialog.transient(self.master)
        dialog.grab_set()

        labels = ["Title:", "Author:", "ISBN:"]
        entries = {}
        for i, label in enumerate(labels):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5)
            entries[label] = ttk.Entry(dialog, width=40)
            entries[label].grid(row=i, column=1, padx=5, pady=5)
        
        def save():
            title = entries["Title:"].get()
            author = entries["Author:"].get()
            isbn = entries["ISBN:"].get()

            if title and author and isbn:
                self.service.add_book(title, author, isbn)
                self.update_books_list()
                messagebox.showinfo("Success", "Book added successfully.")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "All fields are required.")
        
        ttk.Button(dialog, text="Save", command=save).grid(row=len(labels), column=1, padx=5, pady=10)

    def delete_selected_book(self):
        selected_item = self.books_tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a book to delete.")
            return

        book_id = self.books_tree.item(selected_item, 'values')[0]
        
        success, message = self.service.delete_book(book_id)

        if success:
            messagebox.showinfo("Success", message)
            self.update_books_list()
            self.update_stats_tab(self.notebook.nametowidget(self.notebook.tabs()[-1])) # Update stats
        else:
            messagebox.showerror("Error", message)

    def setup_members_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Controls Frame
        controls = ttk.Frame(tab)
        controls.grid(row=0, column=0, sticky='ew', pady=10)
        ttk.Button(controls, text="Add Member", command=self.open_add_member_dialog).pack(side='left', padx=5)
        ttk.Button(controls, text="Delete Selected", command=self.delete_selected_member).pack(side='left', padx=5)

        # Treeview for Members
        self.members_tree = ttk.Treeview(tab, columns=('ID', 'Name', 'Email', 'Phone', 'Join Date'), show='headings')
        self.members_tree.grid(row=1, column=0, sticky='nsew')

        for col in ('ID', 'Name', 'Email', 'Phone', 'Join Date'):
            self.members_tree.heading(col, text=col, anchor=tk.W)
            self.members_tree.column(col, width=100)

        self.members_tree.column('ID', width=50)
        self.members_tree.column('Name', width=150)
        self.members_tree.column('Email', width=180)

        self.update_members_list()

    def update_members_list(self):
        for i in self.members_tree.get_children():
            self.members_tree.delete(i)
        
        for member in self.service.get_all_members():
            self.members_tree.insert('', 'end', values=(
                member['id'], member['name'], member['email'], member['phone'], member['join_date']
            ))

    def open_add_member_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Add New Member")
        dialog.transient(self.master)
        dialog.grab_set()

        labels = ["Name:", "Email:", "Phone:"]
        entries = {}
        for i, label in enumerate(labels):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5)
            entries[label] = ttk.Entry(dialog, width=40)
            entries[label].grid(row=i, column=1, padx=5, pady=5)
        
        def save():
            name = entries["Name:"].get()
            email = entries["Email:"].get()
            phone = entries["Phone:"].get()

            if name and email and phone:
                self.service.add_member(name, email, phone)
                self.update_members_list()
                messagebox.showinfo("Success", "Member added successfully.")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "All fields are required.")
        
        ttk.Button(dialog, text="Save", command=save).grid(row=len(labels), column=1, padx=5, pady=10)

    def delete_selected_member(self):
        selected_item = self.members_tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a member to delete.")
            return

        member_id = self.members_tree.item(selected_item, 'values')[0]
        
        success, message = self.service.delete_member(member_id)

        if success:
            messagebox.showinfo("Success", message)
            self.update_members_list()
            self.update_stats_tab(self.notebook.nametowidget(self.notebook.tabs()[-1]))
        else:
            messagebox.showerror("Error", message)

    def setup_transactions_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Frame for controls and forms (Row 0)
        controls_frame = ttk.Frame(tab)
        controls_frame.grid(row=0, column=0, sticky='ew', pady=10)
        
        # --- Issue Book Section ---
        issue_frame = ttk.LabelFrame(controls_frame, text="Issue Book", padding="10")
        issue_frame.pack(side='left', padx=10, pady=5, fill='x', expand=True)

        ttk.Label(issue_frame, text="Book ID:").grid(row=0, column=0, padx=5, pady=2)
        self.issue_book_entry = ttk.Entry(issue_frame)
        self.issue_book_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(issue_frame, text="Member ID:").grid(row=1, column=0, padx=5, pady=2)
        self.issue_member_entry = ttk.Entry(issue_frame)
        self.issue_member_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Button(issue_frame, text="Issue", command=self.handle_issue).grid(row=2, column=1, padx=5, pady=5, sticky='e')
        
        # --- Return Book Section ---
        return_frame = ttk.LabelFrame(controls_frame, text="Return Book", padding="10")
        return_frame.pack(side='left', padx=10, pady=5, fill='x', expand=True)

        ttk.Label(return_frame, text="Book ID:").grid(row=0, column=0, padx=5, pady=2)
        self.return_book_entry = ttk.Entry(return_frame)
        self.return_book_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Button(return_frame, text="Return", command=self.handle_return).grid(row=1, column=1, padx=5, pady=5, sticky='e')
        
        # --- Transaction History Treeview (Row 1) ---
        self.transactions_tree = ttk.Treeview(tab, columns=('ID', 'Book ID', 'Member ID', 'Issue Date', 'Due Date', 'Return Date', 'Status'), show='headings')
        self.transactions_tree.grid(row=1, column=0, sticky='nsew')
        
        for col in ('ID', 'Book ID', 'Member ID', 'Issue Date', 'Due Date', 'Return Date', 'Status'):
            self.transactions_tree.heading(col, text=col, anchor=tk.W)
            self.transactions_tree.column(col, width=100)

        self.transactions_tree.column('Status', width=80)
        self.update_transactions_list()

    def update_transactions_list(self):
        for i in self.transactions_tree.get_children():
            self.transactions_tree.delete(i)
        
        transactions = sorted(self.service.get_all_transactions(), key=lambda t: t['issue_date'], reverse=True)
        
        for t in transactions:
            self.transactions_tree.insert('', 'end', values=(
                t['id'], t['book_id'], t['member_id'], t['issue_date'], t['due_date'], t['return_date'] if t['return_date'] else 'N/A', t['status']
            ))

    def handle_issue(self):
        book_id = self.issue_book_entry.get().upper()
        member_id = self.issue_member_entry.get().upper()

        success, message = self.service.issue_book(book_id, member_id)

        if success:
            messagebox.showinfo("Success", message)
            self.issue_book_entry.delete(0, tk.END)
            self.issue_member_entry.delete(0, tk.END)
            self.update_all_related_lists()
        else:
            messagebox.showerror("Error", message)

    def handle_return(self):
        book_id = self.return_book_entry.get().upper()

        success, message = self.service.return_book(book_id)

        if success:
            messagebox.showinfo("Success", message)
            self.return_book_entry.delete(0, tk.END)
            self.update_all_related_lists()
        else:
            messagebox.showerror("Error", message)

    def update_all_related_lists(self):
        """Updates all relevant listviews after a major operation"""
        self.update_books_list()
        self.update_transactions_list()
        self.update_stats_tab(self.notebook.nametowidget(self.notebook.tabs()[-1]))

    def setup_stats_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        
        ttk.Label(tab, text="Library Statistics", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=10, sticky='w')
        
        self.stats_labels = {}
        row_offset = 1
        
        stats = ["Total Books:", "Total Members:", "Books Issued:", "Books Available:", "Overdue Books:"]
        
        for i, stat in enumerate(stats):
            ttk.Label(tab, text=stat, font=("Arial", 12)).grid(row=row_offset + i, column=0, padx=10, pady=5, sticky='w')
            label = ttk.Label(tab, text="0", font=("Arial", 12, "bold"))
            label.grid(row=row_offset + i, column=1, padx=10, pady=5, sticky='w')
            self.stats_labels[stat] = label
            
        self.update_stats_tab(tab)

    def update_stats_tab(self, tab):
        books = self.service.get_all_books()
        members = self.service.get_all_members()
        transactions = self.service.get_all_transactions()
        
        total_books = len(books)
        total_members = len(members)
        books_issued = len([b for b in books if b['status'] == 'Issued'])
        books_available = len([b for b in books if b['status'] == 'Available'])
        
        # Calculate Overdue
        overdue_count = 0
        today = datetime.now().date()
        for t in transactions:
            if t['status'] == 'Issued':
                due_date = datetime.strptime(t['due_date'], "%Y-%m-%d").date()
                if due_date < today:
                    overdue_count += 1

        self.stats_labels["Total Books:"].config(text=str(total_books))
        self.stats_labels["Total Members:"].config(text=str(total_members))
        self.stats_labels["Books Issued:"].config(text=str(books_issued))
        self.stats_labels["Books Available:"].config(text=str(books_available))
        self.stats_labels["Overdue Books:"].config(text=str(overdue_count))


# --- 4. RUN APPLICATION ---

if __name__ == '__main__':
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
