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
import HTMLParser
ATTURL = 'http://www.att.com'
KEYRING_SERVICE = 'att'


class MLStripper(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ' '.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def cleanv(dirtyval):
    cleanval = strip_tags(dirtyval)
    cleanval = ' '.join(cleanval.split())
    return cleanval

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
    fmatch = re.search('<form id="ssoLoginForm".+?</form>', r.text, re.DOTALL)
    if fmatch:
        dprint('form id ssoLoginForm found', debug)
        form1 = fmatch.group()
    else:
        print('ERROR: form not found! exiting')
        return
    dprint('Getting method, action, and input fields from the form...', debug)
    form1_action_match = re.search('<form.+?method="(.+?)".+?action="(.+?)"', form1)
    if form1_action_match:
        dprint('action and method found.', debug)
        form1_method = form1_action_match.group(1)
        form1_action = form1_action_match.group(2)
        dprint('Method: {}'.format(form1_method), debug)
        dprint('Action: {}'.format(form1_action), debug)
    else:
        print('ERROR: action and method not found in form1!')
        return
    form1_payload = {}
    for form1_input in re.finditer('<input.* name="(.+?)".*?>', form1):
        form1_input_name = form1_input.group(1)
        if form1_input_name == 'wireless_num':
            form1_payload[form1_input_name] = userid
        elif form1_input_name == 'pass':
            form1_payload[form1_input_name] = password
        else:
            vmatch = re.search('value="(.+?)"',form1_input.group(0))
            if vmatch:
                form1_payload[form1_input_name] = vmatch.group(1)
    if string.lower(form1_method) != 'post':
        print("ERROR: FORM method is not post! exiting.")
        return
    dprint('Data payload: {}'.format(form1_payload), debug)
    dprint('Connecting to {}'.format(form1_action), debug)
    r2 = requests.post(form1_action, data=form1_payload)
    printres(r2, debug)
    dprint('Looking for form with id tGuardLoginForm', debug)
    f2match = re.search('<form.+?id="tGuardLoginForm".+?</form>', r2.text, re.DOTALL)
    if f2match:
        dprint('form id tGuardLoginForm found', debug)
        form2 = f2match.group()
    else:
        print('ERROR: form not found! exiting')
        return
    # assumption in this re: form parameters has action came first before method.
    dprint('Getting method, action, and input fields from the form...', debug)
    form2_action_match = re.search('<form.+?action="(.+?)".+?method="(.+?)"', form2)
    if form2_action_match:
        dprint('action and method found.', debug)
        form2_action = form2_action_match.group(1)
        form2_method = form2_action_match.group(2)
        dprint('Method: {}'.format(form2_method), debug)
        dprint('Action: {}'.format(form2_action), debug)
    else:
        print('ERROR: action and method not found in form2!')
        return
    form2_payload = {}
    for form2_input in re.finditer('<input.* name="(.+?)".*?>', form2):
        form2_input_name = form2_input.group(1)
        v2match = re.search('value="(.+?)"',form2_input.group(0))
        if v2match:
           form2_payload[form2_input_name] = v2match.group(1)
    if string.lower(form2_method) != 'post':
        dprint("FORM method is not post! exiting.", debug)
        return
    dprint('Data payload: {}'.format(form2_payload), debug)
    dprint('Connecting to {}'.format(form2_action), debug)
    # create session
    s = requests.session()
    r3 = s.post(form2_action, form2_payload)
    printres(r3, debug)
    view_all_usage_match = re.search('href="(.+?)">View all usage</a>', r3.text)
    if view_all_usage_match:
        dprint('view_all_usage link found.', debug)
        usagepage = view_all_usage_match.group(1)
    else:
        print('ERROR: view_all_usage link NOT FOUND!  exiting')
        return
    servername3_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r3.url)
    servername3 = servername3_match.group(1)
    fusagepage = servername3 + usagepage
    match = re.search('<!-- Usage Container -->(.+?)<!-- /Usage Container -->', r3.text, re.DOTALL)
    if match:
        usage_html = match.group()
        sdsmatch = re.search('Shared Data Section.+?fontWeightBoldForce">(.+?)</p>.+?End : Shared Data Section', usage_html, re.DOTALL)
        res = cleanv(sdsmatch.group(1))
        dprint('Data Usage Status from Dashboard: {}'.format(res), debug)
        dprint('Data Usage per device from Dashboard:', debug)
        for phoneitem in re.finditer('<li class="phoneItem.+?sdgFirstName">(.+?)</div>.+?sdgUsage">(.+?)</div>', usage_html, re.DOTALL):
            phone_owner = cleanv(phoneitem.group(1))
            phone_usage = cleanv(phoneitem.group(2))
            dprint('\t{0} : {1}'.format(phone_owner, phone_usage), debug)
    else:
        print('WARN: no match in Shared Data Section page')
    dprint('Connecting to {}'.format(fusagepage), debug)
    r4 = s.get(fusagepage)
    printres(r4, debug)
    usageurl_match = re.search('<div id="UsageUrl".+?>.*?([a-zA-Z_0-9\.\-/]+).*?</div>', r4.text, re.DOTALL)
    if usageurl_match:
        dprint('usageurl link found.', debug)
        usageurl = usageurl_match.group(1)
    else:
        print('ERROR: usageurl link NOT FOUND!  exiting')
        return
    servername4_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r4.url)
    servername4 = servername4_match.group(1)
    fusageurl = servername4 + usageurl
    dprint('Connecting to {}'.format(fusageurl), debug)
    r5 = s.get(fusageurl)
    printres(r5, debug)
    timerangematch = re.search('<div id="timeRange".+?left">(.+?)</div>', r5.text, re.DOTALL)
    timerange = cleanv(timerangematch.group(1))
    daysleftmatch = re.search('<strong>Billing Period:</strong>\s*(.+?left)</p>', r5.text)
    daysleft = cleanv(daysleftmatch.group(1))
    print "Billing Period: {0}; {1}".format(timerange, daysleft)
    print
    deviceusage = {}
    match2 = re.search('<span class="fontWeightBoldForce">([\d\.]+).*?/.*?([\d\.]+).*?(MB used).*?<!-- END PIE CHART SECTION -->', r5.text, re.DOTALL)
    if match2:
        cused = cleanv(match2.group(1))
        climit = cleanv(match2.group(2))
        clabel = cleanv(match2.group(3))
        print 'Detailed Data Usage Status: {0} / {1} {2}'.format(cused, climit, clabel)
        print
        print 'Detailed Data Usage per device:'
        for dphoneitem in re.finditer('<td headers="member_head".*?<p class="font14 botMar0"><strong>(.+?)</strong></P>.*?<p class="font14 botMar0">(.+?)</P>.*?<strong>(.+?)</strong>.*?of.*?([0-9,\.]+).*?(MBs used)', r5.text, re.DOTALL):
            dphone_owner = cleanv(dphoneitem.group(1))
            dphone_number = cleanv(dphoneitem.group(2))
            dphone_used = cleanv(dphoneitem.group(3))
            dphone_limit = cleanv(dphoneitem.group(4))
            dphone_label = cleanv(dphoneitem.group(5))
            print '\t{0} : {1} : {2} of {3} {4}'.format(dphone_owner, dphone_number, dphone_used, dphone_limit, dphone_label)
            deviceusage[dphone_number] = [dphone_owner, dphone_used, dphone_limit, dphone_label]
    else:
        print('WARN: no match in Detailed Data Usage page')
    # return 2 dictionaries.
    return { 'timerange': timerange, 'daysleft': daysleft, 'cused': cused, 'climit': climit, 'clabel': clabel }, deviceusage
    
# if being ran as a script, then execute main()
if __name__ == "__main__":
    status = main()
    sys.exit(status)

