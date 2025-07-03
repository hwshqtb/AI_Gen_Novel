from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
from dashscope import ImageSynthesis
import os

def aliPicLLM(model_name, size='1024*1024', api_key=None):
    api_key = os.environ.get("ALI_AI_API_KEY", api_key)

    prompt = "一间有着精致窗户的花店，漂亮的木质门，摆放着花朵"

    def picLLM(
        prompt: list,
        index: int
    ) -> None:
        print('----sync call, please wait a moment----')
        rsp = ImageSynthesis.call(api_key=api_key,
                                model=model_name,
                                prompt=prompt,
                                n=1,
                                size=size)
        print('response: %s' % rsp)
        if rsp.status_code == HTTPStatus.OK:
            # 在当前目录下保存图片
            for result in rsp.output.results:
                file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
                with open('./outputs/%d.png' % index, 'wb+') as f:
                    f.write(requests.get(result.url).content)
        else:
            print('sync_call Failed, status_code: %s, code: %s, message: %s' %
                (rsp.status_code, rsp.code, rsp.message))
    
    return picLLM