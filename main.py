import openai
import json
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf

openai.api_key = open('API_key', 'r').read()


def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period = '1y').iloc[-1].Close)

def calculate_sma(ticker, window):
    data = yf.Ticker(ticker).history(period = '1y').Close
    return str(data.rolling(window = window).mean().iloc[-1])

def calculate_ema(ticker, window):
    data = yf.Ticker(ticker).history(period = '1y').Close
    return str(data.ewm(span = window, adjust = False).mean().iloc[-1])

def calculate_rsi(ticker):
    data = yf.Ticker(ticker).history(period = '1y').Close
    delta = data.diff()
    up = delta.clip(lower = 0)
    down = -1 * delta.clip(upper = 0)
    ema_up = up.ewm(com = 14-1, adjust = False).mean()
    ema_down = down.ewm(com = 14-1, adjust = False).mean()
    rs = ema_up/ema_down
    return str(100 - (100 / (1+rs)).iloc[-1])

def calculate_macd(ticker):
    data = yf.Ticker(ticker).history(period = '1y').Close
    short_ema = data.ewm(span = 12, adjust = False).mean()
    long_ema = data.ewm(span = 26, adjust = False).mean()

    macd = short_ema - long_ema
    signal = macd.ewm(span = 9, adjust = False).mean()
    macd_histogram = macd - signal

    return f'{macd[-1]}, {signal[-1]}, {macd_histogram[-1]}'

def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period = '1y')
    plt.figure(figsize = (10, 5))
    plt.plot(data.index, data.Close)
    plt.title(f'{ticker} Stock Price over last year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()


functions = [
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (for example AAPL for Apple).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'calculate_sma',
        'description': 'Calculate the simple moving average for a given stock ticker and a window.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (for example AAPL for Apple).',
                },
                'window': {
                    'type': 'integer',
                    'description': 'The timeframe to consider when calculating the SMA'
                }
            },
            'required': ['ticker', 'window']
        }
    },
    {
        'name': 'calculate_ema',
        'description': 'Calculates the latest Exponential Moving Average (EMA) for a given stock using a specified window over the past year.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (e.g., MSFT for Microsoft).',
                },
                'window': {
                    'type': 'integer',
                    'description': 'The number of days over which the EMA is calculated.'
                }
            },
            'required': ['ticker', 'window']
        }
    },
    {
        'name': 'calculate_rsi',
        'description': 'Calculates the current Relative Strength Index (RSI) value for a given stock based on 14-day smoothing over the past year.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (e.g., TSLA for Tesla).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'calculate_macd',
        'description': 'Calculates the Moving Average Convergence Divergence (MACD), signal line, and MACD histogram for a given stock based on 12, 26, and 9-day EMAs over the past year.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (e.g., GOOG for Google).'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'plot_stock_price',
        'description': 'Generates and saves a line plot showing the daily closing stock price of a company over the past year. The plot is saved as "stock.png".',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (e.g., NFLX for Netflix).'
                }
            },
            'required': ['ticker']
        }
    }
]

available_functions = {
    'get_stock_price': get_stock_price,
    'calculate_sma': calculate_sma,
    'calculate_ema': calculate_ema,
    'calculate_rsi': calculate_rsi,
    'calculate_macd': calculate_macd,
    'plot_stock_price': plot_stock_price
}

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.title('Stock Analysis Assistant')

user_input = st.text_input('Input: ')

if user_input:
    try:
        st.session_state['messages'].append({'role': 'user', 'content': f'{user_input}'})

        response = openai.ChatCompletion.create(
            model = 'gpt-4o-mini',
            messages = st.session_state['messages'],
            functions = functions,
            function_call = 'auto'
        )

        response_message = response['choices'][0]['message']

        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            if function_name in ['get_stock_price', 'calculate_rsi', 'calculate_macd', 'plot_stock_price']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_sma', 'calculate_ema']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}

            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            if function_name == 'plot_stock_price':
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name': function_name,
                        'content': function_response
                    }
                )
                second_response = openai.ChatCompletion.create(
                    model = 'gpt-4o-mini',
                    messages = st.session_state['messages'],
                )
                st.text(second_response['choices'][0]['message']['content'])
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response['choices'][0]['message']['content']})
        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role': 'assistant', 'content': response_message['content']})
    except Exception as e:
        st.error(f'Error occurred: {str(e)}')