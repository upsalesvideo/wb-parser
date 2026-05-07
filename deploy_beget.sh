#!/bin/bash
# Запускать на сервере Beget через SSH
# Замени YOUR_LOGIN на свой логин Beget

cd ~/wb_parser

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

echo "Done. Configure .htaccess with your login and enable Passenger in Beget panel."
