from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pymysql
from yes2 import connminh   # kết nối MySQL riêng

app = Flask(__name__)
CORS(app)

# ================================================
#  TẠO BẢNG SQL (CHẠY TỰ ĐỘNG 1 LẦN)
# ================================================
try:
    conn = connminh()
    cursor = conn.cursor()

    # Bảng thiết bị
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            status TINYINT DEFAULT 0
        )
    """)

    # Bảng lịch sử
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS histories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            history VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Ensure created_at column exists (for older table versions that lack it)
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = (SELECT DATABASE()) AND TABLE_NAME = %s AND COLUMN_NAME = %s", ('histories', 'created_at'))
    has_created_at = cursor.fetchone()[0]
    if has_created_at == 0:
        cursor.execute("ALTER TABLE histories ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    # Thêm dữ liệu mặc định
    cursor.execute("""
        INSERT INTO devices (name, status)
        SELECT %s, %s
        WHERE NOT EXISTS (SELECT 1 FROM devices WHERE name=%s)
    """, ('light', 0, 'light'))

    cursor.execute("""
        INSERT INTO devices (name, status)
        SELECT %s, %s
        WHERE NOT EXISTS (SELECT 1 FROM devices WHERE name=%s)
    """, ('air_conditioner', 0, 'air_conditioner'))

    conn.commit()
    cursor.close()
    del cursor
    conn.close()
    del conn

except Exception as e:
    print("Lỗi tạo bảng:", e)


# ============================
# Helper: Ghi lịch sử
# ============================
def add_history(text):
    conn = connminh()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO histories (history) VALUES (%s)", (text,))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


# ============================
# Helper: Lấy trạng thái thiết bị
# ============================
def get_device_status(name):
    conn = connminh()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT status FROM devices WHERE name=%s", (name,))
        row = cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

    if row is None:
        return None
    return row[0]


# ============================
# Helper: Update trạng thái thiết bị
# ============================
def update_device_status(name, new_status):
    conn = connminh()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE devices SET status=%s WHERE name=%s", (new_status, name))
        conn.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


# ====================================================
# GET trạng thái đèn
# ====================================================
@app.route("/device/light", methods=["GET"])
def get_light():
    status = get_device_status("light")
    if status is None:
        return jsonify({"error": "Light not found"}), 404

    return jsonify({
        "device": "light",
        "status": "on" if status == 1 else "off"
    })


# ====================================================
# POST bật/tắt đèn
# Body: { "status": "on" } / "off"
# ====================================================
@app.route("/device/light", methods=["POST"])
def set_light():
    data = request.get_json()
    new_status = 1 if data.get("status") == "on" else 0
    update_device_status("light", new_status)

    # GHI LỊCH SỬ
    add_history(f"Đèn đã được {'bật' if new_status == 1 else 'tắt'}")

    return jsonify({
        "message": "Light updated",
        "status": "on" if new_status == 1 else "off"
    })


# ====================================================
# GET trạng thái điều hòa
# ====================================================
@app.route("/device/ac", methods=["GET"])
def get_ac():
    status = get_device_status("air_conditioner")
    if status is None:
        return jsonify({"error": "AC not found"}), 404

    return jsonify({
        "device": "air_conditioner",
        "status": "on" if status == 1 else "off"
    })


# ====================================================
# POST bật/tắt điều hòa
# ====================================================
@app.route("/device/ac", methods=["POST"])
def set_ac():
    data = request.get_json()
    new_status = 1 if data.get("status") == "on" else 0
    update_device_status("air_conditioner", new_status)

    # GHI LỊCH SỬ
    add_history(f"Điều hòa đã được {'bật' if new_status == 1 else 'tắt'}")

    return jsonify({
        "message": "Air conditioner updated",
        "status": "on" if new_status == 1 else "off"
    })


# ====================================================
# API GET lịch sử thay đổi
# ====================================================
@app.route("/history", methods=["GET"])
def history():
    conn = connminh()
    result = []
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT history, created_at FROM histories ORDER BY id DESC")
            rows = cursor.fetchall()
            # rows will be (history, created_at)
            result = [
                {"history": h, "time": t.strftime("%Y-%m-%d %H:%M:%S") if t else None}
                for (h, t) in rows
            ]
        except Exception as e:
            # If created_at column does not exist or other error occurs, fall back to selecting only history
            print("/history: primary query failed, falling back to simple query:", e)
            try:
                cursor.close()
            except Exception:
                pass
            cursor = conn.cursor()
            cursor.execute("SELECT history FROM histories ORDER BY id DESC")
            rows = cursor.fetchall()
            result = [{"history": h[0], "time": None} for h in rows]
        finally:
            try:
                cursor.close()
            except Exception:
                pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return jsonify(result)

@app.route("/")
def index():
    return render_template("index.html")

# ====================================================
# Chạy server
# ====================================================
if __name__ == "__main__":
    app.run(debug=True)
