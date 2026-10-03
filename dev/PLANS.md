# Obfuscidian Implementation Plan

> **Original design brief:** This document is preserved as the initial concept.
> Follow [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the authoritative
> implementation roadmap, approved decisions, safety requirements, and thread-sized
> tasks. Its updated decisions take precedence wherever this brief differs.

## 1. Purpose & Big Picture

The primary purpose of this project is to provide an easy-to-use CLI tool that empowers Obsidian 
users to reversibly obfuscate and encrypt their vault content so that they can confidently back up 
their data into a private cloud-hosted Git repository such as GitHub or GitLab without worrying about hosting their 
sensitive information in the cloud in case of a data breach impacting the cloud provider.

### Scope & Deliverables

The vault content would primarily be their Markdown notes, but would also include their folder structure 
and directory names, and potentially even their configuration files and attachments. The files would be encrypted 
as individual files rather than a file archive (e.g. `zip` or `tar.gz` file) to avoid exceeding the maximum file size 
permitted by GitHub and other hosts.

For example, if an Obsidian vault contains 3 files (e.g. `todo-list.md`, `journal.md`, and `projects.md`) then the 
resulting data would also be 3 files (e.g. `dG9kby1saXN0Lm1k.obf`, `am91cm5hbC5tZA.obf`, and `cHJvamVjdHMubWQ.obf`) 
rather than zipping the 3 files into a single archive.


### Packaging & Distribution

Once developed, tested, and stabilized, this project will be made open-source as a public GitHub repository 
and will be hosted on PyPI. It will also be documented using Sphinx, restructuredText, and MyST Markdown in 
a similar style to the documentation for the [`salespyforce`](https://github.com/jeffshurtliff/salespyforce) 
and [`pydplus`](https://github.com/jeffshurtliff/pydplus) projects and using the same Sphinx theme and structure.

---

## 2. Context & Structure

This tool will be developed in Python using the `click` library by 
[Pallets](https://click.palletsprojects.com/en/stable/quickstart/) using 
[entry points](https://click.palletsprojects.com/en/stable/entry-points/), along with the Fernet 
symmetric encryption recipe from the `cryptography` python package for the secure AES-128/256 
data encryption. Base64 will also be leveraged to assist in obfuscating the file and directory names.

The primary encryption/decryption processes should **not** be performed within the main Obsidian vault, 
but instead will use the main vault as the source and will point to a sibling/mirror vault that will act 
as the destination, with the latter being associated with the private cloud repository.

For example, if the main vault is in `/Users/johndoe/my-obsidian-vault/` then the repository for the 
obfuscated and encrypted vault data might be in `/Users/johndoe/my-obsidian-vault-encrypted` with the 
latter being associated with a private GitHub repository.

### Environment Variables

Environment variables can optionally be defined and used in place of command-line arguments to specify how 
the `obfuscidian` command should operate. The supported variables are explained below.

#### Private Key Variables

- The `OBFUSCIDIAN_KEY_PATH` variable can be used to define the full path to the private key that should be leveraged.
- The `OBFUSCIDIAN_KEY_ALIAS` variable can be used to define the alias of the private key.
- The `OBFUSCIDIAN_KEY_DIR` variable can be used to define the directory where the private key is stored.

The path variable is prioritized over the other two variables and will be used there are competing definitions. 
Similarly, the command-line arguments are prioritized over environment variables if both are provided.

If the `OBFUSCIDIAN_KEY_ALIAS` variable is defined but the `OBFUSCIDIAN_KEY_DIR` variable is not, then the command 
will assume that the key with the given alias is located in the user's home directory.

If a valid private key is not found with the information defined in these environment variables, then a warning will 
be displayed and the user will be prompted for an alias. However, if the `--non-interactive` flag is set, the command 
will fail with an error.

#### Obsidian Vault Locations

- The `OBFUSCIDIAN_ORIGIN_VAULT` variable can be used to define the full path to the source/origin Obsidian vault.
- The `OBFUSCIDIAN_MIRROR_VAULT` variable can be used to define the full path to the mirror vault where the obfuscated 
  and encrypted data resides.

If either of these environment variables are not defined, then the respective command-line arguments must be supplied.

---

## 3. Functionality

The CLI should have the ability to perform the following tasks:

- Generate and save a private key (likely using the `Fernet.generate_key()` method from the `cryptography`
  library) that will be used to encrypt and decrypt the vault data.
- Obfuscate and encrypt the vault data in the source path using a private key, populating a destination path 
  with the resulting data.
- Restore and unencrypt the data in the mirror path (which would this time be the source path) using a private 
  key, populating the restored data in a specified destination path. (This will have associated flags/options that 
  define how the data will be moved to the destination to avoid data loss when existing data is present. This will 
  be explained further in a subsequent section of this plan.)


### Generating the private key

A private key can be generated using the `obfuscidian keygen` command with optional specifications.

#### Requirements & Defaults

To generate a private key, the following details are required:

- An alias for the key that will be included in the filename
- A directory path where the key will be saved

**Alias**

An alias can be defined with the `--alias` option, only supporting alphanumeric characters and hyphens as 
valid characters. For example:

```commandline
obfuscidian keygen --alias="my-vault"
```

If an alias is not provided and the `--non-interactive` flag is not set, then the user should be 
prompted for an alias, with input validation in place. If they press enter and submit an empty value, then a 
timestamp should be used as the alias in the following format: `YYYYMMDD-HHmmss` (e.g. `20261001-132713`)

The filename of the generated key will be `obfuscidian-ALIAS.key` where `ALIAS` is the defined alias value.

**Output Directory**

An output directory can be specified with the `--dir` option. The option should handle values with and without a 
trailing slash, and should be based on the current working directory if a full path is not provided. 

For example, each of the commands below would be considered valid if the directories exist:

```commandline
obfuscidian keygen --dir="resources/my_keys/"
obfuscidian keygen --dir="/Users/johndoe/.ssh"
obfuscidian keygen --dir="../Documents"
```

The default destination directory will be the user's home directory if a path is not explicitly defined.

The destination directory must already exist. A missing directory will not be created and will result in an error.

### Obfuscation & Decryption

An Obsidian vault can be obfuscated and encrypted using the `obfuscidian shroud` command with one of two modes and 
some possible optional specifications, assuming the prerequisites are in place. These modes, which are `fresh` and 
`merge`, are explained in a section below. 

#### Prerequisites & Requirements

There are a few prerequisites needed in order to perform this operation:

- A private key must exist and its path or alias must be provided via argument or environment variable.
- The path to the directory for the origin/source vault must be provided via argument or environment variable.
- The path to the directory for the mirror vault where the obfuscated/encrypted data will be created must be 
  provided via argument or environment variable.

**Private Key**

If the private key is not found via the defined `OBFUSCIDIAN_KEY_PATH`, `OBFUSCIDIAN_KEY_ALIAS`, and/or 
`OBFUSCIDIAN_KEY_DIR` environment variables, then the key must be specified using an argument method below.

- The full or relative path to the key (including file name) can be provided via the `--key` option.
- The key alias can be provided via the `--alias` option, along with the `--keydir` option if the key does not 
  reside in the user's home directory.

For example, to use the key `~/obfuscidian-primary.key`, any of the argument methods below would be valid.
(NOTE: Other required arguments are not displayed to avoid overcomplicating the examples.)

```commandline
obfuscidian --key="/Users/johndoe/obfuscidian-primary.key"
obfuscidian --key="$HOME/obfuscidian-primary.key"
obfuscidian --key="~/obfuscidian-primary.key"
obfuscidian --key="obfuscidian-primary.key"
obfuscidian --alias="primary"
obfuscidian --alias="primary" --keydir="/Users/johndoe/"
obfuscidian --alias="primary" --keydir="$HOME"
```

In the examples above, the `--keydir` arguments would be valid but unnecessary. However, if the private key file was 
in a location other than the user's home directory, then the `--keydir` argument *would* be necessary.

**Origin/Source Vault Location**

If the full path to the origin/source Obsidian vault is not defined in the `OBFUSCIDIAN_ORIGIN_VAULT` environment 
variable, then the full or relative path to the vault must be provided via the `--origin` option. The `--origin` 
argument will always be prioritized over a defined environment variable and the environment variable will be ignored 
if both are defined.

The directory provided via either method **must exist** and the command will throw an error if it is not found. If both  
an environment variable and the command-line argument are defined and the latter directory is not found, then the  
command will throw an error and exit without falling back to the environment variable.

**Mirror Vault Location**

If the full path to the mirror Obsidian vault location is not defined in the `OBFUSCIDIAN_MIRROR_VAULT` environment 
variable, then the full or relative path to the vault must be provided via the `--mirror` option. The `--mirror` 
argument will always be prioritized over a defined environment variable and the environment variable will be ignored 
if both are defined.

Unlike with the origin vault location, the directory for the mirror vault location **does not** need to exist and the 
directory will be created if not found. However, any missing parent directories will **not** be created and the command 
will throw an error and exit if more than the final node is missing.

#### Fresh and Merge Modes

There are two different modes of performing the `shroud` (i.e. obfuscation and encryption) operation, which must be 
passed as positional arguments in the command.

**Fresh Mode**

Using the syntax `obfuscidian shroud fresh` will perform a **fresh copy**, where the mirror vault directory will start 
as empty, except for the root-level `.git` directory and `.gitignore` file. This means that if the mirror vault 
directory already has any content, the files and subdirectories will be deleted prior to the new data creation. This 
method ensures that stale, outdated files or folders -- such as those that may have been deleted or moved in the 
origin vault since the operation -- are **not** included in the backup.

**Merge Mode**

Using the syntax `obfuscidian shroud merge` will perform more of an incremental backup on top of the existing data 
found within the mirror vault directory, except for the root-level `.git` directory and `.gitignore` file which 
are left as-is. This means that **no files are deleted** or subdirectories in the mirror vault directory when the 
operation is initiated. During the operation, any files matching existing files will be overwritten, and all others 
will be created. While this is less destructive than the other method, it also means that previously deleted or moved 
files may return and may introduce duplicates.

#### File and Directory Modification

During the `shroud` operation with either method, the underlying script will traverse the entire vault in alphabetical 
ascending order and will perform the encryption and obfuscation operations from "inside out", working first in the 
deepest subdirectory and then working its way outward. It will then proceed to the next directory in order and descend 
to its lowest level and repeat the process.

Within each directory, it will perform the following tasks:

1. For each file, encode the file name (including the extension) to urlsafe base64, encrypt the string using the private 
   key into another base64 value, and strip trailing '=' padding bytes. Then append the file extension `.obf` to the 
   end of the string. (See `example-file-name-obfuscation-concept.py` and `example-encrypt-base64-to-base64.py` as a 
   concept reference)
2. Use the private key and the `cryptography.fernet` module to encrypt the contents of the file, saving the result 
   in the corresponding mirror vault location using the obfuscated and encrypted file name from Step 1. (See 
   `example-encrypt-decrypt-concept.py` as a concept reference)
3. After performing Steps 1-3 for all files in the directory, step up one level in the file structure and then use 
   the same obfuscation technique from Step 1 (excluding the file extension) to rename the directory.

### Restoring to the Origin Vault

An obfuscated and encrypted Obsidian vault in a mirror vault directory can be restored to the origin vault using 
the `obfuscidian unshroud` command with one of two modes and some possible optional specifications, assuming the 
prerequisites are in place. These modes, which are `fresh` and `merge`, are explained in a section below. 

Restoring from an obfuscated and encrypted mirror vault to the origin vault is very similar to the previous process, 
but essentially in reverse. The private key is used the identify the original file names and directory names, and to 
decrypt the file contents. However, the overall process varies depending on the specified mode.

#### Fresh and Merge Modes

There are two different modes of performing the `unshroud` (i.e. decryption and restore) operation, which must be 
passed as positional arguments in the command.

**Fresh Mode**

Using the syntax `obfuscidian unshroud fresh` will perform a **fresh restore**, where the origin vault directory will 
start as empty, except for the root-level `.git` directory and `.gitignore` file, and optionally excluding the 
`.obsidian/` configuration directory. This means that the files and subdirectories in the origin vault 
directory will be deleted prior to the new data creation. This method treats the operation as a full or fresh restore, 
return the vault exactly as it was at the time it was backed up.

**Merge Mode**

Using the syntax `obfuscidian unshroud merge` will perform more of an incremental restore on top of the existing data 
found within the origin vault directory, except for the root-level `.git` directory and `.gitignore` file which 
are left as-is. However, unlike the inverse process, this method requires `git` to be initialized for the origin 
vault as a local repository so that the restore can occur in a separate branch. The user will then be able to merge
the new branch into the `main` branch via the Git workflow to resolve any conflicts and allow for rollbacks as 
necessary or desired.

This mode assumes the following if no other options are specified in the command:

- The origin vault is already set up as a local Git repository, with the root Obsidian directory being the repository 
  root where the `.git/` directory is located.
- The primary repository uses `main` as its name, rather than `master` or something else.
- The new branch for the restore operation uses the following timestamp naming convention:
  `obfuscidian/restore-YYYYMMDD-HHmmss` (For example: `obfuscidian/restore-20261001-170732`)

The options below can be included in the command as desired to override these assumptions:

- The `--gitdir` argument allows the user to specify a different path to the repository (i.e. ".git" directory) which 
  will map to the `--git-dir=<path>` argument for the `git` commands that are performed. 
  (For example: `obfuscidian shroud merge --gitdir="path/to/repo"`)
- the `--worktree` argument similarly allows the user to specify a different path to the working tree, which will 
  map to the `--work-tree=<path>` argument for the `git` commands that are performed.
  (For example: `obfuscidian shroud merge --worktree="path/to/worktree"`)
- The `--branch` argument allows the user to specify the name of the branch suffix to be used in conjunction with 
  the `obfuscidian/` prefix when creating the restore branch. This option should only permit characters that are 
  valid branch names, such as only alphanumeric characters, hyphens, and forward slashes. (For example: 
  `obfuscidian shroud merge --branch="october-2026"` would use `obfuscidian/october-2026` as the branch name.)


### Exclusions & Constraints

The constraints and exclusions below apply to the `obfuscidian` command and its functionality.

- Any `.gitignore` file within the origin vault will **not** be obfuscated or encrypted, and will **not** be copied 
  into the mirror vault location, in order to avoid causing configuration conflicts. If the user wishes to include 
  the file, they they will need to copy it manually and it is recommended that they rename it to `.gitignore-origin` 
  or something else that will not conflict with or overwrite needed files.
- The `.git` directory will be excluded from the command operations to avoid overwriting crucial data, especially in 
  circumstances where Git is used locally in the origin vault while Git is also used separately in the mirror vault 
  for its associated cloud-hosted repository.
- In the current version, the command will **not** respect the `.gitignore` files in the mirror vault location 
- In the current version, there will be no validation or verification of the Git configuration for the mirror vault, 
  such as to confirm that the repository is private. Therefore, this validation is the user's responsibility.
- The `obfuscidian` command does **not** commit changes or perform other `git` commands in the mirror vault. Therefore, 
  it is the user's responsibility to commit, merge, and push changes as desired after running the command.


---

## 4. User Experience

The CLI should provide an intuitive, user-friendly experience so that the users are aware of what is taking place 
during operations through standard output and optional logging including the ability to write logs to a log file.

- The users should be able to use the `--help` argument to get help on the overall CLI as well as the sub-commands.
- The users should see the status and progress of operations that include file paths and other relevant information 
  when applicable.
- The CLI should fail gracefully and provide relevant, informative error messages and/or warnings when something fails,
  when a command is not being used properly, when required arguments or values are missing, and when an attempted 
  operation may result in data loss of any kind.

