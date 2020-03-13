import time
from Download import *
from api import *
from mobileToken import TOKEN_MANAGER

import requests as rq
import json

work_id = 75792797
work_id_2 = 11217677  # bad id
PROXY_MANAGER.change_to_proxy('http://127.0.0.1:1081')
# PROXY_MANAGER.change_to_ip()
# TOKEN_MANAGER.refresh_auth_token()
# time.sleep(10)


package = WorkDetailsAPI.get_package(work_id_2, TOKEN_MANAGER._AccessToken)
resp = rq.get(package.url, headers=package.headers, params=package.params, proxies={'https': 'http://127.0.0.1:1081'})
with open('WorkDetails2.json', 'w', encoding='utf-8') as file:
    json.dump(resp.json(), file, ensure_ascii=False)
