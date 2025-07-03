from AIGN import AIGN
from LLM import chatLLM, picLLM

aign = AIGN(chatLLM, picLLM)

user_idea = "主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！"
user_requriments = ""
# embellishment_idea="""
# 请使用文言文创作
# """
# embellishment_idea = """
# - 使用发癫文学的风格
# - 在正文中添加表情包：😂😅😘💕😍👍
# """

print("beginning\n")
aign.genNovelOutline(user_idea)
aign.genBeginning(user_requriments)

for i in range(1):
    print("paragraph {}\n".format(i))
    aign.genNextParagraph()

with open("./outputs/book.md", "w", encoding="utf-8") as f:
    print(aign.getNovel(), file=f)