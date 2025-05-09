from flask import Flask, render_template, request, jsonify, redirect, url_for, session, json

from pymongo import MongoClient

from datetime import datetime

app = Flask(__name__)



# MongoDB 연결

client = MongoClient("mongodb://localhost:27017/")

db = client["Seedo"]  # DB 이름

users_collection = db["users"]  # 컬렉션 (테이블 역할)

app.secret_key = '98dabc3d35b88ef7b5542996e20be45b'  # 보안 키 필수!



from datetime import datetime
def normalize_keys(user):
    correction_map = {
        "Eggplant": "egg_plant",
        "redpepper": "red_pepper",
        "paprika": "bull_pepper",
        "grape": "grapes"
    }

    for field in ["seeds", "food", "delivery"]:
        if field in user:
            corrected = {}
            for key, value in user[field].items():
                std_key = correction_map.get(key, key)
                corrected[std_key] = corrected.get(std_key, 0) + value
            user[field] = corrected

    return user
default_user = {
    "kakao_id": "123456",
    "nickname": "홍길동",
    "credit": 1000,
    "won": 0,
    "seeds": {
        "tomato": 0,
        "potato": 0,
        "carrot": 0,
        "egg_plant": 0,
        "basil": 0,
        "red_pepper": 0,
        "bull_pepper": 0,
        "grapes": 0
    },
    "food": {
        "tomato": 0,
        "potato": 0,
        "carrot": 0,
        "egg_plant": 0,
        "basil": 0,
        "red_pepper": 0,
        "bull_pepper": 0,
        "grapes": 0

    },

    "delivery": {
        "tomato": 0,
        "potato": 0,
        "carrot": 0,
        "egg_plant": 0,
        "basil": 0,
        "red_pepper": 0,
        "bull_pepper": 0,
        "grapes": 0

    },

    "placements": [],

    "last_check_in_date": datetime.utcnow(),  # 마지막 로그인 시각
    "date_minus": 0                           # 오늘과 마지막 로그인 날짜 차이(일)

}

@app.route('/plant_seed', methods=['POST'])

def plant_seed():

    kakao_id = session.get('kakao_id')

    if not kakao_id:

        return jsonify({"success": False})



    data   = request.get_json()

    seedId = data['seedId']

    x      = data['x']

    y      = data['y']

    now    = datetime.utcnow()



    # 처음 심을 땐 daysElapsed = 0

    placement = {

        "seedId": seedId,

        "x": x,

        "y": y,

        "plantedAt": now,

        "daysElapsed": 0

    }



    users_collection.update_one(

        {"kakao_id": kakao_id},

        {

            "$inc": { f"seeds.{seedId}": -1 },

            "$push": { "placements": placement }

        }

    )



    return jsonify({

        "success": True,

        "plantedAt": now.strftime('%Y-%m-%d %H:%M:%S'),

        "daysElapsed": 0

    })

@app.route('/')

def index():

    return render_template('index.html')



@app.route('/login')

def login():

    return render_template('login.html')



@app.route('/login_kakao', methods=['POST'])
def login_kakao():
    user_info = request.get_json()
    kakao_id = str(user_info.get("id"))
    nickname = user_info.get("properties", {}).get("nickname", "알 수 없음")
    now = datetime.utcnow()

    user = users_collection.find_one({"kakao_id": kakao_id})

    if not user:
        users_collection.insert_one({
            "kakao_id": kakao_id,
            "nickname": nickname,
            "credit": 1000,
            "won": 0,
            "seeds": {
                "tomato": 0, "potato": 0, "carrot": 0, "egg_plant": 0,
                "basil": 0, "red_pepper": 0, "bull_pepper": 0, "grapes": 0
            },
            "food": {
                "tomato": 0, "potato": 0, "carrot": 0, "egg_plant": 0,
                "basil": 0, "red_pepper": 0, "bull_pepper": 0, "grapes": 0
            },
            "delivery": {
                "tomato": 0,
                "potato": 0,
                "carrot": 0,
                "egg_plant": 0,
                "basil": 0,
                "red_pepper": 0,
                "bull_pepper": 0,
                "grapes": 0
            },
            "placements": [],
            "last_check_in_date": now,
            "date_minus": 0
        })
    else:
        prev = user.get("last_check_in_date")
        prev_date = prev.date() if prev else now.date()
        today = now.date()
        diff_days = (today - prev_date).days

        old_minus = user.get("date_minus", 0)

        if old_minus >= 10:
            # 이미 10일 이상이면 유지
            new_minus = old_minus
        elif diff_days == 0:
            # 연속 접속이면 리셋
            new_minus = 0
        else:
            # 누적
            new_minus = old_minus + diff_days

        users_collection.update_one(
            {"kakao_id": kakao_id},
            {
                "$set": {
                    "last_check_in_date": now,
                    "date_minus": new_minus
                }
            }
        )
    session['kakao_id'] = kakao_id
    return jsonify({"redirect_url": url_for('home')})



@app.route('/watch_ad', methods=['POST'])
def watch_ad():
    kakao_id = session.get('kakao_id')
    if not kakao_id:
        return jsonify(success=False), 403

    users_collection.update_one(
        {"kakao_id": kakao_id},
        {"$set": {"date_minus": 0}}
    )
    return jsonify(success=True)



from datetime import datetime
from dateutil import parser as date_parser  # 설치: pip install python-dateutil

@app.route('/home')
def home():
    kakao_id = session.get('kakao_id')
    if not kakao_id:
        return redirect(url_for('login'))
    
    user = users_collection.find_one({"kakao_id": kakao_id})
    if not user:
        return redirect(url_for('login'))
    user = normalize_keys(user)  # ← 키 정규화 적용
    updated_placements = []
    for idx, p in enumerate(user.get('placements', [])):
        planted_raw = p['plantedAt']

        # 디버깅 로그로 현재 형태 출력
        print(f"[DEBUG] raw plantedAt: {planted_raw} (type: {type(planted_raw)})")

        # datetime 변환
        if isinstance(planted_raw, dict) and '$date' in planted_raw:
            planted = date_parser.parse(planted_raw['$date'])
        elif isinstance(planted_raw, str):
            planted = date_parser.parse(planted_raw)
        elif isinstance(planted_raw, datetime):
            planted = planted_raw
        else:
            print(f"[ERROR] Unrecognized plantedAt format: {planted_raw}")
            planted = datetime.utcnow()

        days = (datetime.now().date() - planted.date()).days


        # 디버깅 로그로 days 확인
        print(f"[DEBUG] seedId: {p['seedId']}, daysElapsed calculated: {days}")

        users_collection.update_one(
            {"kakao_id": kakao_id},
            {"$set": {f"placements.{idx}.daysElapsed": days}}
        )

        updated_placements.append({
            "seedId": p['seedId'],
            "x": p['x'],
            "y": p['y'],
            "plantedAt": planted.strftime('%Y-%m-%d %H:%M:%S'),
            "daysElapsed": days
        })
    print("[DEBUG] updated_placements =", updated_placements)

    return render_template(
        'home.html',
        nickname=user['nickname'],
        seeds=user['seeds'],
        credit=user['credit'],
        placements=updated_placements,  # ← 이건 이미 잘 되어 있음
        food=user['food'],
        date_minus=user.get("date_minus", 0)
    )
    return render_template(
        'home.html',
        nickname=user['nickname'],
        seeds=user['seeds'],
        credit=user['credit'],
        placements=updated_placements,
        food=user['food'],
        date_minus=user.get("date_minus", 0)
    )


@app.route('/add_credit', methods=['POST'])
def add_credit():
    if 'kakao_id' not in session:
        return jsonify({"message": "로그인이 필요합니다."}), 403

    kakao_id = session['kakao_id']
    user = users_collection.find_one({"kakao_id": kakao_id})

    if not user:
        return jsonify({"message": "사용자 정보가 없습니다."}), 404

    data = request.get_json()
    amount = data.get('amount', 10)

    users_collection.update_one(
        {"kakao_id": kakao_id},
        {"$inc": {"credit": amount}}
    )

    return jsonify({"message": f"{amount} SEED를 획득하였습니다!"})

@app.route('/credit')
def credit():
    return render_template('credit.html')

@app.route('/storage')
def storage():
    if 'kakao_id' not in session:
        return redirect(url_for('login'))

    user = users_collection.find_one({"kakao_id": session['kakao_id']})
    if not user:
        return redirect(url_for('login'))
    user = normalize_keys(user)  # ← 키 정규화
    food_counts = user.get('food', {})

    food_data = [
        {"id": "carrot", "name": "당근", "price": 1130, "count": food_counts.get("carrot", 0), "image": "carrot_round.png"},
        {"id": "tomato", "name": "토마토", "price": 510, "count": food_counts.get("tomato", 0), "image": "tomato_round.png"},
        {"id": "basil", "name": "바질", "price": 270, "count": food_counts.get("basil", 0), "image": "basil_round.png"},
        {"id": "potato", "name": "감자", "price": 550, "count": food_counts.get("potato", 0), "image": "potato_round.png"},
        {"id": "Eggplant", "name": "가지", "price": 990, "count": food_counts.get("egg_plant", 0), "image": "egg_plant_round.png"},
        {"id": "redpepper", "name": "고추", "price": 1130, "count": food_counts.get("red_pepper", 0), "image": "red_pepper_round.png"},
        {"id": "paprika", "name": "파프리카", "price": 1130, "count": food_counts.get("bull_pepper", 0), "image": "paprika_round.png"},
        {"id": "grape", "name": "포도", "price": 2430, "count": food_counts.get("grapes", 0), "image": "grape_round.png"}
    ]
    return render_template('storage.html', food=food_data)
@app.route('/store')
def store():
    seed_data = [
        {"id": "carrot", "name": "당근 씨앗", "price": 40, "count": 0, "image": "carrot_round.png"},
        {"id": "tomato", "name": "토마토 씨앗", "price": 70, "count": 0, "image": "tomato_round.png"},
        {"id": "basil", "name": "바질 씨앗", "price": 50, "count": 0, "image": "basil_round.png"},
        {"id": "potato", "name": "감자 씨앗", "price": 60, "count": 0, "image": "potato_round.png"},
        {"id": "Eggplant", "name": "가지 씨앗", "price": 50, "count": 0, "image": "egg_plant_round.png"},
        {"id": "redpepper", "name": "고추 씨앗", "price": 50, "count": 0, "image": "red_pepper_round.png"},
        {"id": "paprika", "name": "파프리카 씨앗", "price": 50, "count": 0, "image": "paprika_round.png"},
        {"id": "grape", "name": "포도 씨앗", "price": 120, "count": 0, "image": "grape_round.png"}
    ]
    return render_template('store.html', seeds=seed_data)

@app.route('/buy_seeds', methods=['POST'])
def buy_seeds():
    if 'kakao_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."})

    kakao_id = session['kakao_id']
    user = users_collection.find_one({"kakao_id": kakao_id})
    if not user:
        return jsonify({"success": False, "message": "사용자 정보가 없습니다."})

    data = request.get_json()  # 예: {'carrot': 2, 'tomato': 1}

    # 실제 가격 매핑
    seed_prices = {
        "carrot": 40,
        "tomato": 70,
        "basil": 50,
        "potato": 60,
        "Eggplant": 50,
        "redpepper": 50,
        "paprika": 50,
        "grape": 120
    }

    total_cost = 0
    for seed_id, count in data.items():
        price = seed_prices.get(seed_id, 50)
        total_cost += price * count
    if user['credit'] < total_cost:
        return jsonify({"success": False, "message": "크레딧이 부족합니다."})

    for seed_id, count in data.items():
        users_collection.update_one(
            {"kakao_id": kakao_id},
            {
                "$inc": {
                    f"seeds.{seed_id}": count,
                    "credit": -price * count
                }
            }
        )

    return jsonify({"success": True})


@app.route('/box', methods=['POST'])
def box():
    raw_data = request.form.get('boxData')
    if not raw_data:
        return "데이터 없음", 400

    try:
        box_data = json.loads(raw_data)
    except:
        return "데이터 오류", 400

    name_map = {
        "carrot": "당근",
        "tomato": "토마토",
        "basil": "바질",
        "potato": "감자",
        "Eggplant": "가지",
        "redpepper": "고추",
        "paprika": "파프리카",
        "grape": "포도"
    }

    prices = {
        "carrot": 1130,
        "tomato": 510,
        "basil": 270,
        "potato": 550,
        "Eggplant": 990,
        "redpepper": 1130,
        "paprika": 1130,
        "grape": 2430
    }

    return render_template("box.html", items=box_data, prices=prices, name_map=name_map)

@app.route('/sell_items', methods=['POST'])
def sell_items():
    prices = {
        "carrot": 1130,
        "tomato": 510,
        "basil": 270,
        "potato": 550,
        "Eggplant": 990,
        "redpepper": 1130,
        "paprika": 1130,
        "grape": 2430
    }
    if 'kakao_id' not in session:
        return jsonify(success=False, message="로그인이 필요합니다.")

    kakao_id = session['kakao_id']
    user = users_collection.find_one({"kakao_id": kakao_id})
    if not user:
        return jsonify(success=False, message="사용자 정보가 없습니다.")

    data = request.get_json()  # 예: {'carrot': 2, 'tomato': 1}
    total_price = 0

    updates = {}
    for item, count in data.items():
        current = user['food'].get(item, 0)
        if count > current:
            return jsonify(success=False, message=f"{item} 재고 부족")
        total_price += count * prices[item]
        updates[f"food.{item}"] = -count

    updates["won"] = total_price

    users_collection.update_one(
        {"kakao_id": kakao_id},
        {"$inc": updates}
    )
    
    return jsonify(success=True, won=total_price, redirect_url=url_for("home"))

@app.route('/start_delivery', methods=['POST'])
def start_delivery():
    if 'kakao_id' not in session:
        return jsonify(success=False, message="로그인이 필요합니다.")

    kakao_id = session['kakao_id']
    user = users_collection.find_one({"kakao_id": kakao_id})
    if not user:
        return jsonify(success=False, message="사용자 정보가 없습니다.")

    data = request.get_json()  # 예: {'tomato': 2, 'carrot': 1}

    updates = {}
    for item, count in data.items():
        current = user['food'].get(item, 0)
        if count > current:
            return jsonify(success=False, message=f"{item} 재고 부족")
        updates[f"food.{item}"] = -count
        updates[f"delivery.{item}"] = count


    users_collection.update_one(
        {"kakao_id": kakao_id},
        {"$inc": updates}
    )

    return jsonify(success=True)


@app.route('/my')
def my():
    if 'kakao_id' not in session:
        return redirect(url_for('login'))

    kakao_id = session['kakao_id']
    user = users_collection.find_one({"kakao_id": kakao_id})
    user = normalize_keys(user)  # ← 키 정규화
    if not user:
        return redirect(url_for('login'))

    food = user['food']
    delivery = user.get('delivery', {})

    food_meta = {
        "potato":  {"name": "감자", "image": "potato_round.png", "price": 550},
        "carrot":  {"name": "당근", "image": "carrot_round.png", "price": 1130},
        "tomato":  {"name": "토마토", "image": "tomato_round.png", "price": 510},
        "basil":   {"name": "바질", "image": "basil_round.png", "price": 270},
        "egg_plant": {"name": "가지", "image": "egg_plant_round.png", "price": 990},
        "red_pepper": {"name": "고추", "image": "red_pepper_round.png", "price": 1130},
        "bull_pepper": {"name": "파프리카", "image": "paprika_round.png", "price": 1130},
        "grapes":  {"name": "포도", "image": "grape_round.png", "price": 2430},
    }

    # 창고 프리뷰
    food_preview = []
    for key, value in food.items():
        if value > 0 and key in food_meta:
            meta = food_meta[key]
            food_preview.append({
                "name": meta["name"],
                "image": meta["image"],
                "count": value,
                "price": meta["price"]
            })
    food_preview = food_preview[:3]

    # 배송 프리뷰
    delivery_preview = []
    for key, value in delivery.items():
        if value > 0 and key in food_meta:
            meta = food_meta[key]
            delivery_preview.append({
                "name": meta["name"],
                "image": meta["image"],
                "count": value
            })
    delivery_preview = delivery_preview[:3]

    return render_template(
        'my.html',
        nickname=user['nickname'],
        credit=user['credit'],
        won=user['won'],
        food_preview=food_preview,
        delivery_preview=delivery_preview
    )

@app.route('/exchange', methods=['POST'])
def exchange():
    if 'kakao_id' not in session:
        return jsonify(success=False)

    kakao_id = session['kakao_id']
    users_collection.update_one(
        {"kakao_id": kakao_id},
        {"$set": {"won": 0}}
    )

    return jsonify(success=True)


@app.route('/delivery')
def delivery():
    if 'kakao_id' not in session:
        return redirect(url_for('login'))

    user = users_collection.find_one({"kakao_id": session['kakao_id']})
    delivery = user.get("delivery", {})
    user = normalize_keys(user)  # ← 키 정규화
    food_meta = {
        "potato":  {"name": "감자", "image": "potato_round.png"},
        "carrot":  {"name": "당근", "image": "carrot_round.png"},
        "tomato":  {"name": "토마토", "image": "tomato_round.png"},
        "basil":   {"name": "바질", "image": "basil_round.png"},
        "egg_plant": {"name": "가지", "image": "egg_plant_round.png"},
        "red_pepper": {"name": "고추", "image": "red_pepper_round.png"},
        "bull_pepper": {"name": "파프리카", "image": "paprika_round.png"},
        "grapes":  {"name": "포도", "image": "grape_round.png"},
    }

    delivery_items = []
    for key, count in delivery.items():
        if count > 0 and key in food_meta:
            delivery_items.append({
                "name": food_meta[key]["name"],
                "image": food_meta[key]["image"],
                "count": count
            })

    return render_template('delivery.html', delivery_items=delivery_items)



if __name__ == '__main__':
    app.run(debug=True)
