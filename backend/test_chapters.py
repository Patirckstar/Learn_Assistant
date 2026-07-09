"""测试章节数据"""

import json
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

password = quote_plus("Open@12345")
engine = create_engine(
    f"mysql+pymysql://mao:{password}@127.0.0.1:3306/learn_assistant?charset=utf8mb4",
    pool_size=20,
    max_overflow=50,
)

with engine.connect() as conn:
    print("=== 所有章节及其 level ===")
    result = conn.execute(text("""
        SELECT id, title, level, parent_id, sort_order
        FROM chapters
        ORDER BY sort_order
    """))
    chapters = result.fetchall()
    for c in chapters:
        has_paper = conn.execute(text("SELECT COUNT(*) FROM papers WHERE chapter_id = :id"), {"id": c.id}).scalar() > 0
        print(f"ID:{c.id} | Level:{c.level} | Parent:{c.parent_id} | {'✓有试卷' if has_paper else '✗无试卷'} | {c.title}")
    
    print(f"\n=== level=1 的章节 ===")
    result = conn.execute(text("""
        SELECT id, title, level
        FROM chapters
        WHERE level = 1
        ORDER BY sort_order
    """))
    level1_chapters = result.fetchall()
    for c in level1_chapters:
        has_paper = conn.execute(text("SELECT COUNT(*) FROM papers WHERE chapter_id = :id"), {"id": c.id}).scalar() > 0
        print(f"ID:{c.id} | {'✓有试卷' if has_paper else '✗无试卷'} | {c.title}")