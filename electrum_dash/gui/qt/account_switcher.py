"""
Account Switcher Widget for Multi-Account Wallets
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QComboBox, QPushButton, QDialog, QLineEdit,
                             QMessageBox, QSpinBox, QColorDialog, QFrame)
from PyQt5.QtGui import QFont, QColor

from electrum_dash.i18n import _
from electrum_dash.gui.qt.util import WindowModalDialog, OkButton, CancelButton, Buttons
from electrum_dash.multi_account_wallet import MultiAccountWallet


class AccountSwitcher(QWidget):
    """Widget for switching between accounts in multi-account wallets"""
    
    account_changed = pyqtSignal(int)  # Emitted when account is changed
    
    def __init__(self, parent, wallet):
        super().__init__(parent)
        self.parent = parent
        self.wallet = wallet
        self.updating = False
        
        self.setup_ui()
        self.update_accounts()
        
    def setup_ui(self):
        """Set up the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Account label
        self.account_label = QLabel(_("Account:"))
        layout.addWidget(self.account_label)
        
        # Account dropdown
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(150)
        self.account_combo.currentIndexChanged.connect(self.on_account_changed)
        layout.addWidget(self.account_combo)
        
        # Add account button
        self.add_button = QPushButton(_("+"))
        self.add_button.setMaximumWidth(30)
        self.add_button.setToolTip(_("Add new account"))
        self.add_button.clicked.connect(self.add_account)
        layout.addWidget(self.add_button)
        
        # Account overview button
        self.overview_button = QPushButton(_("Overview"))
        self.overview_button.clicked.connect(self.show_overview)
        layout.addWidget(self.overview_button)
        
        # Balance display
        self.balance_label = QLabel()
        font = QFont()
        font.setBold(True)
        self.balance_label.setFont(font)
        layout.addWidget(self.balance_label)
        
    def is_multi_account_wallet(self) -> bool:
        """Check if current wallet supports multi-account"""
        return isinstance(self.wallet, MultiAccountWallet)
    
    def update_accounts(self):
        """Update the account dropdown with current accounts"""
        if not self.is_multi_account_wallet():
            self.setVisible(False)
            return
        
        self.setVisible(True)
        self.updating = True
        
        self.account_combo.clear()
        
        accounts = self.wallet.get_all_accounts()
        current_account = self.wallet.get_current_account()
        
        current_index = 0
        for i, (account_index, account_info) in enumerate(accounts.items()):
            # Display format: "Account Name (Balance)"
            balance = self.wallet.get_account_balance(account_index)
            balance_str = self.parent.format_amount(balance) if hasattr(self.parent, 'format_amount') else f"{balance}"
            
            display_text = f"{account_info.name} ({balance_str})"
            self.account_combo.addItem(display_text, account_index)
            
            if account_index == current_account:
                current_index = i
        
        self.account_combo.setCurrentIndex(current_index)
        self.update_balance_display()
        
        self.updating = False
    
    def update_balance_display(self):
        """Update the balance display"""
        if not self.is_multi_account_wallet():
            return
        
        total_balance = self.wallet.get_total_balance()
        current_balance = self.wallet.get_account_balance(self.wallet.get_current_account())
        
        if hasattr(self.parent, 'format_amount'):
            total_str = self.parent.format_amount(total_balance)
            current_str = self.parent.format_amount(current_balance)
        else:
            total_str = str(total_balance)
            current_str = str(current_balance)
        
        self.balance_label.setText(_("Current: {} | Total: {}").format(current_str, total_str))
    
    def on_account_changed(self, index):
        """Handle account selection change"""
        if self.updating or not self.is_multi_account_wallet():
            return
        
        account_index = self.account_combo.itemData(index)
        if account_index is not None:
            self.wallet.set_current_account(account_index)
            self.account_changed.emit(account_index)
            self.update_balance_display()
    
    def add_account(self):
        """Show dialog to add new account"""
        if not self.is_multi_account_wallet():
            return
        
        dialog = AddAccountDialog(self, self.wallet)
        if dialog.exec_():
            self.update_accounts()
    
    def show_overview(self):
        """Show account overview dialog"""
        if not self.is_multi_account_wallet():
            return
        
        dialog = AccountOverviewDialog(self, self.wallet)
        dialog.exec_()


class AddAccountDialog(WindowModalDialog):
    """Dialog for adding a new account"""
    
    def __init__(self, parent, wallet):
        super().__init__(parent, _("Add New Account"))
        self.wallet = wallet
        
        layout = QVBoxLayout(self)
        
        # Account name
        layout.addWidget(QLabel(_("Account Name:")))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(_("e.g., Savings, Business, etc."))
        layout.addWidget(self.name_edit)
        
        # Account index (optional)
        layout.addWidget(QLabel(_("Account Index (optional):")))
        self.index_spin = QSpinBox()
        self.index_spin.setMinimum(0)
        self.index_spin.setMaximum(999)
        self.index_spin.setValue(self.get_next_account_index())
        self.index_spin.setToolTip(_("Leave as suggested value unless you need a specific index"))
        layout.addWidget(self.index_spin)
        
        # Color (optional)
        layout.addWidget(QLabel(_("Account Color (optional):")))
        self.color_button = QPushButton(_("Choose Color"))
        self.color_button.clicked.connect(self.choose_color)
        self.selected_color = None
        layout.addWidget(self.color_button)
        
        # Buttons
        layout.addLayout(Buttons(CancelButton(self), OkButton(self)))
    
    def get_next_account_index(self):
        """Get the next available account index"""
        accounts = self.wallet.get_all_accounts()
        return max(accounts.keys(), default=-1) + 1
    
    def choose_color(self):
        """Choose color for the account"""
        color = QColorDialog.getColor(Qt.blue, self)
        if color.isValid():
            self.selected_color = color.name()
            self.color_button.setText(f"Color: {self.selected_color}")
            self.color_button.setStyleSheet(f"background-color: {self.selected_color}")
    
    def accept(self):
        """Create the new account"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, _("Error"), _("Please enter an account name"))
            return
        
        account_index = self.index_spin.value()
        
        try:
            # Create the account
            created_index = self.wallet.add_account(account_index, name)
            
            # Set color if chosen
            if self.selected_color:
                account = self.wallet.get_account_info(created_index)
                if account:
                    account.color = self.selected_color
                    self.wallet._save_accounts_to_db()
            
            QMessageBox.information(self, _("Success"), 
                                  _("Account '{}' created successfully!").format(name))
            super().accept()
            
        except Exception as e:
            QMessageBox.warning(self, _("Error"), _("Failed to create account: {}").format(str(e)))


class AccountOverviewDialog(WindowModalDialog):
    """Dialog showing overview of all accounts"""
    
    def __init__(self, parent, wallet):
        super().__init__(parent, _("Account Overview"))
        self.wallet = wallet
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(_("All Accounts"))
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        title.setFont(font)
        layout.addWidget(title)
        
        # Account list
        accounts = self.wallet.get_all_accounts()
        total_balance = 0
        
        for account_index, account_info in accounts.items():
            account_widget = self.create_account_widget(account_index, account_info)
            layout.addWidget(account_widget)
            total_balance += self.wallet.get_account_balance(account_index)
        
        # Total balance
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)
        
        total_label = QLabel(_("Total Balance: {}").format(
            parent.parent.format_amount(total_balance) if hasattr(parent.parent, 'format_amount') else str(total_balance)
        ))
        total_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        total_label.setFont(font)
        layout.addWidget(total_label)
        
        # Close button
        layout.addLayout(Buttons(OkButton(self)))
    
    def create_account_widget(self, account_index, account_info):
        """Create widget for single account display"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        
        layout = QHBoxLayout(widget)
        
        # Account name and index
        name_label = QLabel(f"{account_info.name} (#{account_index})")
        font = QFont()
        font.setBold(True)
        name_label.setFont(font)
        layout.addWidget(name_label)
        
        # Color indicator
        if account_info.color:
            color_label = QLabel("●")
            color_label.setStyleSheet(f"color: {account_info.color}; font-size: 16px;")
            layout.addWidget(color_label)
        
        layout.addStretch()
        
        # Balance
        balance = self.wallet.get_account_balance(account_index)
        balance_label = QLabel(
            self.parent().parent.format_amount(balance) if hasattr(self.parent().parent, 'format_amount') else str(balance)
        )
        layout.addWidget(balance_label)
        
        # Current account indicator
        if account_index == self.wallet.get_current_account():
            current_label = QLabel(_("(Current)"))
            current_label.setStyleSheet("color: green; font-weight: bold;")
            layout.addWidget(current_label)
        
        return widget