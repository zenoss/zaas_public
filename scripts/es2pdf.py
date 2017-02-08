#!/usr/bin/python

#################################
# elasticsearch to PDF exporter #
#    (c) Taylor Glaeser         #
#        Zenoss, Inc.           #
#        2014                   #
#################################

IMPORT_ERRORS = {}

try:
    import os    #Standard library, used to interact with system and console
    import json  #Standard library, used to convert HTTP response to a python dictionary
    import ConfigParser  #Standard library, used to parse a standard formatted config file
    import argparse  #Standard library, used to parse command-line arguments
    from time import time, gmtime, strftime  #Standard library, used to determine current time
    import datetime  #Standard library, used to compute date operations
    import requests  # Non-standard library, used to easily send HTTP requests
    from fpdf import FPDF  # Non-standard library, used to export text to a PDF file
    import encryptPDF  # Custom library, based on pyPdf to encrypt a PDF
except ImportError as e:
    if str(e).split(" ")[-1] == "encryptPDF":
        print "The encryptPDF library is not installed.\nYou will be unable to encrypt the PDF."
        while True:
            ans = raw_input("Continue?\n(y/n): ")
            if ans.lower() == ("y" or "ye" or "yes"):
                IMPORT_ERRORS[str(e).split(" ")[-1]] = False
                break
            elif ans.lower() == ("n" or "no"):
                exit("Exiting due to user...")
            else:
                print "Please use (y)es or (n)o."
    else:        
        exit("Module: " + __name__ + "\nError: " + str(e))




## START GLOBAL VARIABLES ##

DEBUG_MODE = False  #Set debug mode through CL arg

### DEFAULTS ###
DEFAULT_CONFIG = "es2pdf.cfg"  #Default config file
DEFAULT_QUERIES = "es2pdfqueries.json"  #Default JSON query file
DEFAULT_SECTION = "Defaults"  #Default section of config file
DEFAULT_INDEX = "logstash-"  #Default index prefix


### CONFIG FILE VARIABLES ###
TITLE_PDF = ""  #Title of the PDF
ES_QUERY = ""  #Elasticsearch Query
PDF_SAVE_TEMPLATE = ""  #How the PDF file name will appear when saved
LETTERHEAD_PNG = ""  #PNG file for the letter head in PDF
ES_IP_ADDR = ""  #IP Address and port of elasticsearch
MAX_RESULT = 0  #How many results are actually printed
SEARCH_DAY = ""  #Date of index suffix to search from
OPEN_PDF = False  #Whether or not to open PDF after script finishes


### JSON INDEX DICTIONARIES ###
FIELDS = {}  #Fields from elasticsearch to search for and print to the PDF
FIELDS_ORDERED = []  #Fields from elasticsearch ordered in the order from config
FIELDS_NUMBERED = {}  #Fields from elasticsearch but with an index number (i.e. value0, value1, value2, etc)
LIST_FIELDS = False  #Whether or not to list all available fields to print from elasticsearch query
globalList = {}  #List used to store parsed JSON  (values are in format "value0", "value1", "value2", etc...)
globalListFields = {}  #List used to store parsed fields (values are only stored as "value")
TOTAL_MAX_RESULTS = 0
GLOBAL_CELL_INFO = {}

### DATE VARIABLES ###
DATE_RANGE = []
DATE_RANGE_COUNTER = 0
START_DATE = []


## END GLOBAL VARIABLES ##




def sort_keys(keyDict, curResult):
    d_sub = keyDict["hits"]["hits"][curResult]

    global globalList
    global FIELDS_NUMBERED
    global DATE_RANGE_COUNTER

    if len(DATE_RANGE) > 0:
        if DATE_RANGE_COUNTER == 0:
            globalList = {}
        if DATE_RANGE_COUNTER > 0:
            globalList = globalList

    has_fields_stored = False

    def recurse(curDict, depth=-1, currentDictKey="", r=0):
        if depth != 0:
            if r > 0:

                if (type(curDict.get(currentDictKey)) is dict) and (len(curDict.get(currentDictKey)) > 0):
                    curDict_sub = curDict.get(currentDictKey) #Set sub dict as primary dict

                    for i in dict(curDict_sub):
                        recurse(curDict_sub, depth-1, curDict_sub, 0)
                else:

                    if (type(curDict.get(currentDictKey)) is list):
                        list_dict = curDict.get(currentDictKey)
                        if len(list_dict) > 0:
                            list_dict_str = str(list_dict[0])
                        else:
                            list_dict_str = ""
                        globalList[currentDictKey+str(curResult)+str(DATE_RANGE_COUNTER)] = list_dict_str.replace("\n", "")
                        globalListFields[currentDictKey] = list_dict_str.replace("\n", "")
                    elif (type(curDict.get(currentDictKey)) is str):
                        globalList[currentDictKey+str(curResult)+str(DATE_RANGE_COUNTER)] = str(curDict.get(currentDictKey)).replace("\n", "")
                        globalListFields[currentDictKey] = str(curDict.get(currentDictKey)).replace("\n", "")
                    else: 
                        globalList[currentDictKey+str(curResult)+str(DATE_RANGE_COUNTER)] = str(curDict.get(currentDictKey))
                        globalListFields[currentDictKey] = str(curDict.get(currentDictKey))

            else:
                for i in currentDictKey:
                        recurse(curDict, depth-1, i, r+1)

    recurse(d_sub, -1, d_sub)


    if DEBUG_MODE == True:
        print "globalList: "+globalList
        raw_input()

    if LIST_FIELDS is True:
            print ("#")*34 + "\n###   BEGIN AVAILABLE FIELDS   ###"         
            print ("#")*34 + "\n### Template                   ###\n### Field : Current field data ###\n" + ("#")*34
            for i in globalListFields:   
                print "### " + str(i) + " : " + str(globalListFields[i])
            print ("#")*34 + "\n###    END AVAILABLE FIELDS    ###\n" + ("#")*34
            exit()

    
    for i in FIELDS_ORDERED:
        try:
            FIELDS_NUMBERED[i[0]+str(curResult)+str(DATE_RANGE_COUNTER)] = [FIELDS[i[0]][0],str(globalList.get(i[0]+str(curResult)+str(DATE_RANGE_COUNTER)))]
            if FIELDS_NUMBERED[i[0]+str(curResult)+str(DATE_RANGE_COUNTER)][1] == "None":
                FIELDS_NUMBERED[i[0]+str(curResult)+str(DATE_RANGE_COUNTER)][1] = "Not a valid field!!"

        except KeyError, e:
            raise e
            #print "No such value " + str(i)
        has_fields_stored = True


    return


def parseJSON(d):
    global DATE_RANGE_COUNTER
    global GLOBAL_CELL_INFO

    if DEBUG_MODE is False:
        try:
            if MAX_RESULT == -1:
                totalResults = len(d["hits"]["hits"])
            else:
                totalResults = MAX_RESULT
            if totalResults > len(d["hits"]["hits"]):
                totalResults = len(d["hits"]["hits"])
        except KeyError as e:
            print d
            raw_input()

            exit(e)

    elif DEBUG_MODE is True:
        totalResults = TEST_RESULT


    if totalResults <= 0:
        print "No results."

    else:
        for i in range(totalResults):
            sort_keys(d, i)
        
        cellInfo = {}
        
        
        error_list = []
        
        for i in range(totalResults):     
            cellInfo["res"+str(i)+str(DATE_RANGE_COUNTER)] = ""
            for j in FIELDS_ORDERED:
                try:

                    cellInfo["res"+str(i)+str(DATE_RANGE_COUNTER)] += (FIELDS_NUMBERED[j[0]+str(i)+str(DATE_RANGE_COUNTER)][0]).rstrip("\n") + " " + (FIELDS_NUMBERED[j[0]+str(i)+str(DATE_RANGE_COUNTER)][1]).rstrip("\n") + "\n"
                except KeyError as e:
                    print "No value for "+"res"+str(i)+str(l)
                    error_list.append(e)
                    #cellInfo.pop("res"+str(i)+str(l), None)
        

        

        GLOBAL_CELL_INFO.update(cellInfo)

        createPDF(GLOBAL_CELL_INFO)
            
        
    
def createPDF(values):
    global DATE_RANGE_COUNTER
    global DATE_RANGE
    if len(values) > 0:
        if DATE_RANGE_COUNTER == int(len(DATE_RANGE)):
            pdfPath = "./pdfs/"  #Where the pdfs are stored

            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", "B", 24) # Render header
            pdf.cell(0, 10, TITLE_PDF, border=0,align="C", ln=1)

            pdf.set_font("Arial", "", 12) # Render date range
            if len(DATE_RANGE) == 1:
                d_range = DATE_RANGE[0] + " to " + DATE_RANGE[0]
            elif len(DATE_RANGE) > 1:
                if (datetime.datetime.strptime(DATE_RANGE[0], "%Y.%m.%d") - datetime.datetime.strptime(DATE_RANGE[-1], "%Y.%m.%d")).days < 0:
                    d_range = DATE_RANGE[0] + " to " + DATE_RANGE[-1]
                elif (datetime.datetime.strptime(DATE_RANGE[0], "%Y.%m.%d") - datetime.datetime.strptime(DATE_RANGE[-1], "%Y.%m.%d")).days > 0:
                    d_range = DATE_RANGE[-1] + " to " + DATE_RANGE[0]
            elif len(DATE_RANGE) == 0:
                d_range = SEARCH_DAY + " to " + SEARCH_DAY
            pdf.cell(0, 10, "Date Range: " + d_range, border=0,align="C", ln=1)

            if LETTERHEAD_PNG != "None": # Render image
                pdf.image(LETTERHEAD_PNG,5, 5, 60, 0)
            pdf.set_font("Courier", "", 10)

            errors = 0
            for j in range(len(values)+1): # Render body
                for i in range(len(values)+1):
                    try:
                        pdf.multi_cell(0, 6, values["res"+str(i)+str(j)], border=1)
                    except KeyError as e:
                        errors += 1    #May do something with this later, not really important though

            curUTC = strftime("%Y-%m-%dT%H-%M-%SZ", gmtime(time())) # Determine current time for filename
            curPDF = PDF_SAVE_TEMPLATE + "-" + curUTC + ".pdf"
            if os.path.isdir("./pdfs") == False:
                os.mkdir("./pdfs")
            

            pdf.output(pdfPath+curPDF, "F")
            
            print "\n\n" + "-"*15 + "\n\n\nPDF was successfully generated.\nPDF is saved at location "+pdfPath+curPDF
            
            if IMPORT_ERRORS.get("encryptPDF") is not False:    
                encryptPDF.encrypt(pdfPath,curPDF) # Encrypt PDF
                print "PDF was successfully encrypted. Encrypted PDF will be in same directory."
                if OPEN_PDF == True:
                    os.system("open "+str(pdfPath)+"enc-"+str(curPDF))
            else:
                print "Cannot encrypt the PDF due to missing module..."
                if OPEN_PDF == True:
                    os.system("open "+str(pdfPath)+str(curPDF))
    else:
        print "\nNothing to output...\nDid you use a valid query?"
        


def startQuery(q=ES_QUERY, r=MAX_RESULT, ip=ES_IP_ADDR, index=DEFAULT_INDEX, date=None, q_json=None):
    global DATE_RANGE_COUNTER
    global GLOBAL_CELL_INFO
    global DATE_RANGE

    if q == None: q = ES_QUERY
    if ip == None: ip = ES_IP_ADDR
   
    if r == None: 
        r = MAX_RESULT
    elif r == "all":
        r = MAX_RESULT
    
    if index != None: 
        if index != DEFAULT_INDEX:
            date = "OMIT"
    elif index == None:
        index = DEFAULT_INDEX

    if date == None:
        date = strftime("%Y.%m.%d", gmtime(time() - 86400))
    elif date == "OMIT":
        date = ""

    if len(DATE_RANGE) > 0:
        for date_r in DATE_RANGE:
            if DEBUG_MODE is False:
                if MAX_RESULT == -1:    
                    response_results = requests.get("http://" + ip + "/" + index + date_r + "/_search?search_type=scan&scroll=10m&size=50" + "&q=" + q)
                    if response_results.status_code == 200:
                        r = response_results.json()["hits"]["total"]
                if q_json != None:
                    response = requests.get("http://" + ip + "/" + index + date_r + "/_search", data=q_json)
                else:
                    response = requests.get("http://" + ip + "/" + index + date_r + "/_search?size=" + str(r) + "&q=" + q)
                if response.status_code == 200:
                    print ":) - " + str(response.status_code) + " - " + index+date_r
                    parseJSON(response.json())
                else:
                    print ":( - " + str(response.status_code) + " - " + index+date_r
                DATE_RANGE_COUNTER += 1

            elif DEBUG_MODE is True:
                print "http://" + ip + "/" + index + date_r + "/_search?size=" + str(r) + "&q=" + q
                parseJSON(jsontext)
                DATE_RANGE_COUNTER += 1
        createPDF(GLOBAL_CELL_INFO)


    else:
        if DEBUG_MODE is False:
            DATE_RANGE = [date]
            if MAX_RESULT == -1:    
                response_results = requests.get("http://" + ip + "/" + index + date + "/_search?search_type=scan&scroll=10m&size=50" + "&q=" + q)
                if response_results.status_code == 200:
                    r = response_results.json()["hits"]["total"]
            if q_json != None:
                response = requests.get("http://" + ip + "/" + index + date + "/_search", data=q_json)
            else:
                response = requests.get("http://" + ip + "/" + index + date + "/_search?size=" + str(r) + "&q=" + q)
            if response.status_code == 200:
                print ":) - " + str(response.status_code) + " - " + index+date
                parseJSON(response.json())    
            else:
                print ":( - " + str(response.status_code) + " - " + index+date
            DATE_RANGE_COUNTER += 1
            createPDF(GLOBAL_CELL_INFO)

        elif DEBUG_MODE is True:
            print "http://" + ip + "/" + index + date + "/_search?size=" + str(r) + "&q=" + q
            parseJSON(jsontext)
            DATE_RANGE_COUNTER += 1
            createPDF(GLOBAL_CELL_INFO)


def giveDays(dates):
    dt = datetime.datetime
    try:
        start = dates.split("-")[0].strip()
        end = dates.split("-")[1].strip()
    except IndexError as e:
        exit("Invalid date range given.\n"+str(e))
        

    try:
        date_s_dt = dt.strptime(start, "%Y.%m.%d")
        date_e_dt = dt.strptime(end, "%Y.%m.%d")
        date_delta = date_e_dt - date_s_dt
        dates = []
        num_days = date_delta.days
    except ValueError as e:
        exit("Invalid date range given.\n"+str(e))


    if num_days < 0:
        for i in range((num_days*(-1))+1):
            dates.append(dt.strftime(date_e_dt + datetime.timedelta(days=i), "%Y.%m.%d"))
        return dates
    elif num_days > 0:
        for i in range(num_days+1):
            dates.append(dt.strftime(date_s_dt + datetime.timedelta(days=i), "%Y.%m.%d"))
        return dates
    else:
        return [start]


def parseConfig(c=DEFAULT_CONFIG, s=DEFAULT_SECTION):
    try:
        config = ConfigParser.RawConfigParser()
        config.read(c)
        
        if s == None : s = DEFAULT_SECTION

        global TITLE_PDF
        global ES_QUERY
        global PDF_SAVE_TEMPLATE
        global LETTERHEAD_PNG
        global ES_IP_ADDR
        global MAX_RESULT
        global SEARCH_DAY
        global FIELDS  
        global FIELDS_ORDERED

        TITLE_PDF = config.get(s, "title_of_PDF")
        ES_QUERY = config.get(s, "elasticsearch_query")
        PDF_SAVE_TEMPLATE = config.get(s, "pdf_filename_prefix")
        LETTERHEAD_PNG = config.get(s, "letterhead_image")
        ES_IP_ADDR = config.get(s, "elasticsearch_ip")
        
        if config.get(s, "max_search_results") == "all":
            MAX_RESULT = -1
        elif MAX_RESULT == -1:
            MAX_RESULT = -1
        else:
            MAX_RESULT = config.getint(s, "max_search_results")
        

        SEARCH_DAY = config.get(s, "index_day_to_search")
        
        fields_list = config.items("fields_to_print")
        FIELDS_ORDERED = fields_list

        for i in fields_list:
            FIELDS[i[0]] = [i[1]]
        
        if SEARCH_DAY == "yesterday":
            SEARCH_DAY = strftime("%Y.%m.%d", gmtime(time() - 86400))

    except ConfigParser.NoSectionError as e:
        exit("No config file found...")


def parseQueries(q_return, q_file=DEFAULT_QUERIES):
    if q_return != None: 
        try:
            f = open(q_file, "r")
        except IOError as e:
            exit(str(q_file) + " does not exist!\nRun without the '-j' flag or create the file.")
        queries = {}
        temp_stor = ""

        for line in f:
            temp_stor += line.strip()

        temp_list = temp_stor.split("$")
        temp_list.pop(0)
        
        for i in temp_list:    
            queries[i.split("==")[0].strip()] = i.split("==")[1]
        if queries.get(q_return) == None:
            exit("Invalid JSON key: "+q_return)
        else:
            return queries.get(q_return).strip()
    else:
        return None


def parseArgs():
    
    global LIST_FIELDS
    global DEBUG_MODE
    global MAX_RESULT
    global DATE_RANGE
    global OPEN_PDF

    parser = argparse.ArgumentParser(description="Output an elasticsearch query to PDF")
    
    parser.add_argument("-c", "--config", dest="config", default=DEFAULT_CONFIG, metavar="CONFIG", help="Change what config file to use")
    parser.add_argument("-s", "--section", dest="section", default=None, metavar="SECTION", help="Change what config section to use")
    parser.add_argument("-ip", "--ipaddress", dest="ip", default=None, metavar="IPADDR:PORT", help="Change what IP address and port is used to connect to elasticsearch")
    parser.add_argument("-i", "--index", dest="index", default=DEFAULT_INDEX, metavar="INDEX", help="Change what index to query (Default is \'logstash-\')")
    parser.add_argument("-d", "--date", dest="date", default=None, metavar="YYYY.MM.DD", help="Change what index date to query (Default is yesterday)")
    parser.add_argument("-q", "--query", dest="query", default=None, metavar="QUERY", help="Change what query to execute")
    parser.add_argument("-r", "--results", dest="results", default=None, metavar="RESULTS", help="Change the number of results requested")
    parser.add_argument("-f", "--fields", action="store_true", help="List all available fields to output from elasticsearch query")
    parser.add_argument("-debug", action="store_true", help="Run es2pdf in debug mode (i.e. Using premade JSON strings)")
    parser.add_argument("-dr", "--daterange", dest="daterange", default=None, metavar="YYYY.MM.DD-YYYY.MM.DD", help="Choose a date range to run es2pdf through.")
    parser.add_argument("-o", "--open", dest="open", action="store_true", help="Open PDF after script finishes")
    parser.add_argument("-j", "--json", dest="json", default=None, metavar="JSON_QUERY", help="Choose what premade JSON query to use from queries file")

    args_ = parser.parse_args()

    if vars(args_)["open"] == True:
        OPEN_PDF = True


    if vars(args_)["daterange"] != None:
        DATE_RANGE = giveDays(vars(args_)["daterange"])    

    LIST_FIELDS = vars(args_)["fields"]
    DEBUG_MODE = vars(args_)["debug"]
    

    results_ = vars(args_)["results"]
    if results_ == "all":
            MAX_RESULT = -1


    if vars(args_)["date"] == "yesterday":
            vars(args_)["date"] = strftime("%Y.%m.%d", gmtime(time() - 86400))

    return vars(args_)


if __name__ == '__main__':
    args = parseArgs()
    parseConfig(args["config"], args["section"])
    query_json = parseQueries(args["json"])
    startQuery(args["query"], args["results"], args["ip"], args["index"], args["date"], query_json)


