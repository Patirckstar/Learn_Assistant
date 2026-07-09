from app.core.database import get_db
from app.models.chapter import Chapter
from app.models.paper import Paper

db = next(get_db())

chapters = db.query(Chapter).filter(Chapter.level == 1).order_by(Chapter.sort_order).all()
print(f"总共有 {len(chapters)} 个父章节")

for ch in chapters:
    existing_paper = db.query(Paper).filter(Paper.chapter_id == ch.id).first()
    has_content = bool(ch.content)
    
    sections = db.query(Chapter).filter(Chapter.parent_id == ch.id).all()
    total_content_length = 0
    if ch.content:
        total_content_length += len(ch.content)
    for sec in sections:
        if sec.content:
            total_content_length += len(sec.content)
    
    print(f"\n章节ID: {ch.id}, 标题: {ch.title}")
    print(f"  已有试卷: {'是' if existing_paper else '否'}")
    print(f"  章节内容长度: {len(ch.content) if ch.content else 0}")
    print(f"  小节数量: {len(sections)}")
    print(f"  总内容长度: {total_content_length}")
    print(f"  需要生成试卷: {'是' if (not existing_paper and total_content_length > 0) else '否'}")

db.close()
