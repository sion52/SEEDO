from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient

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
    }
}

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
            }
        })

    session['kakao_id'] = kakao_id
    return jsonify({"redirect_url": url_for('home')})
