"""
Multi-Account Plugin Qt GUI Integration
Integrates the account switcher with the main window
"""

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from electrum_dash.i18n import _
from electrum_dash.plugin import hook
from electrum_dash.gui.qt import ElectrumGui
from electrum_dash.gui.qt.util import WindowModalDialog
from electrum_dash.multi_account_wallet import MultiAccountWallet
from electrum_dash.gui.qt.account_switcher import AccountSwitcher, AddAccountDialog, AccountOverviewDialog


class Plugin:
    """Multi-Account Plugin for Qt GUI"""
    
    def __init__(self, parent, config, name):
        self.parent = parent
        self.config = config
        self.name = name
        self.account_switchers = {}  # window -> switcher mapping
        
    @hook
    def load_wallet(self, wallet, window):
        """Called when a wallet is loaded"""
        if isinstance(wallet, MultiAccountWallet):
            self.add_account_switcher(window, wallet)
    
    @hook
    def close_wallet(self, wallet, window):
        """Called when a wallet is closed"""
        if window in self.account_switchers:
            self.remove_account_switcher(window)
    
    def add_account_switcher(self, window, wallet):
        """Add account switcher to the main window"""
        if not isinstance(wallet, MultiAccountWallet):
            return
            
        # Create account switcher widget
        account_switcher = AccountSwitcher(wallet, window)
        
        # Add to window's status bar
        if hasattr(window, 'statusBar'):
            # Create a container widget for better layout
            container = window.statusBar().addPermanentWidget(account_switcher)
            self.account_switchers[window] = account_switcher
            
            # Connect signals
            account_switcher.account_changed.connect(
                lambda idx: self.on_account_changed(window, wallet, idx)
            )
            account_switcher.account_added.connect(
                lambda idx, name: self.on_account_added(window, wallet, idx, name)
            )
        
        # Also add to main toolbar if available
        elif hasattr(window, 'toolbar'):
            window.toolbar.addWidget(account_switcher)
            self.account_switchers[window] = account_switcher
    
    def remove_account_switcher(self, window):
        """Remove account switcher from window"""
        if window in self.account_switchers:
            switcher = self.account_switchers.pop(window)
            if hasattr(window, 'statusBar'):
                window.statusBar().removeWidget(switcher)
            elif hasattr(window, 'toolbar'):
                window.toolbar.removeWidget(switcher)
            switcher.deleteLater()
    
    def on_account_changed(self, window, wallet, account_index):
        """Handle account change"""
        try:
            wallet.set_current_account(account_index)
            # Refresh the window's display
            window.need_update.set()
            window.trigger_update()
            window.history_list.update()
            window.address_list.update()
        except Exception as e:
            window.show_error(_("Failed to switch account: {}").format(str(e)))
    
    def on_account_added(self, window, wallet, account_index, name):
        """Handle new account creation"""
        try:
            # Account was already created by the switcher
            # Just refresh the display
            window.need_update.set()
            window.trigger_update()
            window.show_message(_("Account '{}' created successfully").format(name))
        except Exception as e:
            window.show_error(_("Failed to create account: {}").format(str(e)))
    
    @hook
    def create_status_bar(self, window, status_bar):
        """Hook to add elements to status bar when it's created"""
        wallet = window.wallet
        if isinstance(wallet, MultiAccountWallet):
            QTimer.singleShot(100, lambda: self.add_account_switcher(window, wallet))
    
    def show_account_overview(self, parent, wallet):
        """Show account overview dialog"""
        if not isinstance(wallet, MultiAccountWallet):
            return
            
        dialog = AccountOverviewDialog(parent, wallet)
        dialog.exec_()
    
    @hook
    def create_menu(self, window, menu):
        """Add menu items for multi-account features"""
        wallet = window.wallet
        if not isinstance(wallet, MultiAccountWallet):
            return
            
        # Add to Wallet menu
        if menu.title() == _("&Wallet"):
            menu.addSeparator()
            
            # Add Account Overview action
            overview_action = menu.addAction(_("Account Overview"))
            overview_action.triggered.connect(
                lambda: self.show_account_overview(window, wallet)
            )
            
            # Add New Account action  
            new_account_action = menu.addAction(_("New Account"))
            new_account_action.triggered.connect(
                lambda: self.show_add_account_dialog(window, wallet)
            )
    
    def show_add_account_dialog(self, parent, wallet):
        """Show add account dialog"""
        if not isinstance(wallet, MultiAccountWallet):
            return
            
        dialog = AddAccountDialog(parent, wallet)
        if dialog.exec_():
            account_name = dialog.get_account_name()
            try:
                account_index = wallet.add_account(name=account_name)
                
                # Update any account switchers
                for window, switcher in self.account_switchers.items():
                    if window.wallet == wallet:
                        switcher.refresh_accounts()
                
                parent.show_message(
                    _("Account '{}' created successfully").format(account_name)
                )
                
                # Switch to the new account
                wallet.set_current_account(account_index)
                parent.need_update.set()
                parent.trigger_update()
                
            except Exception as e:
                parent.show_error(_("Failed to create account: {}").format(str(e)))


# Integration helper functions
def is_multi_account_wallet(wallet):
    """Check if wallet supports multi-account features"""
    return isinstance(wallet, MultiAccountWallet)


def get_current_account_info(wallet):
    """Get current account information"""
    if not is_multi_account_wallet(wallet):
        return None
    
    current_account = wallet.get_current_account()
    return wallet.get_account_info(current_account)


def get_account_label(wallet, account_index):
    """Get display label for an account"""
    if not is_multi_account_wallet(wallet):
        return _("Main")
    
    account_info = wallet.get_account_info(account_index)
    if account_info:
        return account_info.name
    
    return _("Account {}").format(account_index)