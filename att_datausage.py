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


class getforms(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.inForm = False
        self.lasttag = None
        self.lastformname = None
        self.forms_data = {}
        self.forms_input_data = {}
    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            self.inForm = False
            for name, value in attrs:
#                print name, value
                if name == 'id':
                    self.lastformname = value
            #self.forms_data[self.lastformname] = attrs
            self.forms_data[self.lastformname] = {}
            self.forms_input_data[self.lastformname] = {}
            self.inForm = True
            self.lasttag = tag
            fname = ''
            fvalue = ''
            for name, value in attrs:
                #print name, value
                if len(self.forms_data[self.lastformname]) > 0:
                    self.forms_data[self.lastformname].update({name: value})
                else:
                    self.forms_data[self.lastformname] = {name: value}
        if tag == 'input' and self.inForm == True:
            inputname = ''
            inputvalue = ''
            for name, value in attrs:
                #print name, value
                if name == 'name':
                    inputname = value
                    #print inputname
                    if len(self.forms_input_data[self.lastformname]) > 0:
                        self.forms_input_data[self.lastformname].update({inputname: inputvalue})
                    else:
                        self.forms_input_data[self.lastformname] = {inputname: inputvalue}
            for name, value in attrs:
                if name == 'value' and inputname is not None and inputname != '':
                    #print inputname, value
                    if len(self.forms_input_data[self.lastformname]) > 0:
                        self.forms_input_data[self.lastformname].update({inputname: value})
                    else:
                        self.forms_input_data[self.lastformname] = {inputname: value}
            self.lasttag = tag
    def handle_endtag(self, tag):
        if tag == 'form':
            self.inForm = False
    def get_forms_data(self):
        return self.forms_data, self.forms_input_data


class gethrefbaseondata(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.inLink = False
        self.lasttag = None
        self.href = ''
        self.curhref = ''
    def handle_starttag(self, tag, attrs):
        self.inLink = False
        if tag == 'a':
            self.inLink = True
            for name, value in attrs:
                if name == 'href':
                    self.curhref = value
        self.lasttag = tag
    def handle_endtag(self, tag):
        if tag == 'a':
            self.inLink = False
    def handle_data(self, data):
        if data == 'View all usage' and self.lasttag == 'a' and self.inLink == True:
            self.href = self.curhref
    def get_href(self):
        return self.href


class getdatabaseondivid(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.inDiv = False
        self.lasttag = None
        self.udata = ''
        self.curid = ''
    def handle_starttag(self, tag, attrs):
        self.inDiv = False
        if tag == 'div':
            self.inDiv = True
            for name, value in attrs:
                if name == 'id':
                    self.curid = value
        self.lasttag = tag
    def handle_endtag(self, tag):
        if tag == 'div':
            self.inDiv = False
    def handle_data(self, data):
        if self.lasttag == 'div' and self.inDiv == True and self.curid in ('UsageUrl','timeRange'):
            self.udata = data
    def get_udata(self):
        return self.udata


class getparagraphdata(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.inPar = False
        self.lasttag = None
        self.lastdata = None
        self.udata = ''
    def handle_starttag(self, tag, attrs):
        self.inPar = False
        self.lasttag = tag
    def handle_endtag(self, tag):
        pass
    def handle_data(self, data):
        if self.lastdata == 'Billing Period:':
            self.udata = data
        self.lastdata = data
    def get_udata(self):
        return self.udata

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
    hparser = getforms()
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
    hparser3 = gethrefbaseondata()
    hparser3.feed(r3.text)
    usagepage = hparser3.get_href()
    servername3_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r3.url)
    servername3 = servername3_match.group(1)
    fusagepage = servername3 + usagepage
#    match = re.search('<!-- Usage Container -->(.+?)<!-- /Usage Container -->', r3.text, re.DOTALL)
#    if match:
#        usage_html = match.group()
#        sdsmatch = re.search('Shared Data Section.+?fontWeightBoldForce">(.+?)</p>.+?End : Shared Data Section', usage_html, re.DOTALL)
#        if sdsmatch:
#            res = cleanv(sdsmatch.group(1))
#            dprint('Data Usage Status from Dashboard: {}'.format(res), debug)
#            dprint('Data Usage per device from Dashboard:', debug)
#            for phoneitem in re.finditer('<li class="phoneItem.+?sdgFirstName">(.+?)</div>.+?sdgUsage">(.+?)</div>', usage_html, re.DOTALL):
#                phone_owner = cleanv(phoneitem.group(1))
#                phone_usage = cleanv(phoneitem.group(2))
#                dprint('\t{0} : {1}'.format(phone_owner, phone_usage), debug)
#        else:
#            print('WARN: no match in Shared Data Section page')
#    else:
#        print('WARN: no match in Usage Container page')
    dprint('Connecting to {}'.format(fusagepage), debug)
    r4 = s.get(fusagepage)
    printres(r4, debug)
    hparser5 = getdatabaseondivid()
    hparser5.feed(r4.text)
    usageurl = cleanv(hparser5.get_udata())
    servername4_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r4.url)
    servername4 = servername4_match.group(1)
    fusageurl = servername4 + usageurl
    dprint('Connecting to {}'.format(fusageurl), debug)
    r5 = s.get(fusageurl)
    printres(r5, debug)
    hparser5.feed(r5.text)
    timerange = cleanv(hparser5.get_udata())
    hparser6 = getparagraphdata()
    hparser6.feed(r5.text)
    daysleft = cleanv(hparser6.get_udata())
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

