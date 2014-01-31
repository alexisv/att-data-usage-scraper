#! /usr/bin/python

# att-datausage-scraper.py
# created by Alexis Villalon alexisv@gmail.com
#

import requests
import re
import string
import sys
import getopt

atturl = 'http://www.att.com'

this = sys.argv[0]

userid = ''
password = ''
debug = ''

def printhelp():
    print '{} -h'.format(this)
    print '{} [-d] -u <userid> -p <password>'.format(this)
    print '{} [-d] --userid=<userid> --password=<password>'.format(this)

def printRes(req):
    if debug == 'Y':
        print 'Status Code: {}'.format(req.status_code)
        print 'URL now: {}'.format(req.url)
        print 'History: {}'.format(req.history)

def dprint(message):
    if debug == 'Y':
        print message

try:
    opts, args = getopt.getopt(sys.argv[1:], "dhu:p:", ["userid=", "password="])
except getopt.GetoptError:
    printhelp()
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        printhelp()
        sys.exit(0)
    elif opt == '-d':
        debug = 'Y'
    elif opt in ("-u", "--userid"):
        userid = arg
    elif opt in ("-p", "--password"):
        password = arg

if userid == '':
    printhelp()
    sys.exit(3)
elif password == '':
    printhelp()
    sys.exit(3)

dprint('Connecting to {}'.format(atturl))
r = requests.get(atturl)
printRes(r)

dprint('Looking for form with id ssoLoginForm')
fmatch = re.search('<form id="ssoLoginForm".+?</form>', r.text, re.DOTALL)
if fmatch:
    dprint('form id ssoLoginForm found')
    form1 = fmatch.group()
else:
    dprint('form not found! exiting')
    sys.exit(4)

dprint('Getting method, action, and input fields from the form...')
form1_action_match = re.search('<form.+?method="(.+?)".+?action="(.+?)"', form1)
if form1_action_match:
    dprint('action and method found.')
    form1_method = form1_action_match.group(1)
    form1_action = form1_action_match.group(2)
    dprint('Method: {}'.format(form1_method))
    dprint('Action: {}'.format(form1_action))
else:
    dprint('action and method not found in form1!')
    sys.exit(4)

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
    dprint("FORM method is not post! exiting.")
    sys.exit(4)

dprint('Data payload: {}'.format(form1_payload))
dprint('Connecting to {}'.format(form1_action))

r2 = requests.post(form1_action, data=form1_payload)
printRes(r2)

dprint('Looking for form with id tGuardLoginForm')
f2match = re.search('<form.+?id="tGuardLoginForm".+?</form>', r2.text, re.DOTALL)
if f2match:
    dprint('form id tGuardLoginForm found')
    form2 = f2match.group()
else:
    dprint('form not found! exiting')
    sys.exit(4)

# assumption in this re: form parameters has action came first before method.
dprint('Getting method, action, and input fields from the form...')
form2_action_match = re.search('<form.+?action="(.+?)".+?method="(.+?)"', form2)
if form2_action_match:
    dprint('action and method found.')
    form2_action = form2_action_match.group(1)
    form2_method = form2_action_match.group(2)
    dprint('Method: {}'.format(form2_method))
    dprint('Action: {}'.format(form2_action))
else:
    dprint('action and method not found in form2!')
    sys.exit(4)

form2_payload = {}

for form2_input in re.finditer('<input.* name="(.+?)".*?>', form2):
    form2_input_name = form2_input.group(1)
    v2match = re.search('value="(.+?)"',form2_input.group(0))
    if v2match:
       form2_payload[form2_input_name] = v2match.group(1)

if string.lower(form2_method) != 'post':
    dprint("FORM method is not post! exiting.")
    sys.exit(4)

dprint('Data payload: {}'.format(form2_payload))
dprint('Connecting to {}'.format(form2_action))

# create session
s = requests.session()

r3 = s.post(form2_action, form2_payload)
printRes(r3)

view_all_usage_match = re.search('href="(.+?)">View all usage</a>', r3.text)
if view_all_usage_match:
    dprint('view_all_usage link found.')
    usagepage = view_all_usage_match.group(1)
else:
    dprint('view_all_usage link NOT FOUND!  exiting')
    sys.exit(4)

servername3_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r3.url)
servername3 = servername3_match.group(1)
fusagepage = servername3 + usagepage

match = re.search('<!-- Usage Container -->(.+?)<!-- /Usage Container -->', r3.text, re.DOTALL)

if match:
    usage_html = match.group()
    sdsmatch = re.search('Shared Data Section.+?fontWeightBoldForce">(.+?)</p>.+?End : Shared Data Section', usage_html, re.DOTALL)
    res = re.sub('<.+?>', ' ', sdsmatch.group(1))
    res = re.sub('&nbsp;', ' ', res)
    res = re.sub('  ',' ',res)
    print 'Data Usage Status: {}'.format(res)
    print
    print 'Data Usage per device:'
    for phoneitem in re.finditer('<li class="phoneItem.+?sdgFirstName">(.+?)</div>.+?sdgUsage">(.+?)</div>', usage_html, re.DOTALL):
        phone_owner = phoneitem.group(1)
        phone_usage = phoneitem.group(2)
        phone_owner = re.sub("\t",'',phone_owner)
        phone_owner = re.sub("\r\n",'',phone_owner)
        phone_usage = re.sub("\t",'',phone_usage)
        phone_usage = re.sub("\r\n",'',phone_usage)
        phone_usage = re.sub('<.+?>', ' ',phone_usage)
        phone_usage = re.sub('&nbsp;', ' ',phone_usage)
        phone_usage = re.sub('  ',' ',phone_usage)
        print '\t{0} : {1}'.format(phone_owner, phone_usage)
else:
    dprint('no match')

dprint('Connecting to {}'.format(fusagepage))
r4 = s.get(fusagepage)
printRes(r4)

usageurl_match = re.search('<div id="UsageUrl".+?>.*?([a-zA-Z_0-9\.\-/]+).*?</div>', r4.text, re.DOTALL)
if usageurl_match:
    dprint('usageurl link found.')
    usageurl = usageurl_match.group(1)
else:
    dprint('usageurl link NOT FOUND!  exiting')
    sys.exit(4)

servername4_match = re.search('(http.*://[a-zA-Z_0-9\.\-]+[:0-9]*)/.+',r4.url)
servername4 = servername4_match.group(1)
fusageurl = servername4 + usageurl

dprint('Connecting to {}'.format(fusageurl))
r5 = s.get(fusageurl)
printRes(r5)

timerangematch = re.search('<div id="timeRange".+?left">(.+?)</div>', r5.text, re.DOTALL)
timerange = timerangematch.group(1)
timerange = re.sub("(\t|\r\n)", '', timerange)
timerange = re.sub('  ', ' ', timerange)

daysleftmatch = re.search('<strong>Billing Period:</strong>\s*(.+?left)</p>', r5.text)
daysleft = daysleftmatch.group(1)
daysleft = re.sub("(\t|\r\n)", '', daysleft)
daysleft = re.sub('  ', ' ', daysleft)

print "Billing Period: {0}; {1}".format(timerange, daysleft)
print

match2 = re.search('<span class="fontWeightBoldForce">([\d\.]+).*?/.*?([\d\.]+).*?(MB used).*?<!-- END PIE CHART SECTION -->', r5.text, re.DOTALL)
if match2:
    cused = match2.group(1)
    climit = match2.group(2)
    clabel = match2.group(3)
    print 'Detailed Data Usage Status: {0} / {1} {2}'.format(cused, climit, clabel)
    print
    print 'Detailed Data Usage per device:'

    for dphoneitem in re.finditer('<td headers="member_head".*?<p class="font14 botMar0"><strong>(.+?)</strong></P>.*?<p class="font14 botMar0">(.+?)</P>.*?<strong>(.+?)</strong>.*?of.*?([0-9,\.]+).*?(MBs used)', r5.text, re.DOTALL):
        dphone_owner = dphoneitem.group(1)
        dphone_number = dphoneitem.group(2)
        dphone_used = dphoneitem.group(3)
        dphone_limit = dphoneitem.group(4)
        dphone_label = dphoneitem.group(5)
	dphone_number = re.sub("\t",'',dphone_number)
	dphone_number = re.sub("\r\n",'',dphone_number)
        print '\t{0} : {1} : {2} of {3} {4}'.format(dphone_owner, dphone_number, dphone_used, dphone_limit, dphone_label)
else:
    dprint('no match')

