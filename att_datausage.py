#! /usr/bin/python

# att_datausage.py
# created by Alexis Villalon alexisv@gmail.com
#
import getopt
import requests
import re
import string
import sys
import keyring
import hparse
ATTURL = 'http://www.att.com'
KEYRING_SERVICE = 'att'

def printhelp(this):
    print '{} -h'.format(this)
    print '{} [-d] -u <userid>'.format(this)
    print '{} [-d] --userid=<userid>'.format(this)

def printres(req, debug):
    if debug == 'Y':
        print 'Status Code: {}'.format(req.status_code)
        print 'URL now: {}'.format(req.url)
        print 'History: {}'.format(req.history)

def dprint(message, debug):
    if debug == 'Y':
        print message

def main():
    this = sys.argv[0]
    userid = ''
    debug = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dhu:", ["userid="])
    except getopt.GetoptError:
        printhelp(this)
        return(2)
    for opt, arg in opts:
        if opt == '-h':
            printhelp(this)
            return(3)
        elif opt == '-d':
            debug = 'Y'
        elif opt in ("-u", "--userid"):
            userid = arg
    if userid == '':
        printhelp(this)
        return(3)
    info = getdatausage(userid, debug)
    if not (info is None):
        return
    else:
        return(4)
    
def getdatausage(userid, debug):
    if userid in (None, ''):
        print "ERROR: userid is needed!"
        return
    password = keyring.get_password(KEYRING_SERVICE, userid)
    if password == None:
        print "ERROR: No password retrieved from keyring.  You need to set up your keyring first."
        return
    if debug == 'Y':
        print "Debug is set."
    dprint('Connecting to {}'.format(ATTURL), debug)
    r = requests.get(ATTURL)
    printres(r, debug)
    dprint('Looking for form with id ssoLoginForm', debug)
    hparser = hparse.getforms()
    hparser.feed(r.text)
    frm1attr, frm1inps = hparser.get_forms_data() 
    dprint('Getting method, action, and input fields from the form...', debug)
    form1_method = frm1attr['ssoLoginForm']['method']
    form1_action = frm1attr['ssoLoginForm']['action']
    form1_payload = {}
    for k in (frm1inps['ssoLoginForm'].viewkeys()):
        if k == 'wireless_num':
            form1_payload[k] = userid
        elif k == 'pass':
            form1_payload[k] = password
        else:
            form1_payload[k] = frm1inps['ssoLoginForm'][k]
    if string.lower(form1_method) != 'post':
        print("ERROR: FORM method is not post! exiting.")
        return
    dprint('Data payload: {}'.format(form1_payload), debug)
    dprint('Connecting to {}'.format(form1_action), debug)
    r2 = requests.post(form1_action, data=form1_payload)
    printres(r2, debug)
    dprint('Looking for form with id tGuardLoginForm', debug)
    #hparser2 = getforms()
    #hparser2.feed(r2.text)
    hparser.feed(r2.text)
    frm2attr, frm2inps = hparser.get_forms_data() 
    dprint('Getting method, action, and input fields from the form...', debug)
    form2_method = frm2attr['tGuardLoginForm']['method']
    form2_action = frm2attr['tGuardLoginForm']['action']
    form2_payload = {}
    for k in (frm2inps['tGuardLoginForm'].viewkeys()):
        form2_payload[k] = frm2inps['tGuardLoginForm'][k]
    if string.lower(form2_method) != 'post':
        dprint("FORM method is not post! exiting.", debug)
        return
    dprint('Data payload: {}'.format(form2_payload), debug)
    dprint('Connecting to {}'.format(form2_action), debug)
    # create session
    s = requests.session()
    r3 = s.post(form2_action, form2_payload)
    printres(r3, debug)
    hparser3 = hparse.gethrefbaseondata()
    hparser3.feed(r3.text)
    usagepage = hparser3.get_href()
    servername3_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r3.url)
    servername3 = servername3_match.group(1)
    fusagepage = servername3 + usagepage
    dprint('Connecting to {}'.format(fusagepage), debug)
    r4 = s.get(fusagepage)
    printres(r4, debug)
    hparser5 = hparse.getdatabaseondivid()
    hparser5.feed(r4.text)
    usageurl = hparser5.get_udata()
    servername4_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r4.url)
    servername4 = servername4_match.group(1)
    fusageurl = servername4 + usageurl
    dprint('Connecting to {}'.format(fusageurl), debug)
    r5 = s.get(fusageurl)
    printres(r5, debug)
    hparser6 = hparse.gettableinfo()
    hparser6.feed(r5.text)
    totalusage, timerange, daysleft, deviceusage = hparser6.get_table_data()
    print "Billing Period: {0}; {1}".format(timerange, daysleft)
    print
    print 'Detailed Data Usage Status: ', totalusage
    print
    print 'Detailed Data Usage per device:'
    for k in deviceusage:
        dphone_number = k
        dphone_owner = deviceusage[k]['name']
        dphone_data = deviceusage[k]['data']
        print '\t{0} : {1} : {2}'.format(dphone_owner, dphone_number, dphone_data)
        deviceusage[dphone_number] = [dphone_owner, dphone_data]
    # return 2 dictionaries.
    return { 'timerange': timerange, 'daysleft': daysleft, 'totalusage': totalusage }, deviceusage
    
# if being ran as a script, then execute main()
if __name__ == "__main__":
    status = main()
    sys.exit(status)

