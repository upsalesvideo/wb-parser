# WB Parser — Парсер Wildberries

Сервис для парсинга фото и описаний товаров с Wildberries.

## Установка

```bash
pip install -r requirements.txt
python app.py
```

Открой в браузере: http://localhost:5050

---

## Возможности

### Веб-интерфейс
- **Поиск** — ищи товары по ключевым словам
- **По артикулу** — получи данные одного товара
- **Массовый парсинг** — список артикулов за раз (до 50)
- Просмотр фото, описаний, цен, рейтингов
- Экспорт в JSON / CSV

### REST API

#### Получить товар по артикулу
```
GET /api/article/{article}
```

#### Поиск товаров
```
GET /api/search?q=кроссовки Nike&page=1
```

#### Массовый парсинг
```
POST /api/bulk
Content-Type: application/json

{"articles": [187433233, 156789012, 200000001]}
```

---

## Структура ответа (один товар)

```json
{
  "article": 187433233,
  "name": "Кроссовки мужские",
  "brand": "Nike",
  "subject": "Кроссовки",
  "price": 8990,
  "sale_price": 5990,
  "rating": 4.7,
  "feedbacks": 1243,
  "images": [
    "https://basket-04.wbbasket.ru/vol1874/part18743/187433233/images/big/1.jpg",
    "https://basket-04.wbbasket.ru/vol1874/part18743/187433233/images/big/2.jpg"
  ],
  "url": "https://www.wildberries.ru/catalog/187433233/detail.aspx",
  "description": "Описание товара..."
}
```

---

## Как скачать изображения

```python
import requests, os

def download_images(product: dict, folder: str = "images"):
    art = product["article"]
    path = os.path.join(folder, str(art))
    os.makedirs(path, exist_ok=True)
    for i, url in enumerate(product["images"]):
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(os.path.join(path, f"{i+1}.jpg"), "wb") as f:
                f.write(r.content)
            print(f"  Saved: {i+1}.jpg")
        else:
            break  # нет больше фото
```
