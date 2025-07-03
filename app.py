import random
import threading
import time

import gradio as gr

from AIGN import AIGN
from LLM import chatLLM, picLLM

STREAM_INTERVAL = 0.

def make_middle_chat():
    carrier = threading.Event()
    carrier.history = []

    def middle_chat(messages, temperature=None, top_p=None):
        nonlocal carrier
        carrier.history.append([None, ""])
        if len(carrier.history) > 20:
            carrier.history = carrier.history[-16:]
        try:
            for resp in chatLLM(
                messages, temperature=temperature, top_p=top_p, stream=True
            ):
                output_text = resp["content"]
                total_tokens = resp["total_tokens"]

                carrier.history[-1][1] = f"total_tokens: {total_tokens}\n{output_text}"
            return {
                "content": output_text,
                "total_tokens": total_tokens,
            }
        except Exception as e:
            carrier.history[-1][1] = f"Error: {e}"
            raise e

    return carrier, middle_chat


def gen_outline_button_clicked(aign, user_idea, history):
    aign.user_idea = user_idea

    carrier, middle_chat = make_middle_chat()
    carrier.history = history
    aign.novel_outline_writer.chatLLM = middle_chat

    gen_outline_thread = threading.Thread(target=aign.genNovelOutline)
    gen_outline_thread.start()

    while gen_outline_thread.is_alive():
        yield [
            aign,
            carrier.history,
            aign.novel_outline,
            gr.Button(visible=False),
        ]
        time.sleep(STREAM_INTERVAL)
    yield [
        aign,
        carrier.history,
        aign.novel_outline,
        gr.Button(visible=False),
    ]


def gen_beginning_button_clicked(
    aign, history, novel_outline, novel_setting, user_requriments, embellishment_idea
):
    aign.novel_outline = novel_outline
    aign.novel_setting = novel_setting
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea

    carrier, middle_chat = make_middle_chat()
    carrier.history = history
    aign.novel_beginning_writer.chatLLM = middle_chat
    aign.novel_embellisher.chatLLM = middle_chat

    gen_beginning_thread = threading.Thread(target=aign.genBeginning)
    gen_beginning_thread.start()

    while gen_beginning_thread.is_alive():
        yield [
            aign,
            carrier.history,
            aign.setting,
            aign.writing_plan,
            aign.temp_setting,
            aign.novel_content,
            gr.Button(visible=False),
        ]
        time.sleep(STREAM_INTERVAL)
    yield [
        aign,
        carrier.history,
        aign.setting,
        aign.writing_plan,
        aign.temp_setting,
        aign.novel_content,
        gr.Button(visible=False),
    ]


def gen_next_paragraph_button_clicked(
    aign,
    history,
    user_idea,
    novel_outline,
    novel_setting,
    writing_memory,
    temp_setting,
    writing_plan,
    user_requriments,
    embellishment_idea,
):
    aign.user_idea = user_idea
    aign.novel_outline = novel_outline
    aign.novel_setting = novel_setting
    aign.writing_memory = writing_memory
    aign.temp_setting = temp_setting
    aign.writing_plan = writing_plan
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea

    carrier, middle_chat = make_middle_chat()
    carrier.history = history
    aign.novel_writer.chatLLM = middle_chat
    aign.novel_embellisher.chatLLM = middle_chat
    aign.memory_maker.chatLLM = middle_chat

    gen_next_paragraph_thread = threading.Thread(target=aign.genNextParagraph)
    gen_next_paragraph_thread.start()

    while gen_next_paragraph_thread.is_alive():
        yield [
            aign,
            carrier.history,
            aign.setting,
            aign.writing_plan,
            aign.temp_setting,
            aign.writing_memory,
            aign.novel_content,
            gr.Button(visible=False),
        ]
        time.sleep(STREAM_INTERVAL)
    yield [
        aign,
        carrier.history,
        aign.setting,
        aign.writing_plan,
        aign.temp_setting,
        aign.writing_memory,
        aign.novel_content,
        gr.Button(visible=False),
    ]


def download_novel_button_clicked(
    aign
):
    with open("./outputs/book.md", "w", encoding="utf-8") as f:
        print(aign.getNovel(), file=f)


css = """
#row1 {
    min-width: 200px;
    max-height: 700px;
    overflow: auto;
}
#row2 {
    min-width: 300px;
    max-height: 700px;
    overflow: auto;
}
#row3 {
    min-width: 200px;
    max-height: 700px;
    overflow: auto;
}
"""

with gr.Blocks(css=css) as demo:
    aign = gr.State(AIGN(chatLLM, picLLM))
    gr.Markdown("## AI 写小说 Demo")
    with gr.Row():
        with gr.Column(scale=0, elem_id="row1"):
            with gr.Tab("开始"):
                gr.Markdown("生成大纲->大纲标签->生成开头->状态标签->生成下一段")
                user_idea_text = gr.Textbox(
                    "主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！",
                    label="想法",
                    lines=4,
                    interactive=True,
                )
                user_requriments_text = gr.Textbox(
                    "",
                    label="写作要求",
                    lines=4,
                    interactive=True,
                )
                embellishment_idea_text = gr.Textbox(
                    "",
                    label="润色要求",
                    lines=4,
                    interactive=True,
                )
                gen_outline_button = gr.Button("生成大纲")
            with gr.Tab("大纲"):
                novel_outline_text = gr.Textbox(
                    label="大纲", lines=24, interactive=True
                )
                gen_beginning_button = gr.Button("生成开头")
            with gr.Tab("状态"):
                writing_memory_text = gr.Textbox(
                    label="记忆",
                    lines=6,
                    interactive=True,
                    max_lines=8,
                )
                novel_setting_text = gr.Textbox(
                    label="设定", lines=4, interactive=True
                )
                writing_plan_text = gr.Textbox(label="计划", lines=6, interactive=True)
                temp_setting_text = gr.Textbox(
                    label="临时设定", lines=5, interactive=True
                )
                gen_next_paragraph_button = gr.Button("生成下一段")
        with gr.Column(scale=3, elem_id="row2"):
            chatBox = gr.Chatbot(height=f"80vh", label="输出")
        with gr.Column(scale=0, elem_id="row3"):
            novel_content_text = gr.Textbox(
                label="小说正文", lines=28, interactive=True, show_copy_button=True
            )
            download_novel_button = gr.Button("下载小说")

    gr.Markdown("github: https://github.com/hwshqtb/AI_Gen_Novel modified from https://github.com/cjyyx/AI_Gen_Novel")

    gen_outline_button.click(
        gen_outline_button_clicked,
        [aign, user_idea_text, chatBox],
        [aign, chatBox, novel_outline_text, gen_outline_button],
    )
    gen_beginning_button.click(
        gen_beginning_button_clicked,
        [
            aign,
            chatBox,
            novel_outline_text,
            novel_setting_text,
            user_requriments_text,
            embellishment_idea_text,
        ],
        [
            aign,
            chatBox,
            novel_setting_text,
            writing_plan_text,
            temp_setting_text,
            novel_content_text,
            gen_beginning_button,
        ],
    )
    gen_next_paragraph_button.click(
        gen_next_paragraph_button_clicked,
        [
            aign,
            chatBox,
            user_idea_text,
            novel_outline_text,
            novel_setting_text,
            writing_memory_text,
            temp_setting_text,
            writing_plan_text,
            user_requriments_text,
            embellishment_idea_text,
        ],
        [
            aign,
            chatBox,
            novel_setting_text,
            writing_plan_text,
            temp_setting_text,
            writing_memory_text,
            novel_content_text,
        ],
    )
    download_novel_button.click(
        download_novel_button_clicked,
        [aign]
    )

demo.queue()
demo.launch()
