from flask import Flask, jsonify, request, render_template
import requests

app = Flask(__name__)

EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/"


#Веб-интерфейс html

@app.route('/')
def home():
    """Отображает главную страницу с формой конвентации"""
    return render_template('index.html')

@app.route('/convert-form', methods=['POST'])
def convert_form():
    """
    Обрабатывает POST-запрос из HTML-формы.
    Получает данные из form, конвертируя валюту ипоказывает результат.
    """

    # Получаем данные из form (не из URL-пареметров)

    from_currency =  request.form.get()
    to_currency = request.args.get('to', type=str)
    amount = request.args.get('amount', type=float)

    #Валидация

    if  from_currency is None or to_currency is None or amount is None:
        return render_template('index.html', error='Заполни все поля!')

    if not from_currency.strip() or not to_currency.strip():
        return render_template('index.html', error='Коды валют не могут быть пустыми!')
    
    from_currency = from_currency.strip().upper()
    to_currency = to_currency.strip().upper()

    try:
        #Запрос к внешнему API
        response = requests.get(f"{EXCHANGE_API_URL}{from_currency}")
        response.raise_for_status()
        data = response.json()

        exchange_rate = data['rates'].get(to_currency)
        if not exchange_rate:
            return render_template('index.html', error=f'Валюта {to_currency} не найдена')
        
        converted_amount = round(amount * exchange_rate, 2)

        #Передаё результат в шаблон
        return render_template('result.html',
                                from_curr=from_currency, 
                                to_curr=to_currency,
                                amount=amount,
                                converted=converted_amount, 
                                rate=exchange_rate
                                )
    except requests.exceptions.RequestException:
        return render_template('index.html', error='Ошибка получения курсов валют. Попробуйте позже.')
    except Exception as e:
        return render_template('index.html', error=f'Ошибка: {str(e)}')

# REST API

@app.route('/')
def index():
    return "Currency converter API is running. Use /convert?from=USD&to=RUB&amount=100"

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/convert', methods=['GET'])
def convert_currency():
    """
    Эндпоинт для конертации валют.
    Ожидает три параметра в строке запроса (query parameters)
    - from: исходная валюта (например, USD)
    - to: целевая валюта (например, EUR)
    - amount: количество для конвертации
    """

#1

    from_currency = request.args.get('from', type=str)
    to_currency = request.args.get('to', type=str)
    amount = request.args.get('amount', type=float)

#2

    if  from_currency is None or to_currency is None or amount is None:
        return jsonify({'error': 'Missing required parameters(from, to, amount)'}), 400
    
    if not from_currency.strip() or not to_currency.strip():
        return jsonify({'error': 'Currency codes cannot be empty'}), 400
    
#3
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    try:
        response = requests.get(f"{EXCHANGE_API_URL}{from_currency}")
        response.raise_for_status()
        data = response.json()

        exchange_rate = data['rates'].get(to_currency)
        if not exchange_rate:
            return jsonify({'error': f'Target currency {to_currency} not found'}), 400

        converted_amount = round(amount * exchange_rate, 2)

#5. Формируем и возвращаем ответ в формате JSON
        result = {
            'from': from_currency,
            'to': to_currency,
            'amount': amount,
            'converted_amount': converted_amount,
            'rate': exchange_rate
        }
        return jsonify(result)

    except requests.exceptions.RequestException as e:

        #Ошибка сети или HTTP-статус не 2xx

        return jsonify({'error': 'Failed to fetch data from exchange service'}), 500

    except Exception as e:
        # ловим другие непредвиденные ошибки
        return jsonify({'error': str(e)}), 500

#запускаем сервер только если файл запущен напрямую

if __name__ == '__main__':
    app.run(debug=True, port=5000)

