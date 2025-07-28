from electrum_dash.i18n import _

fullname = _('Dropbox Labels')
description = ' '.join([
    _("Sync your wallet labels with Dropbox, compatible with Trezor Suite."),
    _("Labels are encrypted using AES-256-GCM before being stored in your Dropbox."),
    _("Hardware wallets use SLIP-0015 key derivation for enhanced security.")
])
available_for = ['qt']  # Start with Qt support only