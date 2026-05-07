from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context
import requests
import json
import os
import re
import time

app = Flask(__name__, static_folder='static')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}

def wb_get(url, retries=3, pause=2):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            print(f"  [{r.status_code}] {url[:100]}")
            if r.status_code == 429:
                wait = pause * (attempt + 1)
                print(f"  429 rate limit - waiting {wait}s...")
                time.sleep(wait)
                continue
            return r
        except Exception as e:
            print(f"  request error (attempt {attempt+1}): {e}")
            time.sleep(1)
    return None

def extract_products(data):
    if isinstance(data, dict):
        d = data.get("data", {})
        if isinstance(d, dict):
            p = d.get("products", [])
            if p:
                return p
        p = data.get("products", [])
        if p:
            return p
    return []

def get_basket_host(vol):
    ranges = [
        (0,143,"01"),(144,287,"02"),(288,431,"03"),(432,719,"04"),(720,1007,"05"),
        (1008,1061,"06"),(1062,1115,"07"),(1116,1169,"08"),(1170,1313,"09"),
        (1314,1601,"10"),(1602,1655,"11"),(1656,1919,"12"),(1920,2045,"13"),
        (2046,2189,"14"),(2190,2405,"15"),(2406,2621,"16"),(2622,2837,"17"),
        (2838,3053,"18"),(3054,3269,"19"),(3270,3485,"20"),(3486,3701,"21"),
        (3702,3917,"22"),(3918,4133,"23"),
    ]
    for lo, hi, num in ranges:
        if lo <= vol <= hi:
            return num
    return "24"

def get_image_urls(article, count=5):
    vol = article // 100000
    part = article // 1000
    basket = get_basket_host(vol)
    base = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{article}/images/big"
    return [f"{base}/{i}.jpg" for i in range(1, count + 1)]

def fetch_product_by_article(article):
    for url in [
        f"https://card.wb.ru/cards/v3/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}",
        f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}",
    ]:
        r = wb_get(url)
        if r and r.status_code == 200:
            try:
                products = extract_products(r.json())
                if products:
                    return products[0]
            except Exception as e:
                print(f"  parse error: {e}")
    return None

def fetch_product_description(article):
    try:
        vol = article // 100000
        basket = get_basket_host(vol)
        url = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{article//1000}/{article}/info/ru/card.json"
        r = wb_get(url, retries=2)
        if r and r.status_code == 200:
            return r.json().get("description", "")
    except:
        pass
    return ""

def search_products(query, page=1, limit=20):
    encoded = requests.utils.quote(query)
    for url in [
        f"https://search.wb.ru/exactmatch/ru/common/v9/search?appType=1&curr=rub&dest=-1257786&page={page}&query={encoded}&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false",
        f"https://search.wb.ru/exactmatch/ru/common/v7/search?appType=1&curr=rub&dest=-1257786&page={page}&query={encoded}&resultset=catalog&sort=popular&spp=30",
    ]:
        r = wb_get(url)
        if r and r.status_code == 200:
            try:
                data = r.json()
                products = extract_products(data)
                print(f"  products found: {len(products)}")
                if not products:
                    print(f"  top keys: {list(data.keys())}")
                if products:
                    return products[:limit]
            except Exception as e:
                print(f"  parse error: {e}")
    return []

def fetch_seller_page(seller_id, page=1):
    for url in [
        f"https://catalog.wb.ru/sellers/v2/catalog?appType=1&curr=rub&dest=-1257786&sort=popular&spp=30&supplier={seller_id}&page={page}",
        f"https://catalog.wb.ru/sellers/v3/catalog?appType=1&curr=rub&dest=-1257786&sort=popular&spp=30&supplier={seller_id}&page={page}",
        f"https://catalog.wb.ru/sellers/catalog?appType=1&curr=rub&dest=-1257786&sort=popular&spp=30&supplier={seller_id}&page={page}",
    ]:
        r = wb_get(url)
        if r and r.status_code == 200:
            try:
                data = r.json()
                products = extract_products(data)
                total = data.get("data", {}).get("total", len(products)) if isinstance(data.get("data"), dict) else len(products)
                print(f"  seller products: {len(products)}, total: {total}")
                if products:
                    return products, total
            except Exception as e:
                print(f"  seller parse error: {e}")
    return [], 0

def format_product(raw):
    article = raw.get("id", 0)
    price_data = raw.get("sizes", [{}])[0].get("price", {}) if raw.get("sizes") else {}
    return {
        "article": article,
        "name": raw.get("name", ""),
        "brand": raw.get("brand", ""),
        "subject": raw.get("subjectName", raw.get("subject", "")),
        "price": price_data.get("basic", price_data.get("product", 0)) // 100 if price_data else 0,
        "sale_price": price_data.get("product", 0) // 100 if price_data else 0,
        "rating": raw.get("reviewRating", 0),
        "feedbacks": raw.get("feedbacks", 0),
        "images": get_image_urls(article),
        "url": f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
        "description": raw.get("description", ""),
    }

def extract_seller_id(url_or_id):
    s = url_or_id.strip()
    if s.isdigit():
        return int(s)
    m = re.search(r'/seller/(\d+)', s)
    if m:
        return int(m.group(1))
    return None

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/article/<int:article>")
def api_article(article):
    raw = fetch_product_by_article(article)
    if not raw:
        return jsonify({"error": "Товар не найден"}), 404
    product = format_product(raw)
    if not product["description"]:
        product["description"] = fetch_product_description(article)
    return jsonify(product)

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    if not query:
        return jsonify({"error": "Укажите поисковый запрос"}), 400
    products = [format_product(p) for p in search_products(query, page=page)]
    return jsonify({"query": query, "page": page, "count": len(products), "products": products})

@app.route("/api/bulk", methods=["POST"])
def api_bulk():
    data = request.json or {}
    articles = data.get("articles", [])
    if not articles:
        return jsonify({"error": "Нет артикулов"}), 400
    results, errors = [], []
    for art in articles[:50]:
        try:
            raw = fetch_product_by_article(int(art))
            if raw:
                results.append(format_product(raw))
            else:
                errors.append({"article": art, "error": "не найден"})
        except Exception as e:
            errors.append({"article": art, "error": str(e)})
    return jsonify({"results": results, "errors": errors})

@app.route("/api/seller/info")
def api_seller_info():
    raw = request.args.get("url", "").strip()
    if not raw:
        return jsonify({"error": "Укажите ссылку или ID продавца"}), 400
    seller_id = extract_seller_id(raw)
    if not seller_id:
        return jsonify({"error": "Не удалось определить ID продавца"}), 400
    products_first, total = fetch_seller_page(seller_id, page=1)
    if not products_first:
        return jsonify({"error": "Продавец не найден или нет товаров"}), 404
    seller_name = products_first[0].get("brand", f"Продавец #{seller_id}")
    return jsonify({
        "seller_id": seller_id,
        "seller_name": seller_name,
        "total_approx": total,
        "preview": [format_product(p) for p in products_first[:6]],
    })

@app.route("/api/seller/parse")
def api_seller_parse():
    raw = request.args.get("url", "").strip()
    max_pages = min(int(request.args.get("max_pages", 100)), 200)
    seller_id = extract_seller_id(raw)
    if not seller_id:
        def err():
            yield f'data: {json.dumps({"type":"error","message":"Не удалось определить ID продавца"})}\n\n'
        return Response(stream_with_context(err()), mimetype="text/event-stream")
    def generate():
        total_loaded = 0
        known_total = None
        for page in range(1, max_pages + 1):
            products_raw, page_total = fetch_seller_page(seller_id, page)
            if known_total is None:
                known_total = page_total
            if not products_raw:
                break
            formatted = [format_product(p) for p in products_raw]
            total_loaded += len(formatted)
            yield f'data: {json.dumps({"type":"progress","page":page,"loaded":total_loaded,"total":known_total or "?"})}\n\n'
            yield f'data: {json.dumps({"type":"products","products":formatted})}\n\n'
            if len(products_raw) < 100:
                break
            time.sleep(0.3)
        yield f'data: {json.dumps({"type":"done","total":total_loaded})}\n\n'
    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, port=5050)
