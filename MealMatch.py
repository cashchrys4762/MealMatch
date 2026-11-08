from __future__ import annotations

import html  
import mimetypes  
import random  # สุ่มเลือกเมนู
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # เปิดเว็บเซิร์ฟเวอร์
from pathlib import Path  # จัดการที่อยู่โฟลเดอร์/ไฟล์
from typing import Any  # ชนิดข้อมูล
from urllib.parse import parse_qs, unquote  # อ่านค่าฟอร์ม และ URL

#เมนูอาหารทั้งหมด ราคา แคลอรี รูป
MENUS: list[dict[str, Any]] = [
    # ประหยัด < 40 บาท
    {
        "name": "ไข่ต้ม",
        "price": 16,
        "calories": 160,
        "category": "ประหยัด",
        "image": "seven-boiled-eggs-two-160.jpg",
    },
    {
        "name": "โอนิกิริแซลมอนย่างซีอิ๊ว",
        "price": 25,
        "calories": 210,
        "category": "ประหยัด",
        "image": "onigiri-soy-grilled-salmon-calories.jpg",
    },
    {
        "name": "ขนมปังช็อกโกแลตชิพเลอแปง",
        "price": 32,
        "calories": 360,
        "category": "ประหยัด",
        "image": "le-pain-chocolate-chip-bread-calories.jpg",
    },
    {
        "name": "ข้าวผัดหมู",
        "price": 35,
        "calories": 620,
        "category": "ประหยัด",
        "image": "pork-fried-rice-calories.jpg",
    },
    {
        "name": "แซนด์วิชครัวซองต์แฮมชีส",
        "price": 39,
        "calories": 460,
        "category": "ประหยัด",
        "image": "croissant-ham-cheese-sandwich-calories.jpg",
    },
    # ทั่วไป 40–100 บาท
    {
        "name": "ข้าวราดลาบไก่",
        "price": 45,
        "calories": 365,
        "category": "ทั่วไป",
        "image": "khao-rad-larb-gai-calories.jpg",
    },
    {
        "name": "สุกี้น้ำหมู",
        "price": 50,
        "calories": 310,
        "category": "ทั่วไป",
        "image": "suki-nam-pork-calories.jpg",
    },
    {
        "name": "ข้าวมันไก่ เนื้อ+หนัง",
        "price": 45,
        "calories": 660,
        "category": "ทั่วไป",
        "image": "khao-man-gai-meat-skin-calories.jpg",
    },
    {
        "name": "ก๋วยเตี๋ยวต้มยำน้ำใส",
        "price": 50,
        "calories": 570,
        "category": "ทั่วไป",
        "image": "guay-tiew-tom-yum-nam-sai-calories.jpg",
    },
    {
        "name": "กะเพราหมูกรอบไข่ดาว",
        "price": 55,
        "calories": 879,
        "category": "ทั่วไป",
        "image": "krapow-moo-krob-kai-dao-calories.jpg",
    },
    # ไฮคลาส > 100 บาท
    {
        "name": "ทงโคะสึ โชยุ ราเมน",
        "price": 129,
        "calories": 800,
        "category": "ไฮคลาส",
        "image": "tonkotsu-shoyu-ramen-calories.jpg",
    },
    {
        "name": "สลัดบาร์",
        "price": 159,
        "calories": 600,
        "category": "ไฮคลาส",
        "image": "salad-bar-calories.jpg",
    },
    {
        "name": "สเต๊กปลาย่าง",
        "price": 149,
        "calories": 300,
        "category": "ไฮคลาส",
        "image": "grilled-fish-steak-calories.jpg",
    },
    {
        "name": "อาซาอิโบวล์",
        "price": 139,
        "calories": 260,
        "category": "ไฮคลาส",
        "image": "acai-bowl-calories.jpg",
    },
    {
        "name": "พิซซ่าถาดเล็ก",
        "price": 119,
        "calories": 450,
        "category": "ไฮคลาส",
        "image": "small-pizza-calories.jpg",
    },
]


#คำนวณ BMI จากน้ำหนักและส่วนสูง
def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    #แปลงส่วนสูงจากเซนติเมตรเป็นเมตร
    height_m = height_cm / 100
    #สูตร BMI = น้ำหนัก / (ส่วนสูงเป็นเมตร)^2
    return weight_kg / (height_m ** 2)


#แปลง BMI เป็นหุ่น
def get_bmi_status(bmi: float) -> str:
    #น้อยกว่า 18.5 ถือว่าผอม
    if bmi < 18.5:
        return "ผอม"
    #18.5 ถึงน้อยกว่า 23 ถือว่าสมส่วน
    if bmi < 23:
        return "สมส่วน"
    #23 ขึ้นไปถือว่าท้วม
    return "ท้วม"


#ข้อความแนะนำอาหาร BMI
def get_bmi_advice(status: str) -> str:
    #เก็บคำแนะนำของแต่ละสถานะไว้ในพจนานุกรม
    advice = {
        "ผอม": "เน้นโปรตีนและพลังงาน",
        "สมส่วน": "ทานอาหารให้ครบ 5 หมู่ ลดของทอดมันหวาน",
        "ท้วม": "เลือกอาหารแคลต่ำ เน้นผัก โปรตีน งดของทอดมันหวาน",
    }
    #คืนค่าคำแนะนำตามสถานะที่ส่งมา
    return advice[status]


#คำนวณ BMR ด้วยสูตร Mifflin-St Jeor
def calculate_bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    #คำนวณค่าพื้นฐานก่อนจะแยกตามเพศ
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    #ชาย + 5
    if sex == "ชาย":
        return base + 5
    #หญิง - 161
    return base - 161


#กรองเมนูตามช่วงงบประมาณที่ผู้ใช้กรอก
def filter_menus_by_budget(budget: float) -> list[dict[str, Any]]:
    #งบน้อยกว่า 40 บาท เลือกเมนูประหยัด
    if budget < 40:
        return [m for m in MENUS if m["price"] < 40]
    #งบ 40 ถึง 100 บาท เลือกเมนูทั่วไป
    if budget <= 100:
        return [m for m in MENUS if 40 <= m["price"] <= 100]
    #งบมากกว่า 100 บาท เลือกเมนูไฮคลาส
    return [m for m in MENUS if m["price"] > 100]


#สุ่มเมนู 1 รายการจากงบที่กำหนด
def pick_random_menu(budget: float) -> dict[str, Any] | None:
    #ดึงเมนูในช่วงงบ
    choices = filter_menus_by_budget(budget)
   
    if not choices:
        return None
    #สุ่มเลือกเมนู 1 จาน
    return random.choice(choices)


#ประเมินแคลอรีของเมนูว่าต่ำ พอดี หรือสูง
def assess_calories(calories: float) -> str:
    #แคลอรีต่ำกว่า 350
    if calories < 350:
        return "แคลต่ำ เหมาะควบคุมน้ำหนัก"
    #แคลอรีอยู่ระหว่าง 350 ถึง 650
    if calories <= 650:
        return "แคลพอดีสำหรับมื้อหลัก"
    #แคลอรีสูงกว่า 650
    return "แคลสูง ควรระวังถ้าต้องการลดน้ำหนัก"


#กำหนดตัวเลือกเป้าหมายน้ำหนัก
GOALS = ("ลดน้ำหนัก", "คงน้ำหนัก", "เพิ่มน้ำหนัก")
#กำหนดตัวเลือกระดับกิจกรรม
ACTIVITIES = (
    "ไม่ออกกำลังกาย",
    "เบา",
    "ปานกลาง",
    "หนัก",
    "หนักมาก",
)
#ตัวคูณกิจกรรมสำหรับคำนวณ TDEE
ACTIVITY_FACTOR = {
    "ไม่ออกกำลังกาย": 1.2,
    "เบา": 1.375,
    "ปานกลาง": 1.55,
    "หนัก": 1.725,
    "หนักมาก": 1.9,
}


#คำนวณ TDEE โดยนำ BMR คูณกับตัวคูณกิจกรรม
def calculate_tdee(bmr: float, activity: str) -> float:
    return bmr * ACTIVITY_FACTOR[activity]


#คำนวณแคลอรีแนะนำต่อวันตามเป้าหมาย
def daily_calorie_target(tdee: float, goal: str, sex: str, bmr: float) -> int:
    #ลดน้ำหนักให้ขาดดุล 500 กิโลแคลอรี
    if goal == "ลดน้ำหนัก":
        target = tdee - 500
    #เพิ่มน้ำหนักให้เกินดุล 500 กิโลแคลอรี
    elif goal == "เพิ่มน้ำหนัก":
        target = tdee + 500
    #คงน้ำหนักใช้ค่า TDEE ตามปกติ
    else:
        target = tdee
    #กำหนดค่าขั้นต่ำไม่ให้ต่ำเกินไป
    minimum = max(bmr, 1500 if sex == "ชาย" else 1200)
    #ถ้าลดน้ำหนักต้องไม่ต่ำกว่าค่าขั้นต่ำ
    if goal == "ลดน้ำหนัก":
        target = max(target, minimum)
    #ปัดเศษเป็นจำนวนเต็มแล้วคืนค่า
    return int(round(target))


#คำนวณแคลอรีแนะนำต่อมื้อ โดยหารแคลอรีต่อวันด้วย 3
def meal_calorie_target(daily_kcal: float) -> int:
    return int(round(daily_kcal / 3))


#เตือนเมื่อเป้าหมายสวนทางกับเกณฑ์ BMI
def goal_warning(status: str, goal: str) -> str | None:
    #กรณีผอมแต่เลือกลดน้ำหนัก
    if status == "ผอม" and goal == "ลดน้ำหนัก":
        return (
            "BMI อยู่ในเกณฑ์ผอม การลดน้ำหนักอาจไม่เหมาะสม "
            "ควรเน้นโปรตีนและพลังงานให้พอ"
        )
    #กรณีท้วมแต่เลือกเพิ่มน้ำหนัก
    if status == "ท้วม" and goal == "เพิ่มน้ำหนัก":
        return "BMI อยู่ในเกณฑ์ท้วม การเพิ่มน้ำหนักอาจทำให้น้ำหนักสูงขึ้นอีก"
    #กรณีอื่นไม่ต้องเตือน
    return None


def assess_goal_fit(calories: float, goal: str) -> str:

    if goal == "ลดน้ำหนัก":
        if calories < 350:
            return "เหมาะกับเป้าหมายลดน้ำหนัก"
        if calories <= 650:
            return "พอใช้ได้ แต่ถ้าลดน้ำหนักควรคุมปริมาณ"
        return "ไม่เหมาะกับเป้าหมายลดน้ำหนัก เพราะแคลอรีสูง"
    if goal == "คงน้ำหนัก":
        if calories < 350:
            return "แคลต่ำไปเล็กน้อยสำหรับเป้าหมายคงน้ำหนัก"
        if calories <= 650:
            return "เหมาะกับเป้าหมายคงน้ำหนัก"
        return "แคลสูงไปสำหรับเป้าหมายคงน้ำหนัก ควรลดมื้ออื่นวันนี้"
    if calories < 350:
        return "แคลต่ำไปสำหรับเป้าหมายเพิ่มน้ำหนัก"
    if calories <= 650:
        return "พอใช้ได้ ถ้าเพิ่มน้ำหนักอาจเติมพลังงานเพิ่ม"
    return "เหมาะกับเป้าหมายเพิ่มน้ำหนัก"


#เลือกเมนูในช่วงงบตามเป้าหมายแคลอรี
def list_menus_for_meal(
    budget: float,
    daily_kcal: float,
    goal: str,
) -> list[dict[str, Any]]:
    #ดึงเมนูตามงบก่อน
    choices = filter_menus_by_budget(budget)
    #หาค่าแคลอรีสูงสุดที่แนะนำต่อมื้อ
    limit = meal_calorie_target(daily_kcal)
    #ถ้าเพิ่มน้ำหนักให้เลือกเมนูแคลสูง
    if goal == "เพิ่มน้ำหนัก":
        high = [menu for menu in choices if menu["calories"] >= limit]
        if high:
            #เรียงจากแคลอรีมากไปน้อย
            return sorted(high, key=lambda menu: menu["calories"], reverse=True)
        #ถ้าไม่มีเมนูถึงเป้า ให้เอาครึ่งบนที่แคลสูงสุด
        ranked = sorted(choices, key=lambda menu: menu["calories"], reverse=True)
        count = max(2, (len(ranked) + 1) // 2)
        return ranked[:count]
    #ลดน้ำหนักหรือคงน้ำหนัก เลือกเมนูที่แคลไม่เกินเป้า
    return [menu for menu in choices if menu["calories"] <= limit]


#สุ่มเลือกเมนู 1 จานจากรายการที่ผ่านเกณฑ์
def pick_menu_for_goal(
    budget: float,
    goal: str,
    daily_kcal: float,
    rng: random.Random | None = None,
) -> dict[str, Any] | None:
    choices = list_menus_for_meal(budget, daily_kcal, goal)
    #ถ้าไม่มีเมนูให้คืนค่าว่าง
    if not choices:
        return None
    chooser = rng if rng is not None else random
    #สุ่มเลือก 1 เมนู
    return chooser.choice(choices)


#รับค่าทศนิยมจากผู้ใช้จนกว่าจะกรอกถูก
def read_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            #แปลงข้อความเป็นตัวเลขทศนิยม
            value = float(raw)
            return value
        except ValueError:
            print("  → กรุณากรอกเป็นตัวเลข")


#รับค่าจำนวนเต็มจากผู้ใช้จนกว่าจะกรอกถูก
def read_int(prompt: str) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            #แปลงข้อความเป็นจำนวนเต็ม
            return int(raw)
        except ValueError:
            print("  → กรุณากรอกเป็นจำนวนเต็ม")


#รับค่าเพศจากผู้ใช้ รับได้เฉพาะชายหรือหญิง
def read_sex() -> str:
    while True:
        raw = input("เพศ (ชาย/หญิง): ").strip()
        if raw in ("ชาย", "หญิง"):
            return raw
        print("  → กรุณาพิมพ์เฉพาะคำว่า ชาย หรือ หญิง")


#รับค่าระดับกิจกรรมจากผู้ใช้
def read_activity() -> str:
    print("ระดับกิจกรรม:")
    print("  1) ไม่ออกกำลังกาย")
    print("  2) เบา (ออกกำลังกาย 1-3 ครั้ง/สัปดาห์)")
    print("  3) ปานกลาง (ออกกำลังกาย 3-5 ครั้ง/สัปดาห์)")
    print("  4) หนัก (ออกกำลังกาย 6-7 ครั้ง/สัปดาห์)")
    print("  5) หนักมาก")
    aliases = {
        "1": "ไม่ออกกำลังกาย",
        "2": "เบา",
        "3": "ปานกลาง",
        "4": "หนัก",
        "5": "หนักมาก",
        "ไม่ออกกำลังกาย": "ไม่ออกกำลังกาย",
        "เบา": "เบา",
        "ปานกลาง": "ปานกลาง",
        "หนัก": "หนัก",
        "หนักมาก": "หนักมาก",
    }
    while True:
        raw = input("เลือกระดับกิจกรรม (1-5): ").strip()
        if raw in aliases:
            return aliases[raw]
        print("  → กรุณาเลือก 1 ถึง 5")


#รับค่าเป้าหมายน้ำหนักจากผู้ใช้
def read_goal() -> str:
    print("เป้าหมายน้ำหนัก:")
    print("  1) ลดน้ำหนัก")
    print("  2) คงน้ำหนัก")
    print("  3) เพิ่มน้ำหนัก")
    aliases = {
        "1": "ลดน้ำหนัก",
        "2": "คงน้ำหนัก",
        "3": "เพิ่มน้ำหนัก",
        "ลด": "ลดน้ำหนัก",
        "คง": "คงน้ำหนัก",
        "เพิ่ม": "เพิ่มน้ำหนัก",
        "ลดน้ำหนัก": "ลดน้ำหนัก",
        "คงน้ำหนัก": "คงน้ำหนัก",
        "เพิ่มน้ำหนัก": "เพิ่มน้ำหนัก",
    }
    while True:
        raw = input("เลือกเป้าหมาย (1/2/3): ").strip()
        if raw in aliases:
            return aliases[raw]
        print("  → กรุณาเลือก 1 ลดน้ำหนัก, 2 คงน้ำหนัก หรือ 3 เพิ่มน้ำหนัก")


#รับข้อมูลผู้ใช้แล้วตรวจสอบความถูกต้อง
def get_user_data() -> dict[str, Any]:
    while True:
        print("\n--- รับข้อมูลผู้ใช้ ---")
        #รับค่าทีละช่อง
        sex = read_sex()
        age = read_int("อายุ (ปี): ")
        weight = read_float("น้ำหนัก (กก.): ")
        height = read_float("ส่วนสูง (ซม.): ")
        goal = read_goal()
        activity = read_activity()
        budget = read_float("งบประมาณมื้อนี้ (บาท): ")

        #เก็บข้อความผิดพลาดไว้ในลิสต์
        errors: list[str] = []
        if not 10 <= age <= 100:
            errors.append("อายุต้องอยู่ระหว่าง 10–100 ปี")
        if not 20 <= weight <= 300:
            errors.append("น้ำหนักต้องอยู่ระหว่าง 20–300 กก.")
        if not 50 <= height <= 250:
            errors.append("ส่วนสูงต้องอยู่ระหว่าง 50–250 ซม.")
        if goal not in GOALS:
            errors.append("กรุณาเลือกเป้าหมายเป็น ลดน้ำหนัก คงน้ำหนัก หรือ เพิ่มน้ำหนัก")
        if activity not in ACTIVITIES:
            errors.append("กรุณาเลือกระดับกิจกรรม")
        if budget < 0:
            errors.append("งบประมาณต้องไม่ติดลบ")

        #ถ้ามีข้อผิดพลาดให้แจ้งแล้วรับใหม่
        if errors:
            print("\nข้อมูลไม่ถูกต้อง:")
            for err in errors:
                print(f"  • {err}")
            print("กรุณากรอกข้อมูลใหม่")
            continue

        #ข้อมูลถูกต้องแล้วคืนค่าเป็นพจนานุกรม
        return {
            "sex": sex,
            "age": age,
            "weight": weight,
            "height": height,
            "goal": goal,
            "activity": activity,
            "budget": budget,
        }


#คำนวณและแสดงผลสุขภาพของผู้ใช้
def show_health_result(data: dict[str, Any]) -> tuple[float, str, float, int]:
    #คำนวณ BMI และสถานะ
    bmi = calculate_bmi(data["weight"], data["height"])
    status = get_bmi_status(bmi)
    advice = get_bmi_advice(status)
    #คำนวณ BMR TDEE และแคลอรีแนะนำ
    bmr = calculate_bmr(data["sex"], data["weight"], data["height"], data["age"])
    tdee = calculate_tdee(bmr, data["activity"])
    daily = daily_calorie_target(tdee, data["goal"], data["sex"], bmr)
    meal = meal_calorie_target(daily)
    warning = goal_warning(status, data["goal"])

    print("\n=== ผลการคำนวณอัตโนมัติ ===")
    print(f"เป้าหมาย: {data['goal']}")
    print(f"ระดับกิจกรรม: {data['activity']}")
    print(f"ดัชนีมวลกาย (BMI): {bmi:.2f} — สถานะ: {status}")
    print(f"คำแนะนำอาหาร: {advice}")
    if warning:
        print(f"ข้อควรระวัง: {warning}")
    print(f"พลังงานพื้นฐาน/วัน (BMR) ≈ {bmr:.0f} kcal")
    print(f"พลังงานที่ใช้ต่อวัน (TDEE) ≈ {tdee:.0f} kcal")
    print(f"แคลอรีแนะนำต่อวัน ≈ {daily} kcal")
    print(f"แคลอรีแนะนำต่อมื้อ ≈ {meal} kcal")
    return bmi, status, bmr, daily


#แสดงรายการเมนูที่แนะนำ
def show_menu_result(menus: list[dict[str, Any]]) -> None:
    print("\n=== เมนูในช่วงงบที่แคลไม่เกินเป้า ===")
    if not menus:
        print("ไม่มีเมนูในงบนี้ที่แคลอรีไม่เกินเป้าต่อมื้อ")
        return
    for menu in menus:
        print(f"- {menu['name']} | {menu['price']} บาท | {menu['calories']} kcal")


#แสดงสรุปผลทั้งหมด
def show_summary(
    data: dict[str, Any],
    bmi: float,
    status: str,
    bmr: float,
    daily: int,
    menus: list[dict[str, Any]],
) -> None:
    tdee = calculate_tdee(bmr, data["activity"])
    meal = meal_calorie_target(daily)
    print("\n========== สรุปผล MealMatch ==========")
    print(
        f"เพศ {data['sex']} | อายุ {data['age']} ปี | "
        f"น้ำหนัก {data['weight']} กก. | ส่วนสูง {data['height']} ซม."
    )
    print(f"เป้าหมาย: {data['goal']} | กิจกรรม: {data['activity']}")
    print(f"งบประมาณมื้อนี้: {data['budget']} บาท")
    print(f"BMI: {bmi:.2f} ({status}) — {get_bmi_advice(status)}")
    warning = goal_warning(status, data["goal"])
    if warning:
        print(f"ข้อควรระวัง: {warning}")
    print(f"BMR ≈ {bmr:.0f} kcal | TDEE ≈ {tdee:.0f} kcal")
    print(f"แคลอรีแนะนำต่อวัน ≈ {daily} kcal")
    print(f"แคลอรีแนะนำต่อมื้อ ≈ {meal} kcal")
    if menus:
        print("เมนูแนะนำ:")
        for menu in menus:
            print(
                f"  - {menu['name']} | {menu['price']} บาท | "
                f"{menu['calories']} kcal"
            )
    else:
        print("ไม่มีเมนูในงบนี้ที่แคลอรีไม่เกินเป้าต่อมื้อ")
    print("======================================")


#ฟังก์ชันหลักแบบรับค่าทางเทอร์มินัล
def cli_main() -> None:
    print("=" * 40)
    print("  MealMatch — แนะนำเมนูตามร่างกายและงบ")
    print("=" * 40)
    print("จัดทำโดย")
    print("  นางสาวกุลธิดา อินต๊ะวงค์")
    print("  นางสาวจิราภรณ์ เกตุแก้ว")
    print("นำเสนอ")
    print("  อาจารย์ เบญญาทิพย์ ศรีเจริญ")
    print("  สาขาวิชาวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์")
    print("  คณะวิศวกรรมศาสตร์")
    print("  มหาวิทยาลัยหอการค้าไทย")

    data = get_user_data()
    bmi, status, bmr, daily = show_health_result(data)

    while True:
        menus = list_menus_for_meal(data["budget"], daily, data["goal"])
        show_menu_result(menus)
        show_summary(data, bmi, status, bmr, daily, menus)

        print("\nเลือกขั้นตอนถัดไป:")
        print("  1) สุ่มเมนูใหม่")
        print("  2) กรอกข้อมูลใหม่")
        print("  3) จบโปรแกรม")
        while True:
            choice = input("เลือก (1/2/3): ").strip()
            if choice in ("1", "2", "3"):
                break
            print("  → กรุณาเลือก 1, 2 หรือ 3")

        if choice == "1":
            continue
        if choice == "2":
            data = get_user_data()
            bmi, status, bmr, daily = show_health_result(data)
            continue
        break

    print("\nขอบคุณที่ใช้ MealMatch")



#กำหนดโฟลเดอร์รูปเมนูและโลโก้
IMAGE_ROOT = Path(__file__).resolve().parent / "ภาพอาหาร"
STATIC_ROOT = Path(__file__).resolve().parent / "static"
#เก็บชื่อไฟล์รูปที่อนุญาตให้เปิดได้
KNOWN_IMAGES = {m["image"] for m in MENUS}


#ค้นหาไฟล์รูปเมนูจากชื่อไฟล์
def find_image(filename: str) -> Path | None:
    if filename not in KNOWN_IMAGES:
        return None
    for path in IMAGE_ROOT.rglob(filename):
        if path.is_file():
            return path
    return None


#ค้นหาไฟล์ในโฟลเดอร์ static เช่นโลโก้
def find_static(filename: str) -> Path | None:
    name = Path(filename).name
    if name != filename.replace("\\", "/").split("/")[-1]:
        return None
    path = STATIC_ROOT / name
    if path.is_file():
        return path
    return None

#เก็บ CSS ของหน้าเว็บไว้ในตัวแปรข้อความ
PAGE_CSS = """
:root { --green:#1f7a4d; --green-dark:#165c3a; --leaf:#e8f5ee; --ink:#1c1917; --muted:#6b635c; --line:#eadfd3; --card:#fff; }
* { box-sizing:border-box; }
body { margin:0; font-family:"Mali","Leelawadee UI",sans-serif; color:var(--ink);
  background: radial-gradient(1200px 500px at 10% -10%, #ffe8c7 0%, transparent 50%),
              radial-gradient(900px 400px at 100% 0%, #d9f3e4 0%, transparent 46%), #f6efe6; }
main { max-width:860px; margin:28px auto 48px; background:var(--card); padding:28px 28px 24px;
  border-radius:28px; box-shadow:0 18px 50px rgba(80,50,20,.08); }
.brand { display:flex; align-items:center; gap:14px; margin-bottom:22px; }
.logo { width:64px; height:64px; border-radius:50%; object-fit:cover; display:block;
  box-shadow:0 6px 16px rgba(80,50,20,.12); background:#fff; }
h1 { margin:0; font-size:30px; letter-spacing:-.02em; }
label { display:block; margin:0 0 6px; font-weight:600; font-size:14px; }
input, select { width:100%; padding:12px 14px; border:1px solid var(--line); border-radius:14px;
  font-size:16px; background:#fffaf4; font-family:inherit; }
input:focus, select:focus { outline:2px solid #b7e3c8; border-color:var(--green); }
.row { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:14px; }
.span { margin-bottom:14px; }
.actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:8px; }
button, .btn { border:0; border-radius:999px; padding:12px 20px; font-size:16px; cursor:pointer;
  font-family:inherit; text-decoration:none; display:inline-flex; align-items:center; }
button.primary { background:var(--green); color:#fff; box-shadow:0 8px 18px rgba(31,122,77,.25); }
button.primary:hover { background:var(--green-dark); }
.btn.secondary, button.secondary { background:#f3ece4; color:var(--ink); }
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:22px; }
.stat { background:var(--leaf); border-radius:16px; padding:14px 12px; text-align:center; }
.stat span { display:block; color:var(--muted); font-size:12px; margin-bottom:4px; }
.stat strong { font-size:20px; }
.gallery { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; margin-top:18px; }
.dish { background:#fff; border:1px solid var(--line); border-radius:20px; overflow:hidden;
  box-shadow:0 8px 20px rgba(80,50,20,.05); }
.dish h2 { margin:0; font-size:18px; }
.meta { padding:12px 14px 16px; }
.pills { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
.pill { background:#fff4e5; color:#8a4b12; border-radius:999px; padding:4px 10px; font-size:13px; font-weight:600; }
.pill.kcal { background:var(--leaf); color:var(--green-dark); }
.photo { width:100%; aspect-ratio:1/1; object-fit:cover; display:block; }
.err { background:#fdecea; color:#8a1f11; padding:12px 14px; border-radius:14px; margin-top:16px; }
.empty { margin-top:18px; padding:20px; text-align:center; background:#fffaf4; border-radius:16px; color:var(--muted); }
.credits { margin-top:28px; padding-top:16px; border-top:1px solid var(--line); color:var(--muted);
  font-size:14px; line-height:1.65; display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.credits .label { font-weight:700; color:var(--ink); }
@media (max-width:700px) {
  main { margin:0; border-radius:0; }
  .row, .stats, .gallery, .credits { grid-template-columns:1fr; }
}
"""


#รับข้อมูลจากฟอร์มเว็บแล้วคำนวณผลลัพธ์
def handle_form(fields: dict[str, str]) -> dict[str, Any]:
    #เตรียมลิสต์เก็บข้อผิดพลาด
    errors: list[str] = []
    #อ่านค่าจากฟอร์ม
    sex = fields.get("sex", "").strip()
    goal = fields.get("goal", "").strip()
    activity = fields.get("activity", "ปานกลาง").strip() or "ปานกลาง"
    try:
        age = int(fields.get("age", ""))
    except ValueError:
        age = -1
        errors.append("อายุต้องเป็นจำนวนเต็ม")
    try:
        weight = float(fields.get("weight", ""))
    except ValueError:
        weight = -1
        errors.append("น้ำหนักต้องเป็นตัวเลข")
    try:
        height = float(fields.get("height", ""))
    except ValueError:
        height = -1
        errors.append("ส่วนสูงต้องเป็นตัวเลข")
    try:
        budget = float(fields.get("budget", ""))
    except ValueError:
        budget = -1
        errors.append("งบประมาณต้องเป็นตัวเลข")

    if sex not in ("ชาย", "หญิง"):
        errors.append("เลือกเพศชายหรือหญิง")
    if goal not in GOALS:
        errors.append("เลือกเป้าหมาย ลด คง หรือเพิ่มน้ำหนัก")
    if activity not in ACTIVITIES:
        errors.append("เลือกระดับกิจกรรม")
    if age != -1 and not 10 <= age <= 100:
        errors.append("อายุต้องอยู่ระหว่าง 10-100 ปี")
    if weight != -1 and not 20 <= weight <= 300:
        errors.append("น้ำหนักต้องอยู่ระหว่าง 20-300 กก.")
    if height != -1 and not 50 <= height <= 250:
        errors.append("ส่วนสูงต้องอยู่ระหว่าง 50-250 ซม.")
    if budget != -1 and budget < 0:
        errors.append("งบประมาณต้องไม่ติดลบ")

    #ถ้าข้อมูลผิดให้ส่งข้อผิดพลาดกลับไปแสดง
    if errors:
        return {"ok": False, "errors": errors, "fields": fields}

    #คำนวณค่าสุขภาพและเลือกเมนู
    bmi = calculate_bmi(weight, height)
    status = get_bmi_status(bmi)
    bmr = calculate_bmr(sex, weight, height, age)
    tdee = calculate_tdee(bmr, activity)
    daily = daily_calorie_target(tdee, goal, sex, bmr)
    target = meal_calorie_target(daily)
    warning = goal_warning(status, goal)
    menus = list_menus_for_meal(budget, daily, goal)
    menu = menus[0] if menus else None
    #คืนผลลัพธ์ทั้งหมดให้หน้าเว็บ
    return {
        "ok": True,
        "errors": [],
        "fields": fields,
        "sex": sex,
        "age": age,
        "weight": weight,
        "height": height,
        "goal": goal,
        "activity": activity,
        "budget": budget,
        "tdee": tdee,
        "daily": daily,
        "bmi": bmi,
        "status": status,
        "advice": get_bmi_advice(status),
        "bmr": bmr,
        "target": target,
        "warning": warning,
        "menu": menu,
        "menus": menus,
    }


#สร้างตัวเลือกในเมนู dropdown ของหน้าเว็บ
def _opt(current: str, value: str, label: str) -> str:
    selected = " selected" if current == value else ""
    return f'<option value="{html.escape(value)}"{selected}>{html.escape(label)}</option>'


#สร้างหน้า HTML ของเว็บ MealMatch
def render_page(result: dict[str, Any] | None = None) -> bytes:
    #อ่านค่าเดิมในฟอร์มเพื่อแสดงค้างไว้
    fields = (result or {}).get("fields") or {}
    sex = fields.get("sex", "ชาย")
    goal = fields.get("goal", "คงน้ำหนัก")
    activity = fields.get("activity", "ปานกลาง")
    age = html.escape(fields.get("age", ""))
    weight = html.escape(fields.get("weight", ""))
    height = html.escape(fields.get("height", ""))
    budget = html.escape(fields.get("budget", ""))

    extra = ""
    if result and not result["ok"]:
        items = "".join(f"<li>{html.escape(e)}</li>" for e in result["errors"])
        extra += f'<div class="err"><strong>ข้อมูลไม่ถูกต้อง</strong><ul>{items}</ul></div>'
    if result and result["ok"]:
        extra += (
            '<div class="stats">'
            f'<div class="stat"><span>BMI</span><strong>{result["bmi"]:.2f}</strong></div>'
            f'<div class="stat"><span>BMR</span><strong>{result["bmr"]:.0f}</strong></div>'
            f'<div class="stat"><span>ต่อวัน</span><strong>{result["daily"]}</strong></div>'
            f'<div class="stat"><span>ต่อมื้อ</span><strong>{result["target"]}</strong></div>'
            "</div>"
        )
        menus = result.get("menus") or []
        if not menus:
            extra += '<div class="empty">ไม่มีเมนูในงบนี้ที่ตรงกับเป้าหมายแคลอรี</div>'
        else:
            extra += '<div class="gallery">'
            for menu in menus:
                extra += (
                    '<article class="dish">'
                    f'<img class="photo" src="/images/{html.escape(menu["image"])}" alt="{html.escape(menu["name"])}"/>'
                    '<div class="meta">'
                    f"<h2>{html.escape(menu['name'])}</h2>"
                    '<div class="pills">'
                    f'<span class="pill">{menu["price"]} บาท</span>'
                    f'<span class="pill kcal">{menu["calories"]} kcal</span>'
                    "</div></div></article>"
                )
            extra += "</div>"

    page = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>MealMatch</title>
  <link rel="icon" href="/static/logo.jpg"/>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Mali:wght@400;500;600;700&display=swap"/>
  <style>{PAGE_CSS}</style>
</head>
<body>
<main>
  <div class="brand">
    <img class="logo" src="/static/logo.jpg" alt="MealMatch"/>
    <div>
      <h1>MealMatch</h1>
    </div>
  </div>
  <form method="post">
    <div class="row">
      <div>
        <label for="sex">เพศ</label>
        <select id="sex" name="sex">
          {_opt(sex, "ชาย", "ชาย")}
          {_opt(sex, "หญิง", "หญิง")}
        </select>
      </div>
      <div>
        <label for="goal">เป้าหมาย</label>
        <select id="goal" name="goal">
          {_opt(goal, "ลดน้ำหนัก", "ลดน้ำหนัก")}
          {_opt(goal, "คงน้ำหนัก", "คงน้ำหนัก")}
          {_opt(goal, "เพิ่มน้ำหนัก", "เพิ่มน้ำหนัก")}
        </select>
      </div>
    </div>
    <div class="span">
      <label for="activity">ระดับกิจกรรม</label>
      <select id="activity" name="activity">
        {_opt(activity, "ไม่ออกกำลังกาย", "ไม่ออกกำลังกาย")}
        {_opt(activity, "เบา", "ออกกำลังกายเบา 1-3 ครั้ง/สัปดาห์")}
        {_opt(activity, "ปานกลาง", "ออกกำลังกายปานกลาง 3-5 ครั้ง/สัปดาห์")}
        {_opt(activity, "หนัก", "ออกกำลังกายหนัก 6-7 ครั้ง/สัปดาห์")}
        {_opt(activity, "หนักมาก", "ออกกำลังกายหนักมาก")}
      </select>
    </div>
    <div class="row">
      <div>
        <label for="age">อายุ (ปี)</label>
        <input id="age" name="age" inputmode="numeric" value="{age}" required>
      </div>
      <div>
        <label for="budget">งบมื้อนี้ (บาท)</label>
        <input id="budget" name="budget" inputmode="decimal" value="{budget}" required>
      </div>
    </div>
    <div class="row">
      <div>
        <label for="weight">น้ำหนัก (กก.)</label>
        <input id="weight" name="weight" inputmode="decimal" value="{weight}" required>
      </div>
      <div>
        <label for="height">ส่วนสูง (ซม.)</label>
        <input id="height" name="height" inputmode="decimal" value="{height}" required>
      </div>
    </div>
    <div class="actions">
      <button class="primary" type="submit" name="action" value="match">แนะนำเมนู</button>
      <a class="btn secondary" href="/">กรอกใหม่</a>
    </div>
  </form>
  {extra}
  <div class="credits">
    <div>
      <div class="label">จัดทำโดย</div>
      นางสาวกุลธิดา อินต๊ะวงค์<br/>
      นางสาวจิราภรณ์ เกตุแก้ว
    </div>
    <div>
      <div class="label">นำเสนอ</div>
      อาจารย์ เบญญาทิพย์ ศรีเจริญ<br/>
      สาขาวิชาวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์<br/>
      คณะวิศวกรรมศาสตร์<br/>
      มหาวิทยาลัยหอการค้าไทย
    </div>
  </div>
</main>
</body>
</html>
"""
    return page.encode("utf-8")


#คลาสรับส่งข้อมูลเว็บด้วย Python มาตรฐาน
class MealMatchHandler(BaseHTTPRequestHandler):
    #เมื่อผู้ใช้เปิดหน้าหรือขอไฟล์รูป
    def do_GET(self) -> None:
        #ถ้าขอรูปเมนู
        if self.path.startswith("/images/"):
            filename = unquote(self.path.split("/", 2)[-1]).split("?")[0]
            self._send_file(find_image(filename))
            return
        #ถ้าขอไฟล์ static เช่นโลโก้
        if self.path.startswith("/static/"):
            filename = unquote(self.path.split("/", 2)[-1]).split("?")[0]
            self._send_file(find_static(filename))
            return
        #กรณีอื่นส่งหน้าเว็บหลัก
        self._send(render_page())

    #ส่งไฟล์รูปหรือไฟล์อื่นกลับไปยังเบราว์เซอร์
    def _send_file(self, path: Path | None) -> None:
        if path is None:
            self.send_error(404)
            return
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    #เมื่อผู้ใช้กดปุ่มส่งฟอร์ม
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        #อ่านข้อมูลที่ส่งมาจากฟอร์ม
        raw = self.rfile.read(length).decode("utf-8")
        parsed = {k: v[-1] for k, v in parse_qs(raw, keep_blank_values=True).items()}
        #คำนวณแล้วแสดงผลหน้าใหม่
        self._send(render_page(handle_form(parsed)))

    #ส่งข้อความ HTML กลับไปยังเบราว์เซอร์
    def _send(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


#ฟังก์ชันหลักสำหรับเปิดเว็บเซิร์ฟเวอร์
def main() -> None:
    #กำหนดหมายเลขพอร์ตของเว็บ
    port = 8000
    #สร้างเซิร์ฟเวอร์และผูกกับคลาสรับส่งข้อมูล
    server = ThreadingHTTPServer(("127.0.0.1", port), MealMatchHandler)
    print(f"เปิดเว็บที่ http://127.0.0.1:{port}")
    print("กด Ctrl+C เพื่อหยุด")
    #เริ่มทำงานรอรับคำขอจากผู้ใช้
    server.serve_forever()


#ถ้ารันไฟล์นี้โดยตรงให้เปิดเว็บ
if __name__ == "__main__":
    main()
