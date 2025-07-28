from PyQt5.QtCore import QThread, pyqtSignal, QUrl
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout, 
                             QWidget, QMessageBox, QDialog, QLineEdit,
                             QCheckBox)
from PyQt5.QtGui import QDesktopServices

from electrum_dash.i18n import _
from electrum_dash.plugin import hook
from electrum_dash.gui.qt.util import WindowModalDialog, OkButton, Buttons, CloseButton

from .dropbox_labels import DropboxLabelsPlugin


class AuthDialog(WindowModalDialog):
    """Dialog for Dropbox OAuth authentication"""
    
    def __init__(self, parent, plugin, wallet):
        WindowModalDialog.__init__(self, parent, _('Dropbox Authentication'))
        self.plugin = plugin
        self.wallet = wallet
        self.auth_code = None
        
        layout = QVBoxLayout(self)
        
        # Instructions
        msg = QLabel(_('To enable Dropbox sync, you need to authorize Electrum-Dash to access your Dropbox.\n\n'
                      '1. Click "Open Browser" to go to Dropbox\n'
                      '2. Log in and authorize the app\n'
                      '3. Copy the authorization code\n'
                      '4. Paste it below and click OK'))
        msg.setWordWrap(True)
        layout.addWidget(msg)
        
        # Button to open browser
        self.auth_url = plugin.authenticate_dropbox(wallet)
        browser_button = QPushButton(_('Open Browser'))
        browser_button.clicked.connect(self.open_browser)
        layout.addWidget(browser_button)
        
        # Input for auth code
        layout.addWidget(QLabel(_('Authorization Code:')))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText(_('Paste authorization code here'))
        layout.addWidget(self.code_input)
        
        # Buttons
        layout.addLayout(Buttons(CloseButton(self), OkButton(self)))
        
    def open_browser(self):
        """Open the authorization URL in default browser"""
        QDesktopServices.openUrl(QUrl(self.auth_url))
    
    def accept(self):
        """Handle OK button"""
        auth_code = self.code_input.text().strip()
        if not auth_code:
            QMessageBox.warning(self, _('Error'), _('Please enter the authorization code'))
            return
            
        # Try to complete authentication
        if self.plugin.complete_authentication(self.wallet, auth_code):
            self.auth_code = auth_code
            super().accept()
        else:
            QMessageBox.warning(self, _('Error'), _('Authentication failed. Please try again.'))


class LabelsThread(QThread):
    """Background thread for syncing labels"""
    progress = pyqtSignal(str)
    success = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, plugin, wallet, action='pull'):
        QThread.__init__(self)
        self.plugin = plugin
        self.wallet = wallet
        self.action = action
        
    def run(self):
        try:
            if self.action == 'pull':
                self.progress.emit(_('Downloading labels from Dropbox...'))
                # Run in event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.plugin.pull_labels(self.wallet))
            elif self.action == 'push':
                self.progress.emit(_('Uploading labels to Dropbox...'))
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.plugin.push_labels(self.wallet))
            
            self.success.emit()
        except Exception as e:
            self.error.emit(str(e))


class ImportThread(QThread):
    """Background thread for importing Trezor Suite labels"""
    progress = pyqtSignal(str)
    success = pyqtSignal(int)  # Number of labels imported
    error = pyqtSignal(str)
    
    def __init__(self, plugin, wallet):
        QThread.__init__(self)
        self.plugin = plugin
        self.wallet = wallet
        
    def run(self):
        try:
            self.progress.emit(_('Searching for Trezor Suite labels...'))
            
            # Run import in event loop
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            imported_labels = loop.run_until_complete(
                self.plugin.import_trezor_suite_labels(self.wallet)
            )
            
            self.success.emit(len(imported_labels))
        except Exception as e:
            self.error.emit(str(e))


class Plugin(DropboxLabelsPlugin):
    """Qt GUI integration for Dropbox Labels plugin"""
    
    def __init__(self, parent, config, name):
        DropboxLabelsPlugin.__init__(self, parent, config, name)
        self.windows = {}
        
    @hook
    def on_new_window(self, window):
        """Called when a new window is created"""
        self.windows[window] = None
        
    @hook
    def on_close_window(self, window):
        """Called when a window is closed"""
        self.windows.pop(window, None)
        
    def on_pulled(self, wallet):
        """Called after labels are pulled from Dropbox"""
        # Find the window for this wallet
        for window in self.windows:
            if window.wallet == wallet:
                window.update_labels()
                break
    
    def requires_settings(self):
        """This plugin has settings"""
        return True
    
    def settings_widget(self, window):
        """Create the settings widget"""
        # window here is the settings dialog, get the main window and wallet
        main_window = window.parent()
        wallet = main_window.wallet
        return EncodingDialog(window, self, wallet)
    
    @hook
    def init_menubar_tools(self, window, tools_menu):
        """Add menu item to Tools menu"""
        wallet = window.wallet
        if not wallet:
            return
            
        def show_settings():
            dialog = EncodingDialog(window, self, wallet)
            dialog.exec_()
            
        tools_menu.addAction(_("Dropbox Labels"), show_settings)


class EncodingDialog(WindowModalDialog):
    """Settings dialog for Dropbox Labels"""
    
    def __init__(self, parent, plugin, wallet):
        WindowModalDialog.__init__(self, parent, _('Dropbox Labels Settings'))
        self.plugin = plugin
        self.wallet = wallet
        self.thread = None
        
        layout = QVBoxLayout(self)
        
        # Authentication status
        self.auth_status = QLabel()
        self.update_auth_status()
        layout.addWidget(self.auth_status)
        
        # Auth button
        self.auth_button = QPushButton()
        self.update_auth_button()
        self.auth_button.clicked.connect(self.toggle_auth)
        layout.addWidget(self.auth_button)
        
        # Sync options
        layout.addWidget(QLabel(_('Sync Options:')))
        
        self.auto_sync = QCheckBox(_('Automatically sync labels'))
        self.auto_sync.setChecked(wallet.db.get('dropbox_auto_sync', True))
        layout.addWidget(self.auto_sync)
        
        # Manual sync buttons
        button_layout = QHBoxLayout()
        
        self.pull_button = QPushButton(_('Download from Dropbox'))
        self.pull_button.clicked.connect(self.pull_labels)
        self.pull_button.setEnabled(plugin.is_authenticated(wallet))
        button_layout.addWidget(self.pull_button)
        
        self.push_button = QPushButton(_('Upload to Dropbox'))
        self.push_button.clicked.connect(self.push_labels)
        self.push_button.setEnabled(plugin.is_authenticated(wallet))
        button_layout.addWidget(self.push_button)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel('')
        layout.addWidget(self.status_label)
        
        # Import from Trezor Suite
        if self.is_hardware_wallet():
            import_button = QPushButton(_('Import from Trezor Suite'))
            import_button.clicked.connect(self.import_trezor_labels)
            layout.addWidget(import_button)
        
        # Close button
        layout.addLayout(Buttons(CloseButton(self)))
        
    def is_hardware_wallet(self):
        """Check if this is a hardware wallet"""
        return hasattr(self.wallet, 'keystore') and hasattr(self.wallet.keystore, 'plugin')
    
    def update_auth_status(self):
        """Update authentication status label"""
        if self.plugin.is_authenticated(self.wallet):
            self.auth_status.setText(_('✓ Connected to Dropbox'))
            self.auth_status.setStyleSheet('QLabel { color: green; }')
        else:
            self.auth_status.setText(_('✗ Not connected to Dropbox'))
            self.auth_status.setStyleSheet('QLabel { color: red; }')
    
    def update_auth_button(self):
        """Update auth button text"""
        if self.plugin.is_authenticated(self.wallet):
            self.auth_button.setText(_('Disconnect from Dropbox'))
        else:
            self.auth_button.setText(_('Connect to Dropbox'))
    
    def toggle_auth(self):
        """Connect or disconnect from Dropbox"""
        if self.plugin.is_authenticated(self.wallet):
            # Disconnect
            reply = QMessageBox.question(self, _('Disconnect from Dropbox'),
                                       _('Are you sure you want to disconnect from Dropbox?'),
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.plugin.logout_dropbox(self.wallet)
                self.update_auth_status()
                self.update_auth_button()
                self.pull_button.setEnabled(False)
                self.push_button.setEnabled(False)
        else:
            # Connect
            dialog = AuthDialog(self, self.plugin, self.wallet)
            if dialog.exec_():
                self.update_auth_status()
                self.update_auth_button()
                self.pull_button.setEnabled(True)
                self.push_button.setEnabled(True)
                self.status_label.setText(_('Successfully connected to Dropbox!'))
    
    def pull_labels(self):
        """Download labels from Dropbox"""
        self.start_sync('pull')
    
    def push_labels(self):
        """Upload labels to Dropbox"""
        self.start_sync('push')
    
    def start_sync(self, action):
        """Start sync operation in background thread"""
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, _('Sync in Progress'),
                              _('Please wait for the current sync to complete.'))
            return
            
        self.thread = LabelsThread(self.plugin, self.wallet, action)
        self.thread.progress.connect(self.on_progress)
        self.thread.success.connect(self.on_success)
        self.thread.error.connect(self.on_error)
        
        # Disable buttons during sync
        self.pull_button.setEnabled(False)
        self.push_button.setEnabled(False)
        
        self.thread.start()
    
    def on_progress(self, message):
        """Update progress message"""
        self.status_label.setText(message)
    
    def on_success(self):
        """Handle successful sync"""
        self.status_label.setText(_('Sync completed successfully!'))
        self.pull_button.setEnabled(True)
        self.push_button.setEnabled(True)
    
    def on_error(self, error):
        """Handle sync error"""
        self.status_label.setText(_('Error: {}').format(error))
        self.pull_button.setEnabled(True)
        self.push_button.setEnabled(True)
        QMessageBox.warning(self, _('Sync Error'), str(error))
    
    def import_trezor_labels(self):
        """Import existing labels from Trezor Suite"""
        if not self.plugin.is_authenticated(self.wallet):
            QMessageBox.warning(self, _('Not Connected'),
                              _('Please connect to Dropbox first.'))
            return
            
        reply = QMessageBox.question(self, _('Import Trezor Suite Labels'),
                                   _('This will search for and import any existing Trezor Suite labels.\n\n'
                                     'Your Trezor will ask for confirmation to decrypt the labels.\n\n'
                                     'Continue?'),
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.start_import_thread()
    
    def start_import_thread(self):
        """Start import operation in background thread"""
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, _('Operation in Progress'),
                              _('Please wait for the current operation to complete.'))
            return
            
        self.thread = ImportThread(self.plugin, self.wallet)
        self.thread.progress.connect(self.on_progress)
        self.thread.success.connect(self.on_import_success)
        self.thread.error.connect(self.on_error)
        
        # Disable buttons during import
        self.pull_button.setEnabled(False)
        self.push_button.setEnabled(False)
        
        self.thread.start()
    
    def on_import_success(self, count):
        """Handle successful import"""
        self.status_label.setText(_('Import completed successfully!'))
        self.pull_button.setEnabled(True)
        self.push_button.setEnabled(True)
        QMessageBox.information(self, _('Import Complete'),
                              _('Successfully imported {} labels from Trezor Suite.').format(count))
    
    def accept(self):
        """Save settings when dialog is closed"""
        self.wallet.db.put('dropbox_auto_sync', self.auto_sync.isChecked())
        super().accept()