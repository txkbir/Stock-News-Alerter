import os
import requests
import smtplib
from twilio.rest import Client


# TODO: DETERMINE MINIMUM PERCENT CHANGE IN STOCK FOR YOU TO WANT TO BE NOTIFIED
MIN_PERCENT_CHANGE = 0

# SELECT WHAT TICKER YOU WANT TO MONITOR
STOCK_TICKER = "TSLA"
# SELECT WHAT COMPANY YOU WANT TO SEE NEWS HEADLINES OF
COMPANY_NAME = "Tesla"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

# TODO: CHANGE THESE EMAILS IF YOU WANT TO SEND THE MESSAGES TO SOMEONE ELSE
TO_EMAIL = os.environ['MY_EMAIL']
FROM_EMAIL = os.environ['MY_EMAIL']

alpha_api_key = os.environ['ALPHA_V_API_KEY']
alpha_v_parameters = {
    'function': 'TIME_SERIES_DAILY',
    'symbol': STOCK_TICKER,
    'apikey': alpha_api_key,
}
alpha_response = requests.get(url=STOCK_ENDPOINT, params=alpha_v_parameters)
alpha_data = alpha_response.json()
alpha_dict = alpha_data['Time Series (Daily)']


# When stock price increase/decreases by 5% between yesterday and the day before yesterday then print("Get News").
stock_closing_prices: list[float] = [float(dic['4. close']) for (date, dic) in alpha_dict.items()][:2]
difference: float = abs(stock_closing_prices[1] - stock_closing_prices[0])
is_positive: bool = stock_closing_prices[1] - stock_closing_prices[0] > 0
arrow: str = '🔺' if is_positive else '🔻'
percent_change: float = (difference / stock_closing_prices[0]) * 100

if percent_change > MIN_PERCENT_CHANGE:
    # Get the first 3 news pieces for the company
    news_api_key = os.environ['NEWS_API_KEY']
    news_parameters = {
        'apiKey': news_api_key,
        'q': COMPANY_NAME,
        'language': 'en',
    }
    news_response = requests.get(url=NEWS_ENDPOINT, params=news_parameters)
    news_data = news_response.json()
    news_articles = news_data['articles']
    three_article_dicts = [article_dict for article_dict in news_articles][:3]

    three_articles = [{article['url']: (article['title'], article['description'])} for article in three_article_dicts][:3]

    account_sid = os.environ['TWILIO_ACC_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_num = os.environ['TWILIO_NUM']
    my_num = os.environ['MY_NUM']
    client = Client(account_sid, auth_token)

    app_pass = os.environ['GMAIL_APP_PASS']
    EMAIL = os.environ['MY_EMAIL']

    for article_dict in three_articles:
        url, (title, description) = article_dict.popitem()  # Get the URL and tuple from the dictionary

        text_msg = f'{STOCK_TICKER}: {arrow}{percent_change:.2f}% Headline: {title} -- Brief: {description}'
        message = client.messages.create(body=text_msg, from_=twilio_num, to=my_num)
        print(message.status)

        with smtplib.SMTP('smtp.gmail.com') as connection:
            connection.starttls()
            connection.login(user=EMAIL, password=app_pass)
            email_subject = f'Subject: {STOCK_TICKER}: {arrow}{percent_change:.2f}% Headline: {title}'
            email_message = (f'Brief: {description}\n\nFor more, read {url}\n\n'
                             f'This message was automated by a script I made in Python.')
            full_email_message = f'{email_subject}\n\n{email_message}'
            connection.sendmail(
                from_addr=FROM_EMAIL,
                to_addrs=TO_EMAIL,
                msg=full_email_message.encode('utf-8')
            )
            print('sent email')
