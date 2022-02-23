import asyncio
from json import JSONEncoder, dumps
from typing import List, Any

from aiohttp import TCPConnector, ClientSession

from .executor import AsyncioProgressbarQueueExecutor, AsyncioSimpleExecutor

PINTEREST_URL = 'https://www.pinterest.ru/resource/ConversationsResource/create/'

PINTEREST_HEADERS = {
  'authority': 'www.pinterest.ru',
  'pragma': 'no-cache',
  'cache-control': 'no-cache',
  'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
  'x-pinterest-appstate': 'active',
  'x-app-version': 'd00edb5',
  'x-pinterest-pws-handler': 'www/edit/[page].js',
  'sec-ch-ua-mobile': '?1',
  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Mobile Safari/537.36',
  'content-type': 'application/x-www-form-urlencoded',
  'accept': 'application/json, text/javascript, */*, q=0.01',
  'x-requested-with': 'XMLHttpRequest',
  'x-pinterest-source-url': '/edit/history/',
  'sec-ch-ua-platform': '"Android"',
  'origin': 'https://www.pinterest.ru',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.pinterest.ru/',
  'accept-language': 'en,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7',
}

class InputData:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class OutputData:
    def __init__(self, data, error):
        # self.id = user_json['id']
        self.username = data['username']
        self.fullname = data['full_name']
        self.is_default_image = data['is_default_image']
        self.image = data['image_large_url']
        self.error = error

    @property
    def fields(self):
        fields = list(self.__dict__.keys())
        fields.remove('error')

        return fields

    def __str__(self):
        error = ''
        if self.error:
            error = f' (error: {str(self.error)}'

        result = ''

        for field in self.fields:
            field_pretty_name = field.title().replace('_', ' ')
            value = self.__dict__.get(field)
            if value:
                result += f'{field_pretty_name}: {str(value)}\n'

        result += f'{error}'
        return result


class OutputDataList:
    def __init__(self, input_data: InputData, results: List[OutputData]):
        self.input_data = input_data
        self.results = results

    def __repr__(self):
        return f'Target {self.input_data}:\n' + '--------\n'.join(map(str, self.results))


class OutputDataListEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, OutputDataList):
            return {'input': o.input_data, 'output': o.results}
        elif isinstance(o, OutputData):
            return {k:o.__dict__[k] for k in o.fields}
        else:
            return o.__dict__

def import_aiohttp_cookies(cookiestxt_filename):
    from http.cookiejar import MozillaCookieJar
    from http.cookies import Morsel
    from aiohttp import CookieJar

    cookies_obj = MozillaCookieJar(cookiestxt_filename)
    cookies_obj.load(ignore_discard=True, ignore_expires=True)

    cookies = CookieJar()

    cookies_list = []
    for domain in cookies_obj._cookies.values():
        for key, cookie in list(domain.values())[0].items():
            c = Morsel()
            c.set(key, cookie.value, cookie.value)
            c["domain"] = cookie.domain
            c["path"] = cookie.path
            cookies_list.append((key, c))

    cookies.update_cookies(cookies_list)

    return cookies


class Processor:
    def __init__(self, *args, **kwargs):
        from aiohttp_socks import ProxyConnector

        # make http client session
        proxy = kwargs.get('proxy')
        self.proxy = proxy

        cookie_jar_file = kwargs.get('cookie_file')
        cookie_jar = import_aiohttp_cookies(cookie_jar_file)

        if proxy:
            connector = ProxyConnector.from_url(proxy, ssl=False)
        else:
            connector = TCPConnector(ssl=False)

        self.session = ClientSession(
            connector=connector, trust_env=True, cookie_jar=cookie_jar
        )
        if kwargs.get('no_progressbar'):
            self.executor = AsyncioSimpleExecutor()
        else:
            self.executor = AsyncioProgressbarQueueExecutor()

    async def close(self):
        await self.session.close()


    async def request(self, input_data: InputData) -> OutputDataList:
        error = None
        output_users = []

        data = {
            'source_url': '/edit/history/',
            'data': '{"options":{"user_ids":[],"emails":["'+input_data.value+'"],"text":"","pinId":"","no_fetch_context_on_resource":false},"context":{}}'
        }

        csrftoken = self.session.cookie_jar._cookies['www.pinterest.ru']['csrftoken'].value

        headers = PINTEREST_HEADERS
        headers.update({
          'x-csrftoken': '4650759346c189e2da4e34dedcb45e95',
        })

        try:
            response = await self.session.post(PINTEREST_URL, headers=headers, data=data)

            resp = await response.json()
            error = resp['resource_response'].get('error', {}).get('message', '')
            error_detail = resp['resource_response'].get('error', {}).get('message_detail', '')

            if not error and not error_detail:
                cur_user_id = resp['client_context']['user']['id']
                users = resp['resource_response']['data']['users']

                for u in users:
                    if str(u['id']) == cur_user_id:
                        continue

                    output_users.append(OutputData(u, error))
            else:
                print(error)
                print(error_detail)

        except Exception as e:
            error = e
            print(e)

        results = OutputDataList(input_data, output_users)

        return results


    async def process(self, input_data: List[InputData]) -> List[OutputDataList]:
        tasks = [
            (
                self.request, # func
                [i],          # args
                {}            # kwargs
            )
            for i in input_data
        ]

        results = await self.executor.run(tasks)

        return results
