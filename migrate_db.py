import sqlite3
import os

DB_PATH = "./data/app.db"

def migrate_database():
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        print("请先运行 python main.py 或 python init_data.py 初始化数据库")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(characters)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'avatar_type' not in columns:
            print("正在添加 avatar_type 列到 characters 表...")
            cursor.execute("ALTER TABLE characters ADD COLUMN avatar_type VARCHAR(20) DEFAULT 'emoji'")
            print("已添加 avatar_type 列")
        else:
            print("characters 表已包含 avatar_type 列")
        
    except Exception as e:
        print(f"更新 characters 表时出错: {e}")
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='background_configs'")
        if not cursor.fetchone():
            print("正在创建 background_configs 表...")
            cursor.execute("""
                CREATE TABLE background_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    background_type VARCHAR(20) DEFAULT 'color',
                    background_value VARCHAR(500) NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    is_default BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("已创建 background_configs 表")
            
            print("正在插入默认背景配置...")
            cursor.execute("""
                INSERT INTO background_configs (name, background_type, background_value, is_active, is_default)
                VALUES ('默认浅灰', 'color', '#f9fafb', 1, 1)
            """)
            print("已插入默认背景配置")
        else:
            print("background_configs 表已存在")
        
    except Exception as e:
        print(f"创建 background_configs 表时出错: {e}")
    
    conn.commit()
    conn.close()
    print("\n数据库迁移完成!")

if __name__ == "__main__":
    migrate_database()
