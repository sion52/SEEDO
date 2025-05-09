from flask import Flask, render_template, request, jsonify, redirect, url_for, session
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

@app.route('/credit')
def credit():
    return render_template('credit.html')

@app.route('/storage')
def storage():
    return render_template('storage.html')

@app.route('/store')
def store():
    seed_data = [
        {"id": "carrot", "name": "당근 씨앗", "price": 50, "count": 0, "image": "carrot.png"},
        {"id": "tomato", "name": "토마토 씨앗", "price": 50, "count": 0, "image": "tomato.png"},
        {"id": "basil", "name": "바질 씨앗", "price": 50, "count": 0, "image": "basil.png"},
        {"id": "potato", "name": "감자 씨앗", "price": 50, "count": 0, "image": "potato.png"},
        {"id": "Eggplant", "name": "가지 씨앗", "price": 50, "count": 0, "image": "Eggplant.png"},
        {"id": "redpepper", "name": "고추 씨앗", "price": 50, "count": 0, "image": "redpepper.png"},
        {"id": "paprika", "name": "파프리카 씨앗", "price": 50, "count": 0, "image": "paprika.png"},
        {"id": "grape", "name": "포도 씨앗", "price": 50, "count": 0, "image": "grape.png"}
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
    total_cost = sum(count * 50 for count in data.values())

    if user['credit'] < total_cost:
        return jsonify({"success": False, "message": "크레딧이 부족합니다."})

    for seed_id, count in data.items():
        users_collection.update_one(
            {"kakao_id": kakao_id},
            {
                "$inc": {
                    f"seeds.{seed_id}": count,
                    "credit": -count * 50
                }
            }
        )

    return jsonify({"success": True})
@app.route('/update_seed_count', methods=['POST'])
def update_seed_count():
    if 'kakao_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."})
    
    kakao_id = session['kakao_id']
    user = users_collection.find_one({"kakao_id": kakao_id})
    if not user:
        return jsonify({"success": False, "message": "사용자 정보가 없습니다."})

    data = request.get_json()
    seed_id = data.get('seedId')
    count = data.get('count')

    if seed_id and count is not None:
        # DB에서 씨앗 수 업데이트
        users_collection.update_one(
            {"kakao_id": kakao_id},
            {"$set": {f"seeds.{seed_id}": count}}
        )
        return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "잘못된 요청"})


@app.route('/my')
def my():
    return render_template('my.html')

if __name__ == '__main__':
    app.run(debug=True)
