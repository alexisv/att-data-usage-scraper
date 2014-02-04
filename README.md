att_datausage.py
created by Alexis Villalon alexisv@gmail.com

A python script that scrapes AT&T web to get Data Usage summary.

Tested to work 100% in wheezy raspbian.

Needed modules are the following.  Only first two need to be installed if you have not done so yet, because the rest are already included in basic installation.

    import requests
    import keyring
    import getopt
    import re
    import string
    import sys
    import HTMLParser

Constant variables are:

    ATTURL = 'http://www.att.com'
    KEYRING_SERVICE = 'att'

If you would use this, you need to have your keyring set up like the following from IDLE or Python CLI:

    >>> import keyring
    >>> keyring.set_password("att", "att_username", "att_password")

Run it like:

    ./att_datausage.py -h
    ./att_datausage.py [-d] -u <userid>
    ./att_datausage.py [-d] --userid=<userid>

Output is like:

    Billing Period: Jan 06, 2014 - Present; 4 days left
    
    Detailed Data Usage Status: 409 / 1024.0 MB used
    
    Detailed Data Usage per device:
        Al**** V******* : xxx-nnn-nnnn : 171 of 1024 MBs used
        E*** V******* : xxx-nnn-nnnn : 238 of 1024 MBs used

Also works as a module like the following, and returns 2 dictionaries.

    >>> import att_datausage
    >>> res = att_datausage.getdatausage('xxxnnnnnnn','')

Enjoy!
