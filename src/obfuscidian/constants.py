# -*- coding: utf-8 -*-
"""
:Module:            obfuscidian.constants
:Synopsis:          Shared configuration and key constants
:Created By:        Jeff Shurtliff
:Last Modified:     Jeff Shurtliff (via GPT-6)
:Modified Date:     03 Oct 2026
"""

ENV_KEY_PATH = 'OBFUSCIDIAN_KEY_PATH'
ENV_KEY_ALIAS = 'OBFUSCIDIAN_KEY_ALIAS'
ENV_KEY_DIR = 'OBFUSCIDIAN_KEY_DIR'
ENV_ORIGIN = 'OBFUSCIDIAN_ORIGIN_VAULT'
ENV_MIRROR = 'OBFUSCIDIAN_MIRROR_VAULT'

KEY_PREFIX = 'obfuscidian-'
KEY_SUFFIX = '.key'
ALIAS_MAX_LENGTH = 64
ALIAS_PATTERN = r'[A-Za-z0-9-]{1,64}'
KEY_ENCODED_SIZE = 44
KEY_MODE = 0o600
TIMESTAMP_FORMAT = '%Y%m%d-%H%M%S'

CUSTODY_GUIDANCE = (
    'Keep the key outside both vaults and their cloud repositories. '
    'Keep a separate offline key backup; losing the key prevents decryption.'
)
WINDOWS_PERMISSION_WARNING = (
    'Windows key access depends on the directory ACL; POSIX mode 0600 does not restrict Windows ACLs. '
    'Use a private directory and review its access permissions.'
)

# Windows ACL creation: protected DACL, OWNER RIGHTS only, and FILE_PERSISTENT_ACLS.
WINDOWS_KEY_DACL = 'D:P(A;;GA;;;OW)'
WINDOWS_PERSISTENT_ACLS = 0x00000008
