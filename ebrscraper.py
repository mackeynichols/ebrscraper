#! python3
# ebrscraper.py - functions to scrape Ontario's Environmental Registry

'''
Scrape all 10 notices on page and send to db/spreadsheet
Inputs: date to scrape after (stored in .txt file)

Outputs:
error log (notice ID, error appended to .txt file, date scraped,linebreak),
date last scrape completed (stored in .txt)
'''

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import datetime
import time
import re
from geopy.geocoders import GoogleV3
from bs4 import BeautifulSoup as bs

# Gspread IDs
accountSID = ''
authToken = ''
scope = [r'https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name(r'C:\Users\mackenzien\Documents\MKN\py\ebrscraper\ebrscraper-181b6ad34305.json', scope)
gc = gspread.authorize(credentials)
wks = gc.open("EBR Tracker").sheet1

# External File containing last date scraping was done
lastScrapeFile = open(r"C:\Users\mackenzien\Documents\MKN\py\ebrscraper\lastebrscrape.txt")
lastScrape = datetime.datetime.strptime(lastScrapeFile.read(), '%Y-%m-%d').date()


# Receives a number of newest notices to fetch, and returns them as
# an array from the ebr site
# Also accepts a language to scrape them in
def getNotices(numRecords = "10", language = "en"):
    startPage = "1"

    formData = {
            "isPopulateSearchNoticeForm": "true",
            "shouldReset":"true",
            "erbRegistryNumber": "",
            "textAll":"",
            "textAtLeastOne":"",
            "textExact":"",
            "textWithout":"",
            "title":"",
            "proponentText":"",
            "dateProposalLoaded":"",
            "dateDecisionLoaded":"",
            "actBillInstrument":"",
            "instruments":"",
            "multimedia":"false",
            "lastOrFromTo":"",
            "timePeriod":"3",
            "dateStart":"",
            "dateEnd":"",
            "numberOfRecords": numRecords,
            "sortBy":"20006",
            "sortOrder":"1",
            "lioSearchType":"0",
            "lioMapSelectionXMLString":"",
            "lioText":"",
            "page": startPage,
            "language": language,
            "criteriaId":"",
            "criteriaName":"",
        }

    req = requests.post("https://www.ebr.gov.on.ca/ERS-WEB-External/searchNotice.do", formData)
    content = bs(req.text, "html.parser")
    notices = content.select('table.searchResult')[0].select('tr[valign="top"]')

    return notices


# Inputs: 
#    notices as an array
#    date to scrape notices after
# Outputs:
#    error log (notice ID, error appended to .txt file, date scraped, linebreak)
#    date last scrape completed (stored in .txt) (optional)

def scrapeNotices(notices, dateToScrapeAfter = "2016-11-01"):
    
    for notice in notices:

        # IF notice is more recent than the day before this script was run last...
        if ((datetime.datetime.strptime(notice.select("td.searchResultContent")[4].text.strip(), '%B %d, %Y').date() - lastScrape).days) > 1:


            
            fullNotice = requests.get(r"https://www.ebr.gov.on.ca" + notice.select('a')[0].get('href'))
            href = r"https://www.ebr.gov.on.ca" + notice.select('a')[0].get('href')    
            soup = bs(fullNotice.text, "html.parser")
            
            
            # If notice is for an instrument, start scraping
            if "Instrument" in soup.select('h1#h1_notice')[0].get_text().split():

                # START TIMER
                start_time = time.time()
                print( "Starting Scrape" )

                notice = soup.select('h1#h1_notice')[0].get_text().strip()

                # Try (twice) to associate coordinates with the proponents address
                proponent = soup.select('span.notice-content-sub')[0].get_text(separator = " ").strip().replace("\n"," ").replace("   ", "")
                try:
                    geolocator = GoogleV3()
                    location = geolocator.geocode(proponent + " Ontario, Canada")
                    proplat = location.latitude
                    proplong = location.longitude
                except Exception as exc:
                    try:
                        location = geolocator.geocode(proponent + " Ontario, Canada")
                        proplat = location.latitude
                        proplong = location.longitude
                    except:            
                        proplat = "Cant Find"
                        proplong = "Cant Find"
                        print(exc)
                    
                instrument = soup.select('span.notice-content-sub')[1].get_text(separator = " ").strip().replace("\n"," ").replace("   ", "")
                ebr_id = soup.select('span.notice-content-sub')[2].get_text().strip().replace("\n"," ").replace("   ", "")
                ministry_id = soup.select('span.notice-content-sub')[3].get_text().strip().replace("\n"," ").replace("   ", "")
                ministry = soup.select('span.notice-content-sub')[4].get_text().strip().replace("\n"," ").replace("   ", "")
                dateproploaded = soup.select('span.notice-content-sub')[5].get_text().strip().replace("\n"," ").replace("   ", "")

                if "Decision" in soup.select('h1#h1_notice')[0].get_text().split():
                    datedecloaded = soup.select('span.notice-content-sub')[6].get_text().strip().replace("\n"," ").replace("   ", "")

                kws = soup.select('div[aria-label="Keyword(s):"]')
                for kw in kws:
                    keywords = kw.get_text().strip().replace("\n"," ").replace("   ", "").replace("Keyword(s):", "").strip()

                if "Proposal" in notice:
                    commenthref = soup.select('input')[0]['onclick'].replace("Javascript:openAddCmtWin('", "").replace("');", "").replace("¬", "&amp;not")
                    commentperiod = soup.select('div[aria-label="Comment Period:"]')[0].get_text().replace("Comment Period:", "").strip()

                # Try (twice) to associate coordinates with locations relevant to the instrument
                if "Location(s)" in soup.select('h2.notice-head-b')[1].get_text():
                    try:
                        location = soup.select('div[aria-label="Location(s) Related to this"]')[0].select('div.notice-content')[0]#.get_text().replace("<br>", "").replace("\n", " ").replace("  ","").strip()
                        location = str(location) + " " + str(soup.select('div[aria-label="Location(s) Related to this"]')[0].select('div.notice-content')[1])
                    except:
                        location = soup.select('div[aria-label="Location(s) Related to this Instrument"]')[0].select('div.notice-content')[0]#.get_text().replace("<br>", "").replace("\n", " ").replace("  ","").strip()
                        location = str(location) + " " + str(soup.select('div[aria-label="Location(s) Related to this Instrument"]')[0].select('div.notice-content')[1])
                        
                    location = re.sub( r"\<\/?[\w]+[\s\w\"\-\=\/]*\>", " ", str(location) ).strip().replace("\n"," ").replace("   ", " ").replace("  ", " ").replace("  ", " ").strip()

                    try:
                        loc = geolocator.geocode(str(location) + " Ontario, Canada")
                        loclat = loc.latitude
                        loclong = loc.longitude
                    except Exception as exc:                        
                        loc = geolocator.geocode(location + " Ontario, Canada")
                        try:
                            loclat = loc.latitude
                            loclong = loc.longitude
                        except:
                            loclat = "Cant Find"
                            loclong = "Cant Find"
                            print(exc)
                print( "Scrape Complete" )

                # Add scraped data to googlespreadsheet
                nrow = sum(i != "" for i in wks.col_values(1))
                print("Adding data to row #" + str(nrow+1))

                wks.update_cell(nrow+1, 1, ebr_id)
                wks.update_cell(nrow+1, 2, href)
                wks.update_cell(nrow+1, 3, ministry_id)
                wks.update_cell(nrow+1, 4, proponent)
                wks.update_cell(nrow+1, 5, proplat)
                wks.update_cell(nrow+1, 6, proplong)
                wks.update_cell(nrow+1, 7, instrument)
                wks.update_cell(nrow+1, 8, notice)
                wks.update_cell(nrow+1, 9, dateproploaded)
                if "Decision" in soup.select('h1#h1_notice')[0].get_text().split():     
                    wks.update_cell(nrow+1, 10, datedecloaded)
                wks.update_cell(nrow+1, 11, ministry)
                wks.update_cell(nrow+1, 12, keywords)
                wks.update_cell(nrow+1, 13, proponent)
                wks.update_cell(nrow+1, 14, proplat)
                wks.update_cell(nrow+1, 15, proplong)
                if "Proposal" in notice:
                    wks.update_cell(nrow+1, 16, commenthref)
                    wks.update_cell(nrow+1, 17, commentperiod)
                wks.update_cell(nrow+1, 18, location)
                wks.update_cell(nrow+1, 19, loclat)
                wks.update_cell(nrow+1, 20, loclong)
                    
                
                print( "Storage Complete" )
                print( str(time.time() - start_time) + " seconds")

                
                print("-----------------------------")
    yesterday = str(datetime.date.today() - datetime.timedelta(1))
    lastScrapeFile = open(r"C:\Users\mackenzien\Documents\MKN\py\ebrscraper\lastebrscrape.txt", 'w')
    lastScrapeFile.write(yesterday)
    lastScrapeFile.close()
                
"""
                # PERMIT TO TAKE WATER
                if instrument == 'Permit to Take Water - OWRA s. 34':
                    description = str(soup.select('div[aria-label="Description of"]')[0])
                    print( waterPurpose.search(description).group(1)  )

                # AIR RELATED INSTRUMENT
                #if "Air" in keywords:
                    

                # WASTEWATER RELATED INSTRUMENT
                #if "Wastewater" in keywords:
                    
"""                    




scrapeNotices(getNotices(250))
