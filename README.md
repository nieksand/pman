# Niek's Password Vault
A utility for managing an encrypted credential vault.

This was written as a hobby project and because I finally had time to explore
Python3.  It should be fine for low-value credentials, but if you are dealing
with serious threat scenarios, consider alternatives.  Also use 2 factor
authenticiation with a separate device whenever possible.

Vault contents are protected using Fernet.  This encrypts using AES128 in CBC
mode and authenticates using HMAC/SHA256.  Fernet's secret token comes from a
user password that is key-stretched using PBKDF2 over SHA256.  The iteration
count for PBKDF2 was dailed in to take about 3 seconds on my 2013 Macbook Air,
which comes out to 2M iterations, well over the NIST minimum guideline of 10K.
Each vault gets a unique 18 byte salt generated from urandom.

# Usage
First create an empty vault.  When prompted for a key you should use a very
strong password.  This is the one you'll have to memorize to protect your vault
contents.

    ./pman init ~/.pman_vault

Add the new vault file to your environment.  For example, a bash user might add
the following to their .profile:

    export PMAN_VAULT=/home/myuser/.pman_vault

To add or update a credential, use the 'set' command.  The inputs are not passed
via the command line to avoid exposing credentials in shell history files or via
the process list.

    ./pman set

You can fetch a credential using the 'get' command.

	./pman get mycred

You can also list all available credentials ('list') or search credentials using
a substring ('search').  To avoid exposing unneeded passwords, these two
commands will only show the credential name, username, description, and number
of days since the entry was last updated.  Once you identify the credential you
want, use 'get' to fetch the details.

	./pman list

You can 'remove' entries.  The entry being deleted will be emitted to stdout in
case you make a mistake.  (You can use that information with a 'set' to recreate
the entry).

	./pman remove mycred

If you ever need to change the secret key for your vault, you can use the
'rekey' command.  This changes both the encryption password and generates a new
random salt for the vault file.

	./pman rekey

# Dependencies
* Python 3.6+
* pyca/cryptography (https://cryptography.io/)

# Weaknesses
I made design choices that I consider acceptable risks.  Note that the vault is
decrypted every time it is accessed.  It does not "unlock" and stay open beyond
the duration of the Python script.

* Decrypts all credentials at once, putting them in process memory.
* Does not explicitly clear memory after use.

For the first item, if you have sufficient access to read arbitrary memory from
arbitrary processes on my computer, then my vault's secret key probably isn't
safe from you anyway.

For the second item, I'm dubious you can securely clear memory using pure
Python.

# Vault Backups
I back up my vault using a simple cron job copying the vault to a private S3
bucket.  I have S3 versioning turned on so accidental deletions don't ruin my
day.

# Author
This was written by Niek Sanders (niek.sanders@gmail.com).

# Unlicense
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
