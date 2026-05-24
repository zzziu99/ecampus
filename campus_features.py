"""
E校园 校园特色功能模块
"""

import random
import time

# ===== 食堂数据 =====
CANTEENS = [
    {"name": "学二餐厅", "location": "学活一层", "campus": "海淀", "type": "基本伙", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
    {"name": "学三餐厅", "location": "学活二层", "campus": "海淀", "type": "风味", "hours": "10:30-13:30, 17:00-19:30"},
    {"name": "民族风味餐厅", "location": "学活三层", "campus": "海淀", "type": "清真", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
    {"name": "学四餐厅", "location": "主校区东南角", "campus": "海淀", "type": "基本伙", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
    {"name": "东快餐厅", "location": "明湖二楼", "campus": "海淀", "type": "风味", "hours": "10:00-13:30, 17:00-19:30"},
    {"name": "明湖餐厅", "location": "明湖三楼", "campus": "海淀", "type": "风味", "hours": "10:00-13:30, 17:00-19:30"},
    {"name": "东区大伙餐厅", "location": "东校区一层东侧", "campus": "海淀", "type": "基本伙", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
    {"name": "东区中快餐厅", "location": "东校区", "campus": "海淀", "type": "风味", "hours": "7:00-9:00, 10:00-13:30, 17:00-19:30"},
    {"name": "东区民族风味餐厅", "location": "东校区", "campus": "海淀", "type": "清真", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
    {"name": "学苑美食厅", "location": "学苑9号楼地下一层", "campus": "海淀", "type": "基本伙", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
    {"name": "学苑风味餐厅", "location": "学苑9号楼", "campus": "海淀", "type": "风味", "hours": "11:00-13:30, 16:00-19:30"},
    {"name": "学苑西餐厅", "location": "学苑", "campus": "海淀", "type": "西餐", "hours": "11:00-13:30, 16:00-19:30"},
    {"name": "学苑民族风味餐厅", "location": "学苑", "campus": "海淀", "type": "清真", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
    {"name": "益民餐厅", "location": "东门外家属区", "campus": "海淀", "type": "大众", "hours": "6:00-14:00, 16:00-21:00"},
    {"name": "红果园餐厅", "location": "校内", "campus": "海淀", "type": "点餐", "hours": "11:00-14:00, 17:00-20:30"},
    {"name": "学子餐厅", "location": "校内", "campus": "威海", "type": "基本伙", "hours": "7:00-13:00, 17:00-19:00"},
    {"name": "风味档口", "location": "校内", "campus": "威海", "type": "风味", "hours": "7:00-20:30"},
    {"name": "红果园餐厅(唐山)", "location": "校内", "campus": "唐山", "type": "基本伙", "hours": "7:00-9:00, 11:00-13:00, 17:00-19:00"},
]

CATEGORIES = ["基本伙", "风味", "清真", "西餐", "点餐", "大众"]
CAMPUSES = ["海淀", "威海", "唐山"]


def recommend_canteen(campus=None, food_type=None):
    """随机推荐食堂"""
    pool = CANTEENS
    if campus:
        pool = [c for c in pool if c["campus"] == campus]
    if food_type:
        pool = [c for c in pool if c["type"] == food_type]

    if not pool:
        pool = CANTEENS

    pick = random.choice(pool)

    now = time.localtime()
    hour = now.tm_hour
    if 6 <= hour < 10:
        meal = "早餐"
    elif 10 <= hour < 14:
        meal = "午餐"
    elif 16 <= hour < 20:
        meal = "晚餐"
    else:
        meal = "非正餐时间"

    return {
        "name": pick["name"],
        "location": pick["location"],
        "campus": pick["campus"],
        "type": pick["type"],
        "hours": pick["hours"],
        "meal": meal,
        "tip": random.choice([
            "今天试试这家吧！",
            "换个口味，去这家看看？",
            "同学推荐这家不错哦～",
            "走起！去吃这家！",
            "别犹豫了，就这家！"
        ])
    }


def get_canteen_stats():
    """食堂统计"""
    return {
        "total": len(CANTEENS),
        "by_campus": {c: len([x for x in CANTEENS if x["campus"] == c]) for c in CAMPUSES},
        "by_type": {t: len([x for x in CANTEENS if x["type"] == t]) for t in CATEGORIES if len([x for x in CANTEENS if x["type"] == t]) > 0}
    }
