Obfuscidian Documentation
=========================

Obfuscidian makes an encrypted backup of your Obsidian vault in a separate
folder. Your notes and attachments stay readable in the original vault.
Use your private key to check the backup and restore it when you need it.

New here? Visit :doc:`getting-started/index` for a plain-language introduction,
or try the :doc:`getting-started/quickstart` with one fake note.
The :doc:`guides/index` have the detailed instructions and safety guidance.

.. important::

   Obfuscidian 1.0.1 is a stable maintenance release. See
   :doc:`getting-started/installation` for pipx and pip installation. Backup and restore writes
   work on Linux/macOS. Native Windows supports key creation, verification and
   previews; vault writes and recovery are refused. See
   :doc:`PLATFORMS` for tested capabilities and limitations.

Choose a task
-------------

* :doc:`BACKUP`: back up current files or keep older entries too.
* :doc:`VERIFY`: authenticate the complete mirror without application writes.
* :doc:`RESTORE`: restore a saved snapshot or review restored files using Git.
* :doc:`CONFIGURATION`: key selection, permissions, environment variables and custody.
* :doc:`getting-started/updating`: update the CLI for fixes and security patches.
* :doc:`SECURITY`: threat model, limits and private reporting.
* :doc:`TROUBLESHOOTING`: failures, recovery and retained plaintext cleanup.

.. toctree::
   :maxdepth: 2
   :hidden:

   getting-started/index
   guides/index
   reference/index
   maintainers/index
   CHANGELOG

Source and tracking
-------------------

The `source repository <https://github.com/jeffshurtliff/obfuscidian>`_ and
`issue tracker <https://github.com/jeffshurtliff/obfuscidian/issues>`_ contain
source code, release history and support requests. Remote hosting, repository privacy and publication are
user-managed. The Apache-2.0 license applies to the project.
