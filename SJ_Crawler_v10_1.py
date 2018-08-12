from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import datetime
from time import sleep
import csv
import json
import os

DepartLocations = ['Stockholm Central']
ArriveLocations = ['Oslo S', 'Oslo Bussterminal']
homepage = "https://www.sj.se/en/home.html#/"

class Crawler():
    
    def __init__(self, homepage):
        print("Initiating Scraper...", end='')
        self.homepage = homepage
        self.RequestCounter = 0
        self.PointerResultFromTo = "Home Page"
        self.SurveyRemoved = False

        #Chrome driver Options
        self.chromeOptions = webdriver.ChromeOptions()
        self.chromeOptions.add_experimental_option("prefs", {"profile.managed_default_content_settings.images":2, 'disk-cache-size': 4096})
        self.chromeOptions.add_argument('--disable-logging')
        self.chromeOptions.add_argument("--incognito")
        self.chromeOptions.add_argument("--headless")
        self.chromeOptions.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(chrome_options=self.chromeOptions)
        self.driver.implicitly_wait(2)
        self.initial = True
        self.driver.get(self.homepage)
        self.driver.maximize_window()

        self.inputfromto()

        print("Done")
        if self.SurveyRemoved == False:
            self.get_rid_of_survey()



    #Input dummy from and to destinations and deal with unpredictable survey appearance
    def inputfromto(self):
        z = False
        counter = 0
        while z == False:
            try:
                self.driver.find_element_by_id("booking-departure").send_keys("Depart")
                self.driver.find_element_by_id("booking-arrival").send_keys("Arrive")
                z = True
            except:
                counter += 1
                print("Error finding element for departure and arrival")
                if counter > 5:
                    self.driver.get(self.homepage)
                    self.get_rid_of_survey()
                else:
                    self.get_rid_of_survey()
        del z
        
        
    def get_rid_of_survey(self):
        #Close Survey if exists
        try:
            print("...Removing Survey...", end='')
            sleep(2)
            self.driver.switch_to_default_content()
            survey = self.driver.find_element_by_css_selector('div.usabilla__overlay iframe')
            self.driver.switch_to_frame(survey)

            cancel_button = self.driver.find_element_by_xpath("//a[@id='close_link']")
            cancel_button.send_keys(Keys.RETURN)

            self.driver.switch_to_default_content()
            del survey
            self.SurveyRemoved = True
            print("Done")

        except:
            print("Error Survey Close")
            self.driver.switch_to_default_content() 


    def getroutewithdate(self, departure, arrival, dateinput):

        #Check if driver instance needs to be restarted
        if self.RequestCounter > 10:
            print("Restarting driver...", end='')
            self.driver.quit()
            delattr(self, 'driver')
            self.driver = webdriver.Chrome(chrome_options=self.chromeOptions)
            self.driver.implicitly_wait(2)
            self.initial = True
            self.driver.get(self.homepage)
            self.driver.maximize_window()
            self.inputfromto()

            print("Done", end='')
            if self.SurveyRemoved == False:
                self.get_rid_of_survey()
            
            self.RequestCounter = 0

        self.driver.application_cache.status.clear()
        self.success = False
        self.rows = None
        self.departure = departure
        self.arrival = arrival
        self.searchdate = dateinput
        self.querydate = datetime.datetime.now()
        self.disturbance_msg_appeared = False
        self.RequestCounter += 1
    
        Currenturl = self.driver.current_url.split("/")
        
        if self.initial == True:
            assert Currenturl[6] == "Depart"
            assert Currenturl[7] == "Arrive"
            assert Currenturl[8] == "enkel"
        
        Currenturl[10] = datetime.datetime.strftime(dateinput, "%Y%m%d-%H%M")
        Currenturl[12] = datetime.datetime.strftime(dateinput, "%Y%m%d-%H%M")
        Currenturl[6] = departure.strip().replace(" ", "%2520")
        Currenturl[7] = arrival.strip().replace(" ", "%2520")
        
        Currenturl = "/".join(Currenturl)
        #print(Currenturl)
        self.driver.get(Currenturl)

        def get_rid_of_disturbance_page(self):
            try:
                checkbox = self.driver.find_element_by_class_name("disturbance-explanation-page__checkbox").find_element_by_id("checkbox")
                continue_button = self.driver.find_element_by_class_name("disturbance-explanation-page__continue-button")
                ActionChains(self.driver).move_to_element(checkbox).click().perform()
                ActionChains(self.driver).move_to_element(continue_button).click().perform()
                self.disturbance_msg_appeared = True
            except:
                #print("Remove disturbance page: Error")
                pass

        def remove_tool_tip(self):
            try:
                self.driver.find_element_by_class_name('disturbance-banner-tooltip-tiangle').click()
            except:
                #print("Remove tool tip: Error")
                pass
        
        
        if self.initial == True:
            
            #click submit after search only once for initial run
            sleep(2)
            self.initial = False
            submit_button = self.driver.find_element_by_xpath("//button[@ng-click='continueToTimetable(this.booking_form_main)']")
            ActionChains(self.driver).move_to_element(submit_button).perform()
            submit_button.click()

            del submit_button
        
        del Currenturl

        #Remove disturbance msg
        if self.disturbance_msg_appeared == False:
            sleep(4)
            get_rid_of_disturbance_page(self)
        else:
            sleep(2)
        
        remove_tool_tip(self)
        

        #Expand all available time for the day
        def expand_page_down(self):
            doexpanding = True
            while doexpanding == True:
                try:
                    expandbutton = self.driver.find_element_by_xpath("//a[@ng-click='getNextTimetableView()']")
                    ActionChains(self.driver).move_to_element(expandbutton).perform()
                    expandbutton.click()
                    sleep(1)
                except:
                    doexpanding = False
            del doexpanding

        expand_page_down(self)
        
        #Expand All Items
        sleep(1)
        Rows = self.driver.find_elements_by_xpath("//div[@sj-timetable-row='timetableRow']")
        
        for row in Rows:
            if "The departure time has passed" not in row.text:
                ActionChains(self.driver).move_to_element(row).perform()
                row.click()
                sleep(1)
        del Rows
        
        self.rows = self.driver.find_elements_by_xpath("//div[@sj-timetable-row='timetableRow']")
        self.rows = [x.text.split("\n") for x in self.rows]
        
        def ProcessRows(self, rows):
            All_items = []
            
            for x in rows:
                #print(">>>>>>>>>>>>>>", str(x), "<<<<<<<<<<<")
                if len(x) > 2:
                    #print(x)
                    #Initiate variables
                    row_dict = {}
                    split = x[0].split(" ")

                    #Prepare Header
                    row_dict['Departure time'] = split[0]
                    row_dict['Arrival time'] = split[2]
                    row_dict['Duration'] = split[5]
                    row_dict['Changes'] = int(split[7])
                    row_dict['Journey'] = {}

                    #Fix issue of variable items within html such as notifications about 2d call only which might not appear in some cases
                    for k, v in enumerate(x):
                        if "Arrival" in x[k] and "Travel time" in x[k-1]:
                            x.insert(k, "")
                        elif "Travel time" in x[k-1] and x[k] == row_dict['Arrival time']:
                             x.insert(k, "")

                    #Fix pricing possible structure discrepacies
                    for k, v in enumerate(x):
                        if 'Not available' in x[k] and 'Not available' in x[k-1]:
                            x.insert(k, "")

                    #process items so that each change/leg is structured into separate item
                    for y in range(0, row_dict['Changes']):
                        row_dict['Journey'][y] = []
                        for z in range(0, 7):
                            #print(x, z+(y*7)+2)
                            row_dict['Journey'][y].append(x[z+(y*7)+2])

                    row_dict['Journey'][row_dict['Changes']] = []
                    lines = 5
                    for z in range(0, lines):
                            row_dict['Journey'][row_dict['Changes']].append(x[z+(row_dict['Changes']*7)+2])

                    lines2 = 2
                    row_dict['Journey'][row_dict['Changes']+1] = []
                    for z in range(0, lines2):
                            row_dict['Journey'][row_dict['Changes']+1].append(x[z+lines+(row_dict['Changes']*7)+2])        

                    #Get prices
                    prices = dict()
                    for k in range(0, len(x)):
                        #print("---------->>", x[k], x[k-1], "<<---------------------")
                        if (x[k] == '1st class*' or x[k] == '1st class') and (x[k-1] ==  '2nd class*' or x[k-1] == '2nd class'):
                            prices[x[k]] = {x[k+4]:x[k+3].replace(":-", "")}
                            prices[x[k-1]] = {x[k+2]:x[k+1].replace(":-", "")}

                            prices[x[k]][x[k+4+4]] = x[k+3+4].replace(":-", "")
                            prices[x[k-1]][x[k+2+4]] = x[k+1+4].replace(":-", "")

                            prices[x[k]][x[k+4+4+4]] = x[k+3+4+4].replace(":-", "")
                            prices[x[k-1]][x[k+2+4+4]] = x[k+1+4+4].replace(":-", "")
                            #print(x[k], x[k-1], "success")
                            break
                        elif (x[k] == 'Berth in couchette/sleeping car*' or x[k] == 'Berth in couchette/sleeping car') and (x[k-1] ==  '2nd class*' or x[k-1] == '2nd class'):
                            prices['1st class*'] = {}
                            prices['1st class*']['Non-rebookable*']= x[k+3].replace(":-", "").replace("fr. ", "")
                            prices[x[k-1]] = {x[k+2]:x[k+1].replace(":-", "")}

                            prices['1st class*']['Rebookable*'] = "Not available"
                            if "Rebookable" in x[k+2+4]:
                                prices[x[k-1]][x[k+2+4]] = x[k+1+4].replace(":-", "")
                            elif "Rebookable" in x[k+2+4-1]:
                                prices[x[k-1]][x[k+2+4-1]] = x[k+1+4-1].replace(":-", "")

                            prices['1st class*']['Refundable*'] = "Not available"
                            if "Refundable" in x[k+8]:
                                prices[x[k-1]][x[k+8]] = x[k+7].replace(":-", "")
                            elif "Refundable" in x[k+8-1]:
                                prices[x[k-1]][x[k+8-1]] = x[k+7-1].replace(":-", "")
                                
                            #print("Prices: ----", prices.items())
                            #print(x[k], x[k-1], "success")
                            break
                            
                            
                    row_dict['Prices'] = prices

                    All_items.append(row_dict)

                    del row_dict, prices, lines, lines2, split
            return All_items
        
        if len(self.rows) > 0:
            self.rows = ProcessRows(self, self.rows)
            self.success = True
        else:
            pass
            #Success FALSE
            
            
        
    def writetofile(self, outputfile):
        
        try:
            if self.success == True:
                outputlist = []
                header = ["Departure time", "Arrival time", "Duration", "Changes", "Journey", "1st class* Non-rebookable",
                          "1st class* Rebookable", "1st class* Refundable", "2nd class* Non-rebookable",
                          "2nd class* Rebookable", "2nd class* Refundable", "Best price"]
                
                for x in self.rows:
                    min_price = []
                    all_prices = []
                    
                    if '1st class*' in x["Prices"].keys():
                        class1 = '1st class*'
                    else:
                        class1 = '1st class'

                    if '2nd class*' in x["Prices"].keys():
                        class2 = '2nd class*'
                    else:
                        class2 = '2nd class'
                        
                    all_prices = [list(v.values()) for v in x["Prices"].values()]
                    
                    #print(all_prices)
                    #print(self.rows)
                    
                    for p1 in all_prices:
                        for p2 in p1:
                            min_price.append(p2)
                    
                    min_price = [int(k.replace(".", "").replace(",", "").replace(" ", "").strip()) for k in min_price if k.replace(".", "").replace(",", "").replace(" ", "").strip().isdigit() == True]
                  
                    min_price = min(min_price) if len(min_price)>0 else None
                    
                    
                    
                    outputlist.append([self.querydate, self.searchdate, self.departure, self.arrival, x['Departure time'],
                                      x['Arrival time'], x['Duration'], x['Changes'], json.dumps(x['Journey']),
                                      x["Prices"][class1]['Non-rebookable'] if 'Non-rebookable' in x["Prices"][class1].keys() else x["Prices"][class1]['Non-rebookable*'],
                                      x["Prices"][class1]['Rebookable'] if 'Rebookable' in x["Prices"][class1].keys() else x["Prices"][class1]['Rebookable*'],
                                      x["Prices"][class1]['Refundable'] if 'Refundable' in x["Prices"][class1].keys() else x["Prices"][class1]['Refundable*'],
                                      x["Prices"][class2]['Non-rebookable'] if 'Non-rebookable' in x["Prices"][class2].keys() else x["Prices"][class2]['Non-rebookable*'],
                                      x["Prices"][class2]['Rebookable'] if 'Rebookable' in x["Prices"][class2].keys() else x["Prices"][class2]['Rebookable*'],
                                      x["Prices"][class2]['Refundable'] if 'Refundable' in x["Prices"][class2].keys() else x["Prices"][class2]['Refundable*'],
                                      min_price
                                      ])
                    
                    del all_prices, min_price
                
                for k1 in range(0, len(outputlist)):
                    for k2 in range(2, 8):
                        if outputlist[k1][0 - k2].replace(".", "").replace(",", "").replace(" ", "").strip().isdigit() == True:
                            outputlist[k1][0 - k2] = outputlist[k1][0 - k2].replace(" ", "").strip()
                        elif outputlist[k1][0 - k2].strip() == "Sold out" or outputlist[k1][0 - k2].strip() == "Not available":
                            outputlist[k1][0 - k2] = None

                with open('Load/SJ/' + outputfile, 'a', newline='', encoding="utf-8") as writefile:
                    wr = csv.writer(writefile)
                    wr.writerows(outputlist)
            
            
                #return("Upload Success: ", self.querydate, self.searchdate, self.departure, self.arrival)
                return True
            
            else:
                with open('Load/SJ/' + outputfile, 'a', newline='', encoding="utf-8") as writefile:
                    wr = csv.writer(writefile)
                    print(str([self.querydate, self.searchdate, self.departure, self.arrival, "ERROR at parsing"]))
                    wr.writerow([self.querydate, self.searchdate, self.departure, self.arrival, "ERROR"])

                return True
        except:
            with open('Load/SJ/' + outputfile, 'a', newline='', encoding="utf-8") as writefile:
                    wr = csv.writer(writefile)
                    print(str([self.querydate, self.searchdate, self.departure, self.arrival, "ERROR at writerows"]))
                    wr.writerow([self.querydate, self.searchdate, self.departure, self.arrival, "ERROR"])
            return False


if __name__ == "__main__":
    #stations list
    with open("Settings/SJ/stations.csv", 'r', encoding="utf-8") as readfile:
        rd = csv.reader(readfile)
        stations = list(rd)
        
    station_combinations = []
    exception_combinations = [['Köbenhavn', 'Copenhagen'], ['Copenhagen', 'Köbenhavn']]

    for item in stations:
        for item2 in stations:
            if item[0].split(" ")[0] != item2[0].split(" ")[0] and item[0].split(" ")[0] != 'XXX' and item2[0].split(" ")[0] != 'XXX' and [item[0].split(" ")[0], item2[0].split(" ")[0]] not in exception_combinations:
                station_combinations.append([item[0], item2[0]])
        

    print("Total station combination searches: " + str(len(station_combinations)))
    print(station_combinations)

    searchdate_start = datetime.datetime.now()
    searchdate_start = searchdate_start.replace(hour=0, minute=0, second=0, microsecond=0)
    dayrange = 90
    outputfilename_prev = "SJ_output_1.csv"
    outputfilename = "SJ_output_1.csv"
    stationslice = slice(0, 5)
    startfromday = 0
    error_give_up_limit = 5

    #initiate scraper
    SJ = Crawler(homepage)

    #Continue from stations
    #for k, item in enumerate(station_combinations):
    #    if item[0] == "Stockholm Central" and item[1] == "Köbenhavn Österport":
    #        fromstart = int(k)
    #        break
    def StartFromLastItem(outputfilename):
        try:
            with open("Load/SJ/"+outputfilename, 'r', encoding="utf-8") as stationoutput:
                rd = csv.reader(stationoutput)
                stationoutput_list = list(rd)
                stationoutput_list = [str(x[1]) +"-"+ str(x[2])+"-"+str(x[3]) for x in stationoutput_list]
                checker_for_previous = False
                return stationoutput_list, checker_for_previous
        except:
            checker_for_previous = True
            return [], checker_for_previous

    stationoutput_list,  checker_for_previous = StartFromLastItem(outputfilename_prev)

    def search_and_write(searchdate, fromto, outputfilename):
        try:
            print(str(fromto[0]), str(fromto[1]), str(searchdate), "....", end='')                   
            SJ.getroutewithdate(fromto[0], fromto[1], searchdate)
            write_success = SJ.writetofile(outputfilename)
            if SJ.success == True and write_success == True:
                print("Success. Wrote to file.")
                return True
            elif SJ.success == True and write_success == False:
                print("Failed to transform data for writing and write to a file")
                return False
            elif SJ.success == False and write_success == True:
                print("Failed to parse website data")
                return False
            else:
                print("Failed, something else")
                return False
        except:
            print(str(fromto[0]), str(fromto[1]), str(searchdate), ".... Error: Unable to write data")
            SJ.writetofile(outputfilename)
            return False




    for dayrun in range(startfromday, dayrange):
        searchdate = searchdate_start + datetime.timedelta(days=dayrun)

        for fromto in station_combinations[stationslice]:
            error_counter = 0
            initial = True

            if checker_for_previous == False:

                if searchdate.strftime("%Y-%m-%d %H:%M:%S") +"-"+ fromto[0] + "-"+fromto[1] not in stationoutput_list:

                    checker_for_previous = True
                    del stationoutput_list
                    while initial == True or (error_counter > 0 and error_counter <= error_give_up_limit):
                        print("***********Retrying to fix error********* Attempt: " + str(error_counter)) if initial == False else None
                        initial = False
                        outcome = search_and_write(searchdate, fromto, outputfilename)
                        if outcome == False:
                            error_counter += 1
                        else:
                            error_counter = 0

            else:
                while initial == True or (error_counter > 0 and error_counter <= error_give_up_limit):
                    print("***********Retrying to fix error********* Attempt: " + str(error_counter)) if initial == False else None
                    initial = False
                    outcome = search_and_write(searchdate, fromto, outputfilename)
                    if outcome == False:
                        error_counter += 1
                    else:
                        error_counter = 0
