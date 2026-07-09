import sys
sys.path.insert(0, '.')

from app.core.llm import get_llm

try:
    print("正在测试LLM调用...")
    llm = get_llm()
    print("LLM对象创建成功")
    
    response = llm.invoke("请简短回答：你好")
    print(f"LLM响应成功: {response.content[:50]}")
except Exception as e:
    print(f"LLM调用失败: {type(e).__name__}: {str(e)}")
