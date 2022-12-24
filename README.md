# dreamhost-utilities

Series of small utilities for Dreamhost stuff

## Requirements

```sh
pip install -r requirements.txt
```

# Scripts

## dreamhost_backup.py

When you request a backup from your account Dreamhost will generate a series of .tar.gz files and make it available in the control panel.

As per their documentation here: https://help.dreamhost.com/hc/en-us/articles/215089918-Back-up-an-account-in-the-panel

This script will allow you to automatically download all the files made available.

To use it, you need to save the HTML file from the [backup page](https://panel.dreamhost.com/?tree=billing.backup) locally and then run:

```sh
./dreamhost_backup.py filename.html
```
