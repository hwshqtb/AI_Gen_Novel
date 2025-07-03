import os
import re
import time

def Retryer(func, max_retries=10):
    def wrapper(*args, **kwargs):
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print("-" * 30 + f"\n失败：\n{e}\n" + "-" * 30)
                time.sleep(2.333)
        raise ValueError("失败")

    return wrapper


class MarkdownAgent:
    """专门应对输入输出都是md格式的情况，例如小说生成"""

    def __init__(
        self,
        chatLLM,
        sys_prompt: str,
        name: str,
        temperature=0.8,
        top_p=0.8,
        use_memory=False,
        first_replay="明白了。",
        # first_replay=None,
        is_speak=True,
    ) -> None:

        self.chatLLM = chatLLM
        self.sys_prompt = sys_prompt
        self.temperature = temperature
        self.top_p = top_p
        self.use_memory = use_memory
        self.is_speak = is_speak

        self.history = [{"role": "user", "content": self.sys_prompt}]

        if first_replay:
            self.history.append({"role": "assistant", "content": first_replay})
        else:
            resp = chatLLM(messages=self.history)
            self.history.append({"role": "assistant", "content": resp["content"]})
            # if self.is_speak:
            #     self.speak(Msg(self.name, resp["content"]))

    def query(self, user_input: str) -> str:
        resp = self.chatLLM(
            messages=self.history + [{"role": "user", "content": user_input}],
            temperature=self.temperature,
            top_p=self.top_p,
        )
        if self.use_memory:
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": resp["content"]})

        return resp

    def getOutput(self, input_content: str, output_keys: list) -> dict:
        """解析类md格式中 # key 的内容，未解析全部output_keys中的key会报错"""
        resp = self.query(input_content)
        output = resp["content"]

        lines = output.split("\n")
        sections = {}
        current_section = ""
        for line in lines:
            if line.startswith("# ") or line.startswith(" # "):
                # new key
                current_section = line[2:].strip()
                sections[current_section] = []
            else:
                # add content to current key
                if current_section:
                    sections[current_section].append(line.strip())
        for key in sections.keys():
            sections[key] = "\n".join(sections[key]).strip()

        for k in output_keys:
            if (k not in sections) or (len(sections[k]) == 0):
                raise ValueError(f"fail to parse {k} in output:\n{output}\n\n")

        # if self.is_speak:
        #     self.speak(
        #         Msg(
        #             self.name,
        #             f"total_tokens: {resp['total_tokens']}\n{resp['content']}\n",
        #         )
        #     )
        return sections

    def invoke(self, inputs: dict, output_keys: list) -> dict:
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"

        result = Retryer(self.getOutput)(input_content, output_keys)

        return result

    def clear_memory(self):
        if self.use_memory:
            self.history = self.history[:2]


class AIGN:
    def __init__(self, chatLLM, picLLM):
        self.chatLLM = chatLLM
        self.picLLM = picLLM

        self.novel_outline = ""
        self.paragraph_list = []
        self.novel_content = ""
        self.writing_plan = ""
        self.temp_setting = ""
        self.writing_memory = ""
        self.no_memory_paragraph = ""
        self.user_idea = ""
        self.user_requirements = ""
        self.embellishment_idea = ""
        self.setting = ""
        self.pictures = []

        self.novel_outline_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=open("prompts/outline.md", "r", encoding="utf-8").read(),
            name="NovelOutlineWriter",
            temperature=0.98,
        )
        self.novel_beginning_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=open("prompts/beginning.md", "r", encoding="utf-8").read(),
            name="NovelBeginningWriter",
            temperature=0.80,
        )
        self.novel_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=open("prompts/write.md", "r", encoding="utf-8").read(),
            name="NovelWriter",
            temperature=0.81,
        )
        self.novel_embellisher = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=open("prompts/embellish.md", "r", encoding="utf-8").read(),
            name="NovelEmbellisher",
            temperature=0.92,
        )
        self.memory_maker = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=open("prompts/memory.md", "r", encoding="utf-8").read(),
            name="MemoryMaker",
            temperature=0.66,
        )
        self.novel_climax_maker = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=open("prompts/climax.md", "r", encoding="utf-8").read(),
            name="ClimaxMaker",
            temperature=0.66,
        )

    def updateNovelContent(self):
        self.novel_content = ""

        pic_index = 0
        for i in range(len(self.paragraph_list)):
            self.novel_content += f"{self.paragraph_list[i]}\n\n"
            if pic_index < len(self.pictures) and i == self.pictures[pic_index]:
                self.novel_content += f"![{pic_index}](./{pic_index}.png)\n\n"
                pic_index = pic_index + 1
        
        return self.novel_content

    def genNovelOutline(self, user_idea=None):
        if user_idea:
            self.user_idea = user_idea
        resp = self.novel_outline_writer.invoke(
            inputs={"用户想法": self.user_idea},
            output_keys=["大纲"],
        )
        self.novel_outline = resp["大纲"]
        return self.novel_outline

    def genBeginning(self, user_requirements=None, embellishment_idea=None):
        if user_requirements:
            self.user_requirements = user_requirements
        if embellishment_idea:
            self.embellishment_idea = embellishment_idea

        resp = self.novel_beginning_writer.invoke(
            inputs={
                "用户想法": self.user_idea,
                "小说大纲": self.novel_outline,
                "用户要求": self.user_requirements,
            },
            output_keys=["开头", "设定", "计划", "临时设定"],
        )
        beginning = resp["开头"]
        self.writing_plan = resp["计划"]
        self.setting = resp["设定"]
        self.temp_setting = resp["临时设定"]

        resp = self.novel_embellisher.invoke(
            inputs={
                "大纲": self.novel_outline,
                "设定": self.setting,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "润色要求": self.embellishment_idea,
                "要润色的内容": beginning,
            },
            output_keys=["润色结果"],
        )
        beginning = resp["润色结果"]

        self.paragraph_list.append(beginning)
        self.genPicture(beginning)
        self.updateNovelContent()

        return beginning

    def getLastParagraph(self, max_length=2000):
        last_paragraph = ""

        for i in range(0, len(self.paragraph_list)):
            if (len(last_paragraph) + len(self.paragraph_list[-1 - i])) < max_length:
                last_paragraph = self.paragraph_list[-1 - i] + "\n" + last_paragraph
            else:
                break
        return last_paragraph

    def recordNovel(self):
        record_content = ""
        record_content += f"# 大纲\n\n{self.novel_outline}\n\n"
        record_content += f"# 设定\n\n{self.setting}\n\n"
        record_content += f"# 正文\n\n"
        record_content += self.novel_content
        record_content += f"# 记忆\n\n{self.writing_memory}\n\n"
        record_content += f"# 计划\n\n{self.writing_plan}\n\n"
        record_content += f"# 临时设定\n\n{self.temp_setting}\n\n"

        with open("novel_record.md", "w", encoding="utf-8") as f:
            f.write(record_content)

    def updateMemory(self):
        if (len(self.no_memory_paragraph)) > 2000:
            resp = self.memory_maker.invoke(
                inputs={
                    "前文记忆": self.writing_memory,
                    "正文内容": self.no_memory_paragraph,
                },
                output_keys=["新的记忆"],
            )
            self.writing_memory = resp["新的记忆"]
            self.no_memory_paragraph = ""

    def genNextParagraph(self, user_requirements=None, embellishment_idea=None):
        if user_requirements:
            self.user_requirements = user_requirements
        if embellishment_idea:
            self.embellishment_idea = embellishment_idea

        resp = self.novel_writer.invoke(
            inputs={
                "用户想法": self.user_idea,
                "大纲": self.novel_outline,
                "前文记忆": self.writing_memory,
                "设定": self.setting,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "用户要求": self.user_requirements,
                "上文内容": self.getLastParagraph(),
            },
            output_keys=["段落", "设定", "计划", "临时设定"],
        )
        next_paragraph = resp["段落"]
        next_setting = resp["设定"]
        next_writing_plan = resp["计划"]
        next_temp_setting = resp["临时设定"]

        resp = self.novel_embellisher.invoke(
            inputs={
                "大纲": self.novel_outline,
                "设定": next_setting,
                "临时设定": next_temp_setting,
                "计划": next_writing_plan,
                "润色要求": embellishment_idea,
                "上文": self.getLastParagraph(),
                "要润色的内容": next_paragraph,
            },
            output_keys=["润色结果"],
        )
        next_paragraph = resp["润色结果"]

        self.paragraph_list.append(next_paragraph)
        self.setting = next_setting
        self.writing_plan = next_writing_plan
        self.temp_setting = next_temp_setting

        self.no_memory_paragraph += f"\n{next_paragraph}"

        self.updateMemory()
        self.genPicture(next_paragraph)
        self.updateNovelContent()
        self.recordNovel()

        return next_paragraph

    def genPicture(self, content):
        resp2 = self.novel_climax_maker.invoke(
            inputs={
                "大纲": self.novel_outline,
                "设定": self.setting,
                "临时设定": self.temp_setting,
                "上文": content,
            },
            output_keys=["高潮", "描述"],
        )
        climax = resp2["描述"]

        if climax:
            self.picLLM(climax, len(self.pictures))
            self.pictures.append(len(self.paragraph_list) - 1)
            
        return len(climax)

    def getNovel(self):
        return self.novel_content