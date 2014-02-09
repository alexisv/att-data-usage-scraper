att_datausage.py
created by Alexis Villalon alexisv@gmail.com

A python script that scrapes AT&T web to get Data Usage information.

Tested to work 100% in wheezy raspbian.

Uses the requests module to connect to the web.

Needed modules are the following.  Only first two need to be installed if you have not done so yet.  The next four modules are already included in basic python installation.  The customized hparse module (hparse.py) contains the classes that are needed to parse the particular AT&T web pages, and this file is included in this repository as well.

    import requests
    import keyring
    
    import datetime
    import getopt
    import string
    import sys
    
    import hparse

Constant variables in this script are:

    ATTURL = 'http://www.att.com'
    KEYRING_SERVICE = 'att'
    FORM1 = 'ssoLoginForm'
    FORM2 = 'tGuardLoginForm'

Constant variables in the hparse.py module are:

    TIMERANGE_DIV_ID = 'timeRange'
    BILLING_PERIOD_P_DATA = 'Billing Period:'
    TOTAL_DATA_USAGE_P_ATTRS = 'left PadTop10 botMar0 center'

If you would use this, you need to have your keyring set up.  You could set it up like the following from IDLE or Python CLI:

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
    >>> d1, d2 = att_datausage.getdatausage('xxxnnnnnnn','')
    >>> d1
    {'timerange': u'Jan 06, 2014 - Present', 'totalusage': u'409 / 1024.0 MB used ', 'daysleft': u'4 days left'}
    >>> d2
    {u'xxx-nnn-nnnn': {'data': u'171 of 1024 MBs used', 'name': u'Al**** V*******'}, u'xxx-nnn-nnnn': {'data': u'238 of 1024 MBs used', 'name': u'E*** V*******'}}

Enjoy!
