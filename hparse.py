import HTMLParser

TIMERANGE_DIV_ID = 'timeRange'
BILLING_PERIOD_P_DATA = 'Billing Period:'
TOTAL_DATA_USAGE_P_ATTRS = 'left PadTop10 botMar0 center'

class gettableinfo(HTMLParser.HTMLParser):
    def __init__(self):
        self.reset()
        self.inTable = False
        self.inTR = False
        self.inTD = False
        self.inOwnerName = False
        self.inOwnerPhone = False
        self.inData = False
        self.TRcntr = 0
        self.TDcntr = 0
        self.TD_Pcntr = 0
        self.curname = ''
        self.curphone = ''
        self.curdata = ''
        self.lasttag = ''
        self.inP = False
        self.lastPdata = ''
        self.billingperiodinfo = ''
        self.inDIV = False
        self.curDivId = ''
        self.timerange = ''
        self.inTotalUsage = False
        self.totalusage = ''
        self.table_data = {}
    def handle_starttag(self, tag, attrs):
        #print 'start ', tag
        self.inOwnerName = False
        self.inOwnerPhone = False
        self.inData = False
        self.inP = False
        self.inDIV = False
        #self.inTotalUsage = False
        if tag == 'tbody':
            self.inTable = True
        if self.inTable == True and tag == 'tr':
            self.inTR = True
            self.TRcntr = self.TRcntr + 1
            self.curname = ''
            self.curphone = ''
            self.curdata = ''
        if self.inTR == True and tag == 'td':
            self.inTD = True
            self.TD_Pcntr = 0
            self.TDcntr = self.TDcntr + 1
        if self.inTD == True and tag == 'p':
            self.TD_Pcntr = self.TD_Pcntr + 1
        if self.inTD == True and tag == 'strong' and self.TDcntr == 1:
            self.inOwnerName = True
            #print 'ownername found'
        if self.inTD == True and tag == 'p' and self.TDcntr == 1 and self.TD_Pcntr == 2:
            self.inOwnerPhone = True
            #print 'ownerphone found'
        if self.inTD == True and self.TDcntr == 2:
            if tag in ('span', 'strong', 'abbr'):
                self.inData = True
                #print 'data found'
        #print "TR cntr = ", self.TRcntr
        #print "TD cntr = ", self.TDcntr
        #print "TD P cntr = ", self.TD_Pcntr
        if tag == 'div':
            self.inDIV = True
            for name, value in attrs:
                if name == 'id':
                    self.curDivId = value
                    #print 'starttag curDivId: ', self.curDivId
        if tag == 'p':
            for name, value in attrs:
                if name == 'class' and value == TOTAL_DATA_USAGE_P_ATTRS:
                    self.inTotalUsage = True
                    #print 'in Total Usage'
        self.lasttag = tag
    def handle_endtag(self, tag):
        #print 'end ', tag
        if tag == 'tbody':
            self.inTable = False
            self.TRcntr = 0
        if tag == 'tr':
            self.inTR = False
            self.TDcntr = 0
        if tag == 'td':
            self.inTD = False
            self.inData = False
            self.TD_Pcntr = 0
        if tag == 'strong' and self.inOwnerName == True:
            #print 'set inOwnerName to false'
            self.inOwnerName == False
        if tag == 'p' and self.inOwnerPhone == True:
            #print 'set inOwnerPhone to false'
            self.inOwnerPhone == False
        if tag == 'abbr' and self.inData == True:
            #print 'set inData to false'
            self.inData = False
        if tag == 'div':
            self.inDIV = False
        if tag == 'p' and self.inTotalUsage == True:
            self.inTotalUsage = False
    def handle_data(self,data):
        if self.inTD == True:
            if self.inOwnerName == True:
                self.curname = self.curname + ' '.join(data.split())
                #print 'Owner name: ', ' '.join(self.curname.split())
            elif self.inOwnerPhone == True:
                self.curphone = self.curphone + ' '.join(data.split())
                #print 'Owner phone: ', ' '.join(self.curphone.split())
            elif self.inData == True:
                self.curdata = ' '.join(self.curdata.split()) + " " + ' '.join(data.split())
                #print 'Data info: ', ' '.join(self.curdata.split())
            #else:
                #print "Data: ", data
            if self.lasttag == 'abbr' and self.inData == True:
                #print self.curname, self.curphone, self.curdata
                self.table_data[self.curphone] = {'name': self.curname, 'data': self.curdata}
        if self.lastPdata == BILLING_PERIOD_P_DATA:
            self.billingperiodinfo = ' '.join(data.split())
        self.lastPdata = data
        if self.lasttag == 'div' and self.inDIV == True and self.curDivId == TIMERANGE_DIV_ID:
            #print 'handledata: ', data
            self.timerange = ' '.join(data.split())
        if self.inTotalUsage:
            self.totalusage = ' '.join(self.totalusage.split()) + " " + ' '.join(data.split())
            #print 'inTotalUsage :', self.totalusage
    def get_table_data(self):
        return self.totalusage, self.timerange, self.billingperiodinfo, self.table_data


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
        if self.lasttag == 'div' and self.inDiv == True and self.curid == 'UsageUrl':
            self.udata = ' '.join(data.split())
    def get_udata(self):
        return self.udata


