#! /usr/bin/python

# att_datausage.py
# created by Alexis Villalon alexisv@gmail.com
#
import requests
import keyring
import datetime
import getopt
import string
import sys
import hparse
ATTURL = 'http://www.att.com'
KEYRING_SERVICE = 'att'
FORM1 = 'ssoLoginForm'
FORM2 = 'tGuardLoginForm'

def printhelp(this):
    print '{} -h'.format(this)
    print '{} [-d] -u <userid>'.format(this)
    print '{} [-d] --userid=<userid>'.format(this)

def procres(req, debug):
    if debug == 'Y':
        dprint('Status Code: {}'.format(req.status_code), debug)
        dprint('URL now: {}'.format(req.url), debug)
        dprint('History: {}'.format(req.history), debug)
    if req.status_code != 200:
        print 'ERROR: Web server response status is ', req.status_code
        return(1)

def dprint(message, debug):
    if debug == 'Y':
        print 'debug:', str(datetime.datetime.now()), ':', message

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
    d1, d2 = getdatausage(userid, debug)
    if d1 in (199, 209, 219, 229, 239, 249, 259, 299, 349, 399):
        return(d1)
    elif not (d1 is None):
        print '----------------------------------------------------------------'
        print "Billing Period: {0}; {1}".format(d1['timerange'], d1['daysleft'])
        print 'Detailed Data Usage Status: {}'.format(d1['totalusage'])
        print 'Detailed Data Usage per device:'
        for dphone_number in d2:
            dphone_owner = d2[dphone_number]['name']
            dphone_data = d2[dphone_number]['data']
            print '\t{0} : {1} : {2}'.format(dphone_owner, dphone_number, dphone_data)
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
    resisnot200 = procres(r, debug)
    if resisnot200:
        return(199)
    dprint('Looking for form with id {}'.format(FORM1), debug)
    hparser = hparse.getforms()
    hparser.feed(r.text)
    frm1attr, frm1inps = hparser.get_forms_data()
    dprint('Getting method, action, and input fields from the form...', debug)
    form1_method = frm1attr[FORM1]['method']
    form1_action = frm1attr[FORM1]['action']
    form1_payload = {}
    for k in (frm1inps[FORM1].viewkeys()):
        if k == 'wireless_num':
            form1_payload[k] = userid
        elif k == 'pass':
            form1_payload[k] = password
        else:
            form1_payload[k] = frm1inps[FORM1][k]
    if string.lower(form1_method) != 'post' or form1_action in (None, '', ' '):
        print('ERROR: FORM details are not as expected! ', frm1attr[FORM1], frm1inps[FORM1])
        return(249)
    #dprint('Data payload: {}'.format(form1_payload), debug)
    dprint('Connecting to {}'.format(form1_action), debug)
    r2 = requests.post(form1_action, data=form1_payload)
    resisnot200 = procres(r2, debug)
    if resisnot200:
        return(209)
    dprint('Looking for form with id {}'.format(FORM2), debug)
    # re-use hparser
    hparser.feed(r2.text)
    frm2attr, frm2inps = hparser.get_forms_data() 
    dprint('Getting method, action, and input fields from the form...', debug)
    form2_method = frm2attr[FORM2]['method']
    form2_action = frm2attr[FORM2]['action']
    form2_payload = {}
    for k in (frm2inps[FORM2].viewkeys()):
        form2_payload[k] = frm2inps[FORM2][k]
    if string.lower(form2_method) != 'post' or form2_action in (None, '', ' '):
        print('ERROR: FORM details are not as expected! ', frm2attr[FORM2], frm2inps[FORM2])
        return(259)
    #dprint('Data payload: {}'.format(form2_payload), debug)
    dprint('Connecting to {}'.format(form2_action), debug)
    # create session
    s = requests.session()
    r3 = s.post(form2_action, form2_payload)
    resisnot200 = procres(r3, debug)
    if resisnot200:
        return(219)
    hparser3 = hparse.gethrefbaseondata()
    hparser3.feed(r3.text)
    usagelandingpage = hparser3.get_href()
    if usagelandingpage in (None, '', ' '):
        print('ERROR: usagelandingpage link not found!')
        return(299)
    url3toks = r3.url.split('/')
    servername3 = url3toks[0] + '//' + url3toks[2]
    fusagelandingpage = servername3 + usagelandingpage
    dprint('Connecting to {}'.format(fusagelandingpage), debug)
    r4 = s.get(fusagelandingpage)
    resisnot200 = procres(r4, debug)
    if resisnot200:
        return(229)
    hparser5 = hparse.getdatabaseondivid()
    hparser5.feed(r4.text)
    usagetable = hparser5.get_udata()
    if usagetable in (None, '', ' '):
        print('ERROR: usagetable link not found!')
        return(349)
    url4toks = r4.url.split('/')
    servername4 = url4toks[0] + '//' + url4toks[2]
    fusagetable = servername4 + usagetable
    dprint('Connecting to {}'.format(fusagetable), debug)
    r5 = s.get(fusagetable)
    resisnot200 = procres(r5, debug)
    if resisnot200:
        return(239)
    hparser6 = hparse.gettableinfo()
    hparser6.feed(r5.text)
    totalusage, timerange, daysleft, deviceusage = hparser6.get_table_data()
    if totalusage in (None, '', ' '):
        print('ERROR: Usage information not found!')
        return(399)
    dprint("Billing Period: {0}; {1}".format(timerange, daysleft), debug)
    dprint('Detailed Data Usage Status: {}'.format(totalusage), debug)
    dprint('Detailed Data Usage per device:', debug)
    for dphone_number in deviceusage:
        dphone_owner = deviceusage[dphone_number]['name']
        dphone_data = deviceusage[dphone_number]['data']
        dprint('\t{0} : {1} : {2}'.format(dphone_owner, dphone_number, dphone_data), debug)
        deviceusage[dphone_number] = {'name': dphone_owner, 'data': dphone_data}
    # return 2 dictionaries.
    return { 'timerange': timerange, 'daysleft': daysleft, 'totalusage': totalusage }, deviceusage
    
# if being ran as a script, then execute main()
if __name__ == "__main__":
    status = main()
    sys.exit(status)

