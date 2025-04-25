import sqlite3

def check_database():
    try:
        # 连接到数据库
        conn = sqlite3.connect('DATABASE-puzzles.db')
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("数据库中的表:")
        for table in tables:
            table_name = table[0]
            print(f"\n表名: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("列结构:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 获取表中的数据行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"行数: {count}")
            
            # 显示前几行数据
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                print("示例数据:")
                for row in rows:
                    print(f"  {row}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    check_database() 