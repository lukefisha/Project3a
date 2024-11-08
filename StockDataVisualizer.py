import requests
import csv
from Graphs import bar_graph, line_graph
from dotenv import load_dotenv
import os
from flask import Flask, render_template, request

app = Flask(__name__)
app.config["DEBUG"] = True

#Function for setting up a sercure API key
def APIConfigure():
    #loads .env file
    load_dotenv()
    #sets api_key from .env file
    api_key = os.getenv("Alpha_API_key")
    return api_key


#Function for obtaining stock data
def stock_data(symbol: str, time_series: str, start_date: str, end_date: str) ->dict:
    #sets api key from .env file
    api_key = APIConfigure()
    
    #sets time series map for selection 1-4
    time_series_map={
        "1": "TIME_SERIES_INTRADAY",
        "2": "TIME_SERIES_DAILY",
        "3": "TIME_SERIES_WEEKLY",
        "4": "TIME_SERIES_MONTHLY", 
    }

    #sets parameters for api calls in the url so that we can keep the API key secure
    parameters={
        "function": time_series_map[time_series],
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "full"
    }

    if time_series == "1":
        parameters["interval"] = "5min"

    #Base url to be modified by parameters
    url = "https://www.alphavantage.co/query"

    #reponse set equal to request
    r = requests.get(url, params=parameters)

    #data set equal to r.json for proper api calling
    data = r.json()

    #returns proper data from function
    if time_series == "1":
        key = "Time Series (5mins)"
    elif time_series == "2":
        key = "Time Series (Daily)"
    elif time_series == "3":
        key = "Weekly Time Series"
    elif time_series == "4":
        key = "Monthly Time Series"

    time_series_data = data.get(key,{})
    filtered_data_dic = {date: values for date, values in time_series_data.items() if start_date <= date.split(' ')[0] <= end_date}

    #print(filtered_data_dic)

    #initalizes the dic to empty 
    dates = []
    opens = []
    highs = []
    lows = []
    closes = []

    #fills dic with data from json file
    for date, values in sorted(filtered_data_dic.items()):
        dates.append(date.split(' ')[0])
        opens.append(float(values["1. open"]))
        highs.append(float(values["2. high"]))
        lows.append(float(values["3. low"]))
        closes.append(float(values["4. close"]))
    
    return {"dates": dates, "open": opens, "high": highs, "low": lows, "close": closes}
        

print('-------Stock Data Visualizer-------')

@app.route('/', methods=["GET", "POST"])
def index():
    companies = []
    with open('stocks.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            symbol, name, sector = row
            companies.append({'symbol': symbol, 'name': name, 'sector': sector})

    chart = None
    if request.method == "POST":
        #get values from user input
        stockSymbol = request.form["symbol"]
        chartType = request.form["chart_type"]
        timeSeries = request.form["time_series"]
        startDate = request.form["start_date"]
        endDate = request.form["end_date"]
        try:
            #get the graph for either bar or line graph
            data = stock_data(stockSymbol, timeSeries, startDate, endDate)
            if chartType == '1':
                title = f"Stock Data for {stockSymbol}: {startDate} to {endDate}"
                chart = bar_graph(title, data['dates'], data['open'], data['high'], data['low'], data['close'])
            elif chartType == '2':
                chart = data
                title = f"Stock Data for {stockSymbol}: {startDate} to {endDate}"
                chart = line_graph(title, data['dates'], data['open'], data['high'], data['low'], data['close'])
        except ValueError as e:
            chart = None
            print("Error fetching data:", e)
    #return index html with the chart
    return render_template("index.html", chart=chart, companies=companies)