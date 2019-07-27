#######################################
# SkySat Mission Ops Coding Challenge #
#         Yasamin Houshmand			  #
########################################################################################################################
# This application takes a NOAA GOES Proton Flux text file (ftp://ftp.swpc.noaa.gov/pub/lists/particle/), converts the #
# data to a pandas dataframe, iterates through the rows of the dataframe one-by-one, checking for values in the P>10,  #
# P>30, P>50, and P>100 columns to see if the flux level has gone above the predetermined thresholds. If it has, it    #
# will trigger a Warning (flux > 1), Alert (flux>10), or Critical (flux>100) email and make a POST request to an API.  #
# Additionally, if the flux level has returned to below 1 (flux<1) for at least 90 minutes, it will trigger an Info    #
# email and make a POST request to the API. With each email it attaches an up-to-date plot with the information up     #
# until that point in time.                                                											   #
#																													   #
# Few things to note:                                                                                                  #
# 1) There is an "installLibs.sh" file that comes with this program - it should be used to install necessary libraries #
#																													   #
# 2) If the flux level is consistently above a certain threshold, it will send emails/make POST requests repeatedly.   #
#     This is by design, since the idea is that each new entry will be a new update from the weather satellite		   #
#																													   #
# 3) The email is configurable, so the details will need to be added in the 'tools.py' file, under the "sendEmail"     #
#     method. The "To", "From", "password", and server "smtplib.SMTP(<server>, <port>)" details would change           #
#     Additionally, I created 'skysatops06@gmail.com' just for testing purposes - please feel free to use it! :)       #
#																													   #
# 4) Similarly, the API Post URL is configurable, but will need to be changed in the 'tools.py' file                   #
#																													   #
# 5) The text input can be designed in many ways - as of now I have set it to take input via the cmd line in the form  #
#     of a human written text, however the line below it in the comments is there incase a script would be run. Once   #
#     replaced with the "input" line, the bash/cmd line entries should be as follows: 				                   #
#     python3 mainApp.py <NOAA GOES Proton Flux filename>															   #
#                                                                                                                      #
#           Thank you for this opportunity and I hope the app works well on your ubuntu system! :)                     #
########################################################################################################################

import sys
import datetime
from tools import getPlot, fileToDataframe, fluxCriticality, postAPI, sendEmail

# Begin a timer to check how long it takes to run the program
start = datetime.datetime.now()
print('Start time is ' + str(start) + '\n')


# NOTE: This can be hard coded, but since a file would be passed in I thought it would be easier to test by giving an
# input text file (ex: test1.txt) instead of changing the line of code
protonFluxFile = input("NOTE: The file must be in the same folder as the  'mainApp.py' and 'tools.py' folder! \nPlease "
                       "enter the NOAA GOES Proton Flux text file: \n")

# Alternative way to make automation easier - can take input from command line/bash
# To use this, add a # in front of "protonFluxFile = input(...." above and then uncomment part below
# protonFluxFile = sys.argv[1]


# Checking for text file
while protonFluxFile[-4:] != '.txt':
    print("\nERROR: The file must be a text (.txt) file!")
    protonFluxFile = input("NOTE: The file must be in the same folder as the  'mainApp.py' and 'tools.py' folder! \n"
                           "Please enter the NOAA GOES Proton Flux text file: \n")

# Convert the text file to a dataframe - Note: must be in same folder as program
dataFrame = fileToDataframe(protonFluxFile)

# Used for INFO email/API call, default value is -1
P10_event = -1
P30_event = -1
P50_event = -1
P100_event = -1


# Check the different proton flux ranges by iterating through dataframe, row-by-row
for n in dataFrame.index:
    row_index = dataFrame['P>10'].index.values[n]

    # Flux at different P-values for current row
    val1 = dataFrame.at[row_index, 'P>10']
    val2 = dataFrame.at[row_index, 'P>30']
    val3 = dataFrame.at[row_index, 'P>50']
    val4 = dataFrame.at[row_index, 'P>100']

    # For the case that we are checking the first row
    if row_index == dataFrame.index[0]:
        plot_index = row_index + 2
    else:
        plot_index = row_index + 1

    # Compare flux to threshold criteria, if above triggers a plot (getPlot), an email and API call (fluxCriticality)
    # and set the P**_event marker to count up to 90mins before triggering INFO email
    if val1 > 1.0:  # P>10
        P10_event = row_index
        plotFilename = getPlot(dataFrame.iloc[:plot_index, :])
        fluxCriticality(val1, 'P>10', plotFilename)
    if val2 > 1.0:  # P>30
        P30_event = row_index
        plotFilename = getPlot(dataFrame.iloc[:plot_index, :])
        fluxCriticality(val2, 'P>30', plotFilename)
    if val3 > 1.0:  # P>50
        P50_event = row_index
        plotFilename = getPlot(dataFrame.iloc[:plot_index, :])
        fluxCriticality(val3, 'P>50', plotFilename)
    if val4 > 1.0:  # P>100
        P100_event = row_index
        plotFilename = getPlot(dataFrame.iloc[:plot_index, :])
        fluxCriticality(val4, 'P>100', plotFilename)

    # INFO Email Criteria check
    if (P10_event+18) == n and P10_event != -1:
        plotFilename = getPlot(dataFrame.iloc[:row_index, :])
        sendEmail('[INFO]', dataFrame.iloc[row_index, 6], 'P>10', plotFilename)
        postAPI('[INFO]', dataFrame.iloc[row_index, 6])
        P10_event = -1

    if (P30_event+18) == row_index and P30_event != -1:
        plotFilename = getPlot(dataFrame.iloc[:row_index, :])
        sendEmail('[INFO]', dataFrame.iloc[row_index, 7], 'P>30', plotFilename)
        postAPI('[INFO]', dataFrame.iloc[row_index, 7])
        P30_event = -1

    if (P50_event+18) == row_index and P50_event != -1:
        plotFilename = getPlot(dataFrame.iloc[:row_index, :])
        sendEmail('[INFO]', dataFrame.iloc[row_index, 8], 'P>50', plotFilename)
        postAPI('[INFO]', dataFrame.iloc[row_index, 8])
        P50_event = -1

    if (P100_event+18) == row_index and P100_event != -1:
        plotFilename = getPlot(dataFrame.iloc[:row_index, :])
        sendEmail('[INFO]', dataFrame.iloc[row_index, 9], 'P>100', plotFilename)
        postAPI('[INFO]', dataFrame.iloc[row_index, 9])
        P100_event = -1


finish = datetime.datetime.now()
print("The program took " + str(finish-start) + " to complete")
