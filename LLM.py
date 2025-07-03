from uniai import aliChatLLM, deepseekChatLLM, zhipuChatLLM, aliPicLLM

def chatLLM(
    messages: list,
    temperature=0.85,
    top_p=0.8,
    stream=False,
) -> dict:
    ...

def picLLM(
    prompt: list,
    index: int
) -> None:
    ...

if __name__ == "__main__":

    content = "请用一个成语介绍你自己"
    messages = [{"role": "user", "content": content}]

    resp = chatLLM(messages)
    print(resp)

    for resp in chatLLM(messages, stream=True):
        print(resp)
