# Pinterest Email Checker

## Description

Allows to check existence of accounts for specified emails and get basic information: id, email, fullname, image.

## Cookies

You must get cookies for searching first. The easiest way to register a new Pinterest account with a 10 minutes mail.

Follow next steps to export cookies to file:
1. Login into Pinterest account through your browser.
1. Install any extension to download all the cookies in Netscape format aka cookies.txt: ([Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid), [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)).
1. Save file to the directory of tool with name `cookies.txt` and run script without `--cookies-jar-file`.
1. Or run script with specified path to the cookies file: `./run.py --cookie-jar-file /a/b/c/1.txt email@domain.com`

## Example

```bash
$ ./run.py durov2005@gmail.com

Target: durov2005@gmail.com
Results found: 1
1) Username: durov
Fullname: Pavel Durov
Is Default Image: False
Image: https://i.pinimg.com/140x140_RS/4c/6b/3b/4c6b3bf163ae1221c51189211c848941.jpg

------------------------------
Total found: 1
```
