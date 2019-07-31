# postAPI library
import requests

# sendEmail libraries
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# fileToDataframe library
import pandas as pd

# getPlot libraries
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
from matplotlib.ticker import AutoMinorLocator  # Used to set minor ticks on graph
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


# This function takes the inputs of an email (subject, to, from, body, attachments, etc)and uses email.mime to simplify
# the data and convert a human-readable input into the proper layout needed to send an email via SMTP network propocal.
# A connection is then created to the email server using smtplib, the user is logged in, and an email is sent.
# Note that the attachement is encoded using base64 since it is a great way to ensure data retention for attachments
# and the "From", "password", "To", and server info "smtplib.SMTP(server, port)" must be configured properly for this to
# work. Visit https://www.youtube.com/watch?v=bXRYJEKjqIM for more details
def sendEmail(level, value, pVal, fluxplot):
    msg = MIMEMultipart()  # Stating that it will use MIMEMultipart layout

    # Configurable Variables
    # Email:
    msg['From'] = "skysatops06@gmail.com"
    password = "!t1e2s3t45"
    msg['To'] = "skysatops06@gmail.com"

    # Adding plot as attachment
    attachment = open(fluxplot, 'rb')  # rb = read bytes, so read file as read bytes

    # Opening a stream to send attachment, sending it, and then closing the stream
    # Uploading file in Base 64
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= "+fluxplot)

    if level != '[INFO]':
        # <Level> = Warning, Alert, or Critical
        msg['Subject'] = str(level) + " Proton Event: Currently at " + str(value) + " MeV (" + str(pVal) + ")"
        body = """\
        <html> 
            <head></head>
            <body>
                <p>There is currently an ongoing Proton Event.<br> 
                   Please refer to attached history graph and the link below for more details.<br><br> 
                    <a href="https://www.swpc.noaa.gov/products/goes-proton-flux">GOES Proton Flux Website</a>
                </p>
            </body>
        </html>
        """
    else:
        # <Level> = INFO
        msg['Subject'] = str(level) + ": Flux <1 for last 90mins (" + str(pVal)+ " - currently at "+str(value)
        body = """\
        <html> 
            <head></head>
            <body>
                <p>Flux has been less than 1 for the last 90 minutes.<br> 
                   Please refer to attached history graph and the link below for more details.<br><br> 
                    <a href="https://www.swpc.noaa.gov/products/goes-proton-flux">GOES Proton Flux Website</a>
                </p>
            </body>
        </html>
        """

    msg.attach(part)
    msg.attach(MIMEText(body, 'html'))  # Attach body to the MIMEText Object
    server = smtplib.SMTP("smtp.gmail.com", 587)  # Dependent on which email server you use
    server.starttls()  # Start secure connection to server
    server.login(msg['From'], password)  # Log into server
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()  # End connection to server
    print("Email is now sent for "+str(value)+" at criticality level "+str(level))


# This method makes an API call with the current level(Warning, Alert, Critical, Info), the MeV value, and the GOES
# Proton Flux NOAA endpoint
# Note: the URL can be configured to be whatever post API address is required
def postAPI(level, value):
    url = 'https://httpbin.org/post'
    data = {'alert_text': "Space weather "+str(level[1:-1])+": > 10 MeV proton flux currently at "+str(value),
            'level': str(level[1:-1]),
            'link': "https://www.swpc.noaa.gov/products/goes-proton-flux"
            }  # Note: level[1:-1] to remove the square brackets
    response = requests.post(url, data=data)

    print("The HTTP response is "+str(response.status_code)+" "+str(response.reason))

    print("The JSON response is: "+str(response.json())+"\n")


# This method is configured for a NOAA text file. It takes the text file's name (input=string), puts it into a Pandas
# dataframe, reformats the data to fix spacing issues in the header, removes unused columns, include a new 'Date'
# column that is of type datetime, and turns the remaining information into integers (ex: Year) or floats (ex: P>10)
# depending on the column name. Once it is done, it return the dataframe
def fileToDataframe(filename):
    if type(filename) != str and filename[-1:-4] != '.txt':
        print("ERROR: This is an invalid file type. Please enter a .txt file")
    else:
        with open(filename, 'r') as file:
            dataSet = file.readlines()
            header = dataSet[24]
            header = header.replace('# ', '')
            header = header.replace(' >', '>')  # Additional spaces in some column header names Ex: P > 10, P >5, P> 20
            header = header.replace('> ', '>')
            proton_data = dataSet[26:]
            proton_data = list(map(lambda s: s.strip(), proton_data))  # removing the /n at the end of the list

        # header is a string - need to be a list so we can input into pandas df
        header = header.split()
        # proton_data is a list of strings, need to convert to floating point numbers if we want to graph
        for x in range(len(proton_data)):
            proton_data[x] = proton_data[x].split()
        data_frame = pd.DataFrame(proton_data, columns=header)
        data_frame = data_frame.drop(columns=['Day', 'Day', 'E>0.8', 'E>2.0', 'E>4.0'])

        # Adding a date-time column
        data_frame['Date'] = data_frame['YR'] + '-' + data_frame['MO'] + '-' + data_frame['DA'] + ' ' + \
                             data_frame['HHMM'].str[:2] + ':' + data_frame['HHMM'].str[2:]
        data_frame['Date'] = pd.to_datetime(data_frame['Date'])

        # Converting columns into the correct data types - imported as string
        data_frame = data_frame.astype({"YR": 'int', "MO": 'int', "DA": 'int', "HHMM": 'int', "P>1": 'float64',
                                        "P>5": 'float64', 'P>10': 'float64', 'P>30': 'float64', 'P>50': 'float64',
                                        'P>100': 'float64'})
        return data_frame


# Receives a portion of a dataframe (up until the current row in the iteration) as the input, and creates a 4-line,
# multicolor plot for data from the P>10, P>30, P>50, and P>100 columns. It plots this data against the Date (datetime)
# entry to create the resulting 'GOES Proton Flux Data' graph. Depending on the number of rows (defined by time) in the
# dataframe, it creates the plot with different major x-ticks using the matplotlib.dates drange function and timedelta.
# Lastly, it saves the file as a .png and returns the filename
def getPlot(df):
    plt.plot(df['Date'], df['P>100'], color='green', label='P>100')
    plt.plot(df['Date'], df['P>50'], color='blue', label='P>50')
    plt.plot(df['Date'], df['P>30'], color='orange', label='P>30')
    plt.plot(df['Date'], df['P>10'], color='red', label='P>10')

    plt.ylabel('Particles cm^-2 s^-1 sr^-1')
    plt.xlabel('Universal Time (UTC)')
    plt.title('GOES15 Proton Flux (5 minute data)')
    plt.ylim(0.005, 10e1)
    plt.yticks([10e-2, 10e-1, 10e0, 10e1, 10e2], ['10e-2', '10e-1', '10e0', '10e1', '10e2'])

    if (df.iloc[-1, -1] - df.iloc[0, -1]) <= timedelta(minutes=30):
        rangePlt = mdates.drange(df.iloc[0, -1], df.iloc[-1, -1], timedelta(minutes=5))

    elif timedelta(minutes=30) <(df.iloc[-1, -1] - df.iloc[0, -1]) <= timedelta(hours=1):
        rangePlt = mdates.drange(df.iloc[0, -1], df.iloc[-1, -1], timedelta(minutes=20))

    elif timedelta(hours=1) < (df.iloc[-1, -1] - df.iloc[0, -1]) <= timedelta(hours=5):
        rangePlt = mdates.drange(df.iloc[0, -1], df.iloc[-1, -1], timedelta(hours=1))

    elif timedelta(hours=5) < (df.iloc[-1, -1] - df.iloc[0, -1]) <= timedelta(hours=10):
        rangePlt = mdates.drange(df.iloc[0, -1], df.iloc[-1, -1], timedelta(hours=3))

    elif timedelta(hours=10) < (df.iloc[-1, -1] - df.iloc[0, -1]) <= timedelta(hours=24):
        rangePlt = mdates.drange(df.iloc[0, -1], df.iloc[-1, -1], timedelta(hours=6))

    else:
        rangePlt = mdates.drange(df.iloc[0, -1], df.iloc[-1, -1], timedelta(hours=12))

    plt.xticks(rangePlt)
    plt.gca().xaxis.set_minor_locator(AutoMinorLocator(5))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%b %d'))  # using the strftime table
    plt.yscale('symlog', linthreshy=0.005)
    plt.grid()
    plt.tight_layout()
    plt.legend(('P>100', 'P>50', 'P>30', 'P>10'))
    plt.savefig('fluxplot.png', bbox_inches='tight')
    return 'fluxplot.png'


# This method determines the criticality of a proton flux event. Note that this function is only triggered (via
# mainApp.py) if the input parameter "flux" is above a given threshold, so there is no need to check once again in this
# method. Once the criticaility level is defined, it calls the sendEmail method to send an email and the postAPI method
# to make a POST request. It does this by passing the flux value (MeV),the pval (P>10, P>30, P>50, P>100), the
# criticality level, and the filename of the history plot (plotFile)
def fluxCriticality(flux, pval, plotFile):
    if 1 < flux < 10:
        level = "[WARNING]"

    elif 10 <= flux < 100:
        level = "[ALERT]"

    elif 100 <= flux:
        level = "[CRITICAL]"

    sendEmail(level, flux, pval, plotFile)
    postAPI(level, flux)
