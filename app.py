from flask import Flask, render_template, request, jsonify, redirect, url_for, session, json

from pymongo import MongoClient

from datetime import datetime

app = Flask(__name__)



# MongoDB 연결

client = MongoClient("mongodb://localhost:27017/")

db = client["Seedo"]  # DB 이름

users_collection = db["users"]  # 컬렉션 (테이블 역할)

app.secret_key = '98dabc3d35b88ef7b5542996e20be45b'  # 보안 키 필수!



# 사용자 기본 구조 예시

default_user = {

    "kakao_id": "123456",

    "nickname": "홍길동",

    "credit": 1000,  # 기본 크레딧

    "won":0,

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

    "placements": []

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



    # DB에서 사용자 확인

    user = users_collection.find_one({"kakao_id": kakao_id})

    if not user:

        users_collection.insert_one({

            "kakao_id": kakao_id,

            "nickname": nickname,

            "credit": 1000,

            "won":0,

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

            "placements": []

        })



    session['kakao_id'] = kakao_id

    return jsonify({"redirect_url": url_for('home')})



@app.route('/home')

def home():

    kakao_id = session.get('kakao_id')

    if not kakao_id:

        return redirect(url_for('login'))



    user = users_collection.find_one({"kakao_id": kakao_id})

    if not user:

        return redirect(url_for('login'))



    # 최신 daysElapsed 계산 & DB 업데이트

    updated_placements = []

    for idx, p in enumerate(user.get('placements', [])):

        # p['plantedAt'] 는 datetime 객체

        planted = p['plantedAt']

        days = (datetime.utcnow().date() - planted.date()).days



        # DB 에도 daysElapsed 필드 갱신

        users_collection.update_one(

            { "kakao_id": kakao_id },

            { "$set": { f"placements.{idx}.daysElapsed": days } }

        )



        # 템플릿에 넘길 때도 문자열로 만들어 줌

        updated_placements.append({

            "seedId": p['seedId'],

            "x": p['x'],

            "y": p['y'],

            "plantedAt": planted.strftime('%Y-%m-%d %H:%M:%S'),

            "daysElapsed": days

        })



    return render_template(

        'home.html',

        nickname=user['nickname'],

        seeds=user['seeds'],

        credit=user['credit'],

        placements=updated_placements,

        food=user['food']

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
        {"id": "carrot", "name": "당근 씨앗", "price": 50, "count": 0, "image": "carrot_round.png"},
        {"id": "tomato", "name": "토마토 씨앗", "price": 50, "count": 0, "image": "tomato_round.png"},
        {"id": "basil", "name": "바질 씨앗", "price": 50, "count": 0, "image": "basil_round.png"},
        {"id": "potato", "name": "감자 씨앗", "price": 50, "count": 0, "image": "potato_round.png"},
        {"id": "Eggplant", "name": "가지 씨앗", "price": 50, "count": 0, "image": "egg_plant_round.png"},
        {"id": "redpepper", "name": "고추 씨앗", "price": 50, "count": 0, "image": "red_pepper_round.png"},
        {"id": "paprika", "name": "파프리카 씨앗", "price": 50, "count": 0, "image": "paprika_round.png"},
        {"id": "grape", "name": "포도 씨앗", "price": 100, "count": 0, "image": "grape_round.png"}
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
        "carrot": 50,
        "tomato": 50,
        "basil": 50,
        "potato": 50,
        "Eggplant": 50,
        "redpepper": 50,
        "paprika": 50,
        "grape": 100
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


@app.route('/my')
def my():
    if 'kakao_id' not in session:
        return redirect(url_for('login'))

    kakao_id = session['kakao_id']
    user = users_collection.find_one({"kakao_id": kakao_id})

    if not user:
        return redirect(url_for('login'))

    return render_template(
        'my.html',
        nickname=user['nickname'],
        credit=user['credit'],
        won=user['won'],
        potato_count=user['food']['potato']  
    )

if __name__ == '__main__':
    app.run(debug=True)
