#!/usr/bin/python
try:
    import boto.ec2, boto.vpc
    import time
    import gdata.spreadsheet.service
    import json
    import argparse
    import ConfigParser
except ImportError as e:
    exit("Error: " + str(e))

DEBUG_MODE = False

DEFAULT_CONFIG = "aws2spreadsheet.cfg"


#SPSHEET_IDS = {"Test Spreadsheet": "tbrhwxJxZfhjpXmRLmLPRsg"}
#WKSHEET_IDS = {"Instances" : "od6", "VPCs" : "od7", "Subnets" : "od4", "Route Tables" : "od5", "Elastic IPs": "oda", "Network ACLs": "odb", "Security Groups": "od8"}

spr_client = gdata.spreadsheet.service.SpreadsheetsService()
spr_client.email = ''
spr_client.password = ''
spr_client.ProgrammaticLogin()

class OutputInfo:
    def __init__(self):
        self.worksheet_ids = {}
        self.spreadsheet_id = ""
        self.aws_info_global = {}



class FindSPR_IDS:

  def __init__(self):
    self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    self.gd_client.email = spr_client.email
    self.gd_client.password = spr_client.password
    self.gd_client.ProgrammaticLogin()
    self.curr_key = ""
    self.keys = ""
    self.curr_wksht_ids = {}
    
  def getSpreadsheets(self, search):
    feed = self.gd_client.GetSpreadsheetsFeed()
    self.returnInfo(feed)
    id_parts = self.keys.split('\n')
    self.keys = ""
    for s in id_parts:
        if s.split("$$")[0] == search:
            self.curr_key = s.split("$$")[1]
            return


  def getWorksheets(self, search):
    feed = self.gd_client.GetWorksheetsFeed(self.curr_key)
    self.returnInfo(feed)
    id_parts = self.keys.split("\n")
    self.keys = ""
    for s in id_parts:
        if s.split("$$")[0] == search:
            self.curr_wksht_ids[search] = s.split("$$")[1]

  def returnInfo(self, feed):
    for i, entry in enumerate(feed.entry):
        self.keys +=  '%s$$%s\n' % (entry.title.text, entry.id.text.split('/')[-1])




def fixJSON(string_error):
    new_str_error = ""

    i = 0
    while i < len(string_error):
        if string_error[i] == "\'":
            new_str_error += "\""
        else:
            new_str_error += string_error[i]
        i += 1

    return json.loads(new_str_error)


def getAWSInfo():
    aws_info = {"instances" : [], "vpcs" : [], "subnets" : [], "route_tables" : [], "elastic_ips": [], "network_acls": [], "security_groups": []}

    
    #Zenoss Production AWS Key
    ec2_conn = boto.ec2.connect_to_region("us-east-1", aws_access_key_id="INSERT ID HERE", aws_secret_access_key="INSERT KEY HERE")
    vpc_conn = boto.vpc.VPCConnection(aws_access_key_id="INSERT KEY HERE", aws_secret_access_key="INSERT KEY HERE")


    reservations = ec2_conn.get_all_reservations()
    security_groups = ec2_conn.get_all_security_groups()

    vpcs = vpc_conn.get_all_vpcs()
    network_acls = vpc_conn.get_all_network_acls()
    route_tables = vpc_conn.get_all_route_tables()
    subnets = vpc_conn.get_all_subnets()
    elastic_ips = ec2_conn.get_all_addresses()


    if DEBUG_MODE == True:

        for i in security_groups:
            print "Security Group Info [%s]" % security_groups.index(i)
            print "Name: %s" % i.name
            print "Group ID: %s" % i.id
            print "VPC: %s" % i.vpc_id
            print "Description: %s" % i.description
            
            print "#################################"
            if len(i.rules) > 0:
                print "Inbound Rules:"
                for j in i.rules:
                    try:
                        print "---------------------------------"
                        if j.ip_protocol == "-1":
                            print "Protocol: %s" % "ALL"
                        else:
                            print "Protocol: %s" % j.ip_protocol
                        
                        if j.from_port == j.to_port:
                            if (j.from_port == None and j.ip_protocol == "-1"):
                                print "Port: %s" % "ALL"
                            else:
                                print "Port: %s" % j.from_port
                        else:
                            print "Ports: %s - %s" % (j.from_port, j.to_port)
                        
                        all_grants = ""
                        for k in j.grants:
                            all_grants += str(k) + ", "
                        print "Destination: %s" % all_grants.rstrip(", ")
                    
                    except IndexError as e:
                        print "Error: %s" % e
                #may require for loop
                #print "Outbound Rules: %"  % i.
            else:
                print "Inbound Rules:\nNo rules..."
            print "---------------------------------"
            if len(i.rules_egress) > 0:
                print "Outbound Rules:"
                for j in i.rules_egress:
                    try:
                        print "---------------------------------"
                        if j.ip_protocol == "-1":
                            print "Protocol: %s" % "ALL"
                        else:
                            print "Protocol: %s" % j.ip_protocol
                        
                        if j.from_port == j.to_port:
                            if (j.from_port == None and j.ip_protocol == "-1"):
                                print "Port: %s" % "ALL"
                            else:
                                print "Port: %s" % j.from_port
                        else:
                            print "Ports: %s - %s" % (j.from_port, j.to_port)
                        
                        all_grants = ""
                        for k in j.grants:
                            all_grants += str(k) + ", "
                        print "Destination: %s" % all_grants.rstrip(", ")
                    
                    except IndexError as e:
                        print "Error: %s" % e
                #may require for loop
                #print "Outbound Rules: %"  % i.
            else:
                print "Outbound Rules:\nNo rules..."
                print "---------------------------------"
            print "#################################"
            raw_input()
        raw_input()

    inst = []

    for j in reservations:
        inst.append(j.instances)


    aws_info["instances"] = inst
    aws_info["security_groups"] = security_groups
    aws_info["vpcs"] = vpcs
    aws_info["network_acls"] = network_acls
    aws_info["route_tables"] = route_tables
    aws_info["subnets"] = subnets
    aws_info["elastic_ips"] = elastic_ips

    output_info.aws_info_global = aws_info #Allow access to all information from anywher




    return aws_info
    










####################################### CALLS FOR DIFFERENT ITEMS

#Instances:
# Already implemented
#
#
#Security Groups: 
#security_group[x].name
#security_group[x].id
#security_group[x].description
#security_group[x].rules (is an element/list)
#---->  rules[x].ip_protocol
#---->  rules[x].from_port
#---->  rules[x].to_port
#---->  rules[x].all_grants (is a list)
#security_group[x].rules_egress
#
#
#VPCS:     
#id: The unique ID of the VPC.
#cidr_block: The CIDR block for the VPC.
#
#
#
#Subnets:   
#
#
#
#Route Tables:    
#
#
#
#Elastic IPs:    
# ip_address = ec2_conn.get_all_addresses()
# ip_address[x].public_ip    returns    public elastic IP
# ip_address[x].network_interface_id    returns    elastic IP id
#
#
#Network ACLs:
#
#
#



def startExport(export_info, args):
    for i in export_info:
        print "Starting worksheet export for "+i
        insertCell(2, 2, i, export_info[i], output_info.spreadsheet_id, output_info.worksheet_ids[i][1])

    return #maybe something

instances_information = {"instances": ["Name", "Instance ID", "Interface", "Private IP", "Public IP", "Termination Protection", "Key Pair Name", "Instance Type", "Block Devices"],
                        "security_groups": ["Name", "Group ID", "Description", "Inbound Rules", "Outbound Rules"],
                        "vpcs": ["VPC ID", "CIDR", "Main Route Table"],
                        "subnets": ["Subnet ID", "VPC ID", "CIDR", "Availability Zone", "Route Table", "Network ACL"],
                        "route_tables": ["Route Table ID", "Primary?", "VPC"],
                        "elastic_ips": ["Address", "Interface ID"],
                        "network_acls": ["Network ACL ID", "VPC"]}

def insertCell(start_row, start_col, inputValue_key, inputValue_value, key, wksht_id):
    disable_output = [1, 1, 1, 1, 1, 1, 1]


    entry = spr_client.UpdateCell(1, 1, output_info.worksheet_ids[inputValue_key][0], key, wksht_id)
    counter = 0
    entry = spr_client.UpdateCell(start_row, start_col, "Spreadsheet Generated by aws2spreadsheet on "+time.strftime("%Y-%m-%dT%H:%M:%S"), key, wksht_id)
    start_row += 1
    start_col += 1
    j = 0

    set_headers = False
    no_data = "No Data"
    output = ""
    output_col = 0
    while j < len(inputValue_value):
        i = inputValue_value[j]
        #print "Counter: " + str(counter)
        #print "i: " + str(i)
        #raw_input()
        try:    
            if inputValue_key == "instances" and disable_output[0]:
                i = i[0]
                if set_headers == False:
                    for columns in instances_information[inputValue_key]:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index(columns), columns, key, wksht_id)
                    set_headers = True
                    counter += 1
                if set_headers == True:
                    if i.tags["Name"] != None:
                        output_col = instances_information[inputValue_key].index("Name")
                        output = i.tags["Name"]
                    else:
                        output_col = instances_information[inputValue_key].index("Name")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.id != None:
                        output_col = instances_information[inputValue_key].index("Instance ID")
                        output = i.id
                    else:
                        output_col = instances_information[inputValue_key].index("Instance ID")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if (i.interfaces != None) and (i.interfaces != []):
                        interface = ""
                        for inter in i.interfaces:
                            interface += str(inter.id) + ", "
                        
                        output_col = instances_information[inputValue_key].index("Interface")
                        output = interface.rstrip(", ")
                    else:
                        output_col = instances_information[inputValue_key].index("Interface")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.private_ip_address != None:
                        output_col = instances_information[inputValue_key].index("Private IP")
                        output = i.private_ip_address
                    else:
                        output_col = instances_information[inputValue_key].index("Private IP")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.ip_address != None:
                        output_col = instances_information[inputValue_key].index("Public IP")
                        output = i.ip_address
                    else:
                        output_col = instances_information[inputValue_key].index("Public IP")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.get_attribute("disableApiTermination")["disableApiTermination"] != None:
                        output_col = instances_information[inputValue_key].index("Termination Protection")
                        output = str(i.get_attribute("disableApiTermination")["disableApiTermination"])
                    else:
                        output_col = instances_information[inputValue_key].index("Termination Protection")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.key_name != None:
                        output_col = instances_information[inputValue_key].index("Key Pair Name")
                        output = i.key_name
                    else:
                        output_col = instances_information[inputValue_key].index("Key Pair Name")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.instance_type != None:
                        output_col = instances_information[inputValue_key].index("Instance Type")
                        output = i.instance_type
                    else:
                        output_col = instances_information[inputValue_key].index("Instance Type")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.block_device_mapping != None:
                        block_devices = ""
                        for b in i.block_device_mapping:
                            block_devices += str(b) + ", "

                        output_col = instances_information[inputValue_key].index("Block Devices")
                        output = block_devices.rstrip(", ")
                    else:
                        output_col = instances_information[inputValue_key].index("Block Devices")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


            if inputValue_key == "security_groups" and disable_output[1]:
                if set_headers == False:
                    for columns in instances_information[inputValue_key]:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index(columns), columns, key, wksht_id)
                    set_headers = True
                    counter += 1
                if set_headers == True:
                    if i.name != None:    # Print Security Group Name
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Name"), i.name, key, wksht_id)
                    else:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Name"), "No Value", key, wksht_id)


                    if i.id != None:    #Print Security Group ID
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Group ID"), i.id, key, wksht_id)
                    else:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Group ID"), "No Value", key, wksht_id)


                    if i.description != None:    #Print Security Group Description
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Description"), i.description, key, wksht_id)
                    else:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Description"), "No Value", key, wksht_id)


                    if len(i.rules) > 0:    #Print Security Group Inbound Rules
                        in_rules = ""
                        in_protocol = {}
                        in_port = ""
                        in_all_grants = ""
                        for r in i.rules:
                            
                            if r.ip_protocol.upper() not in in_protocol:
                                if r.ip_protocol.upper() == "-1":
                                    in_protocol[r.ip_protocol.upper()] = "ALL" + "\n"
                                else:
                                    in_protocol[r.ip_protocol.upper()] = r.ip_protocol.upper() + "\n"
                            
                            
                            if r.from_port == r.to_port:
                                if r.from_port == None:
                                    in_protocol[r.ip_protocol.upper()] += "ALL "
                                else:
                                    in_protocol[r.ip_protocol.upper()] += r.from_port + " "
                            else:
                                in_protocol[r.ip_protocol.upper()] += r.from_port + "-" + r.to_port + " "
                            
                            for gr in r.grants:
                                in_protocol[r.ip_protocol.upper()] += str(gr) + ", "

                            in_protocol[r.ip_protocol.upper()] = in_protocol[r.ip_protocol.upper()].rstrip(", \n") + "\n"
                            
                            
                        for i_in_protocol in in_protocol:
                            in_rules += in_protocol[i_in_protocol].rstrip(", ") + "\n"

                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Inbound Rules"), in_rules.rstrip("\n"), key, wksht_id)
                    
                    else:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Inbound Rules"), "No Value", key, wksht_id)




                    if len(i.rules_egress) > 0:    #Print Security Group Outbound Rules
                        out_rules = ""
                        out_protocol = {}
                        out_port = ""
                        out_all_grants = ""
                        for r in i.rules_egress:

                            if r.ip_protocol.upper() not in out_protocol:
                                if r.ip_protocol.upper() == "-1":
                                    out_protocol[r.ip_protocol.upper()] = "ALL" + "\n"
                                else:
                                    out_protocol[r.ip_protocol.upper()] = r.ip_protocol.upper() + "\n"
                                

                            if r.from_port == r.to_port:
                                if r.from_port == None:
                                    out_protocol[r.ip_protocol.upper()] += "ALL "
                                else:
                                    out_protocol[r.ip_protocol.upper()] += r.from_port + " "
                            else:
                                out_protocol[r.ip_protocol.upper()] += r.from_port + "-" + r.to_port + " "
                            
                            for gr in r.grants:
                                out_protocol[r.ip_protocol.upper()] += str(gr) + ", "
                                
                            out_protocol[r.ip_protocol.upper()] = out_protocol[r.ip_protocol.upper()].rstrip(", \n") + "\n"
                            
                            
                        for i_out_protocol in out_protocol:
                            out_rules += out_protocol[i_out_protocol].rstrip(", ") + "\n"

                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Outbound Rules"), out_rules.rstrip("\n"), key, wksht_id)
                    
                    else:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index("Outbound Rules"), "No Value", key, wksht_id)


            if inputValue_key == "vpcs" and disable_output[2]:
                if set_headers == False:
                    for columns in instances_information[inputValue_key]:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index(columns), columns, key, wksht_id)
                    set_headers = True
                    counter += 1
                if set_headers == True:
                    if i.id != None:
                        output_col = instances_information[inputValue_key].index("VPC ID")
                        output = i.id
                    else:
                        output_col = instances_information[inputValue_key].index("VPC ID")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

                    if i.cidr_block != None:
                        output_col = instances_information[inputValue_key].index("CIDR")
                        output = i.cidr_block
                    else:
                        output_col = instances_information[inputValue_key].index("CIDR")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

                    if output_info.aws_info_global["route_tables"] != []:
                        for rt in output_info.aws_info_global["route_tables"]:
                            if rt.associations[0].main and (rt.vpc_id == i.id):
                                output = rt.id
                                break
                            else:
                                output = no_data

                        output_col = instances_information[inputValue_key].index("Main Route Table")
                    else:
                        output_col = instances_information[inputValue_key].index("Main Route Table")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


            if inputValue_key == "subnets" and disable_output[3]:
                if set_headers == False:
                    for columns in instances_information[inputValue_key]:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index(columns), columns, key, wksht_id)
                    set_headers = True
                    counter += 1
                if set_headers == True:
                    if i.id != None:    #Print Subnet ID
                        output_col = instances_information[inputValue_key].index("Subnet ID")
                        output = i.id
                    else:
                        output_col = instances_information[inputValue_key].index("Subnet ID")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if i.vpc_id != None:    #Print VPC ID
                        output_col = instances_information[inputValue_key].index("VPC ID")
                        output = i.vpc_id
                    else:
                        output_col = instances_information[inputValue_key].index("VPC ID")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

                    if i.cidr_block != None:    #Print CIDR Block
                        output_col = instances_information[inputValue_key].index("CIDR")
                        output = i.cidr_block
                    else:
                        output_col = instances_information[inputValue_key].index("CIDR")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

                    if i.availability_zone != None:    #Print Availability Zone
                        output_col = instances_information[inputValue_key].index("Availability Zone")
                        output = i.availability_zone
                    else:
                        output_col = instances_information[inputValue_key].index("Availability Zone")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if output_info.aws_info_global["route_tables"] != []:    #Print Route Table Associations

                        subnet_route_table = output_info.aws_info_global["route_tables"]

                        ass_rts = []

                        for rt in subnet_route_table:
                            for ass in rt.associations:
                                if i.id == ass.subnet_id:
                                    ass_rts.append(ass.route_table_id)

                        output_col = instances_information[inputValue_key].index("Route Table")
                       

                        if ass_rts == []:
                            if output_info.aws_info_global["route_tables"] != []:
                                for rt in output_info.aws_info_global["route_tables"]:
                                    if (len(rt.associations) == 1) and (rt.associations[0].subnet_id == None) and (i.vpc_id==rt.vpc_id):
                                        print "subnet id: "+str(i.id)+" "+"rt id: "+str(rt.id)
                                        output = rt.id
                                        break
                                    else:
                                        output = no_data
                        else:
                            output = ", ".join(str(joined) for joined in ass_rts)
                    else:
                        output_col = instances_information[inputValue_key].index("Route Table")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


                    if output_info.aws_info_global["network_acls"] != []:    #Print Network ACL Associations

                        subnet_acl = output_info.aws_info_global["network_acls"]

                        ass_acls = []

                        for acl in subnet_acl:
                            for ass in acl.associations:
                                if i.id == ass.subnet_id:
                                    ass_acls.append(ass.route_table_id)


                        output_col = instances_information[inputValue_key].index("Network ACL")
                        
                        if ass_acls == []: output = no_data
                        else: output = ", ".join(str(joined) for joined in ass_acls)
                    else:
                        output_col = instances_information[inputValue_key].index("Network ACL")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


            if inputValue_key == "route_tables" and disable_output[4]:
                if set_headers == False:
                    for columns in instances_information[inputValue_key]:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index(columns), columns, key, wksht_id)
                    set_headers = True
                    counter += 1
                if set_headers == True:
                    if i.id != None:
                        output_col = instances_information[inputValue_key].index("Route Table ID")
                        output = i.id
                    else:
                        output_col = instances_information[inputValue_key].index("Route Table ID")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

                    if i.associations > 0:
                        for rt in i.associations:
                            if rt.main:
                                output = str(True)
                                break
                            else:
                                output = str(False)
                        output_col = instances_information[inputValue_key].index("Primary?")
                    else:
                        output_col = instances_information[inputValue_key].index("Primary?")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

                    if i.vpc_id != None:
                        output_col = instances_information[inputValue_key].index("VPC")
                        output = i.vpc_id
                    else:
                        output_col = instances_information[inputValue_key].index("VPC")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


            if inputValue_key == "elastic_ips" and disable_output[5]:
                if set_headers == False:
                    for columns in instances_information[inputValue_key]:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index(columns), columns, key, wksht_id)
                    set_headers = True
                    counter += 1
                if set_headers == True:
                    if i.public_ip != None:
                        output_col = instances_information[inputValue_key].index("Address")
                        output = i.public_ip
                    else:
                        output_col = instances_information[inputValue_key].index("Address")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

                    if i.network_interface_id != None:
                        output_col = instances_information[inputValue_key].index("Interface ID")
                        output = i.network_interface_id
                    else:
                        output_col = instances_information[inputValue_key].index("Interface ID")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)


            if inputValue_key == "network_acls" and disable_output[6]:
                if set_headers == False:
                    for columns in instances_information[inputValue_key]:
                        entry = spr_client.UpdateCell(start_row+counter, start_col+instances_information[inputValue_key].index(columns), columns, key, wksht_id)
                    set_headers = True
                    counter += 1
                if set_headers == True:
                    if i.id != None:
                        output_col = instances_information[inputValue_key].index("Network ACL ID")
                        output = i.id
                    else:
                        output_col = instances_information[inputValue_key].index("Network ACL ID")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)
                    if i.vpc_id != None:
                        output_col = instances_information[inputValue_key].index("VPC")
                        output = i.vpc_id
                    else:
                        output_col = instances_information[inputValue_key].index("VPC")
                        output = no_data
                    entry = spr_client.UpdateCell(start_row+counter, start_col+output_col, output, key, wksht_id)

            
            j += 1
            counter += 1








        except gdata.service.RequestError as e:
            parsed_error = fixJSON(str(e))
            print parsed_error["reason"]
            if parsed_error["reason"] == "Bad Request":
                print "BAD REQUEST!!!!"
                print "MUST ADD CELLS!"
                #entry = spr_client.InsertRow({'col1': 'abc', 'col2':'mytest'}, key, wksht_id)  #Does not function as expected...



    print "Done updating cells.\nSuccessfully updated %i cells. Disclaimer: May not have updated the listed amount of cells..." % (counter) + "\n"


def parseConfig():
    global DEFAULT_CONFIG

    spr_search = FindSPR_IDS()    # PUT THIS IN A CONFIG PARSER TO DETERMINE EXTRA INFO


    config = ConfigParser.RawConfigParser()
    config.read(DEFAULT_CONFIG)

    spreadsheet_name = config.get("Defaults", "spreadsheet_name").split("#")[0].strip()
    spreadsheet_key = config.get("Defaults", "spreadsheet_key").split("#")[0].strip()
    worksheet_list = config.items("Worksheets")
    worksheet_dict = {}

    for dic in worksheet_list:
        worksheet_dict[dic[0]] = [dic[1].split(",")[0].strip(), dic[1].split("#")[0].split(",")[1].strip()]

    
    if len(spreadsheet_key) == 0:
        print "No key provided! Searching for key..."
        spr_search.getSpreadsheets(spreadsheet_name)
        if spr_search.curr_key != None:
            print "Key found: "+spr_search.curr_key
            print "Saving key to config..."
            config.set("Defaults", "spreadsheet_key", spr_search.curr_key + "    " + config.get("Defaults", "spreadsheet_key"))
            with open(DEFAULT_CONFIG, "wb") as configfile:
                config.write(configfile)
        else:
            print "No key was found..."
    else:
        spr_search.curr_key = spreadsheet_key
        print "Key was provided! Key: " + spreadsheet_key


    for i in worksheet_dict:

        if len(worksheet_dict[i][1]) == 0:
            spr_search.getWorksheets(worksheet_dict[i][0])     
            worksheet_dict[i][1] = spr_search.curr_wksht_ids[worksheet_dict[i][0]]
            comments = ""
            for c in config.get("Worksheets", i).split("#")[1:]:
                comments += "#"+c
            config.set("Worksheets", i, worksheet_dict[i][0] + ", " + worksheet_dict[i][1] + "    " + comments )
            with open(DEFAULT_CONFIG, "wb") as configfile:
                config.write(configfile)

    output_info.spreadsheet_id = spr_search.curr_key
    output_info.worksheet_ids = worksheet_dict
    
    return #config list or whatever

def parseArgs():    # ADD KEY PAIR ARG VAR

    parser = argparse.ArgumentParser(description="Extract data from AWS and save to Google Spreadsheet")
    parser.add_argument("-d", "--debug", help="Enable debug (verbose) mode")   # FIX THIS IT DOESN"T WORK AT ALL

    

    args_ = parser.parse_args()

    return vars(args_)



if __name__ == "__main__":
    output_info = OutputInfo()
    args = parseArgs()
    config = parseConfig()
    info = getAWSInfo()
    startExport(info, args)
