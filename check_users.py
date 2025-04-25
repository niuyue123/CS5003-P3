import sqlite3

def check_users():
    try:
        conn = sqlite3.connect('DATABASE-puzzles.db')
        c = conn.cursor()
        
        print("查询users表中的所有用户：")
        c.execute("SELECT id, username, password_hash, created_at FROM users")
        users = c.fetchall()
        
        if not users:
            print("users表中没有数据")
        else:
            print("\nID | 用户名 | 密码哈希 | 创建时间")
            print("-" * 80)
            for user in users:
                print(f"{user[0]} | {user[1]} | {user[2]} | {user[3]}")
                
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_users() 