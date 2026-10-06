Obfuscidian documentation
=========================

Back up an Obsidian vault as individually encrypted files and an encrypted path
manifest, then verify and restore it with the same private key. Original notes
and attachments remain byte-for-byte intact. The CLI is the supported interface;
internal Python helpers are not a public library API.

Start with :doc:`getting-started/installation`, then run the
:doc:`getting-started/tutorial` with fake data before using a real vault.

.. important::

   This is initial ``1.0.0.dev0`` development documentation. No PyPI release or
   hosted documentation is claimed. Linux/macOS write operations are implemented;
   native Windows vault mutation/recovery still fails closed. See
   :doc:`PLATFORMS` for tested capabilities and limitations.

Choose a task
-------------

* :doc:`BACKUP`: current-inventory fresh snapshots or additive retention.
* :doc:`VERIFY`: authenticate the complete mirror without application writes.
* :doc:`RESTORE`: fresh restore or an additive, uncommitted Git review worktree.
* :doc:`CONFIGURATION`: key selection, permissions, environment variables and custody.
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
development evidence. Remote hosting, repository privacy and publication are
user-managed. The Apache-2.0 license applies to the project.
