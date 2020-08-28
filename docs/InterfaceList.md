**return format**

```
{
    "status": bool,
    "result": any
}
```

`status` 表示其输入的参数是否符合链接规范，若为 `False` 则该次请求失败，请求不会被处理。

`result` 表示若请求成功时，服务端返回的结果，具体含义根据请求的链接不同而不同。

***

**sys**

| Path | Parameter | Method | Need login | Return |
| :--: | :-------: | :----: | :--------: | :----: |
| exit |           |  Post  |   False    |  True  |

返回值说明

- exit：永远只会返回 `True` 。

***

**user**

|     Path     |            Parameter            | Method | Need login | Return |
| :----------: | :-----------------------------: | :----: | :--------: | :----: |
|    login     | account: str<br />password: str |  Post  |   False    |  True  |
|    logout    |                                 |  Post  |   False    |  True  |
| refreshToken |                                 |  Post  |   False    |  bool  |
|   isLogin    |                                 |  Get   |   False    |  bool  |
|   tokenMsg   |                                 |  Get   |   False    |  str   |

返回值说明

- login：`True` 表示服务端已发送登陆请求，并不表示登陆成功。
- logout：
- refreshToken：若之前进行过登陆，服务器上存有 `RefreshToken` ，则将使用该 `RefreshToken` 进行 `Token` 刷新操作并返回 `True` 。若无 `RefreshToken` 则将中断操作并返回 `False` 。
- isLogin：是否进行过登陆操作，服务器上存有 `RefreshToken` 。
- tokenMsg：返回值为一个三行的字符串，格式为 `AccessToken: ***\nRefreshToken: ***\nTokenUpdateTime: ***` 。

***

**environment**

|         Path         |          Parameter          | Method | Need login |           Return            |
| :------------------: | :-------------------------: | :----: | :--------: | :-------------------------: |
|     setProxyMode     | mode: int<br />address: str |  Post  |   False    |            bool             |
|      setTimeout      |        timeout: int         |  Post  |   False    |            bool             |
| setConcurrencyNumber |         number: int         |  Post  |   False    |            bool             |
|   setIntervalTime    |         second: int         |  Post  |   False    |            bool             |
|     setIncrement     |       increment: bool       |  Post  |   False    |            bool             |
|    getEnvironment    |                             |  Get   |   False    | [ str, str, int, int, int ] |

`setProxyMode` 可选值及其运行模式：

- `mode` 为 0 表示不适用代理，直接进行连接，此时 `address` 可填入任意值。
- `mode` 为 1 表示使用 `http` 代理进行连接，此时 `address` 应该为该模式的字段 `http://*.*.*.*:*` 。注意，目前只可使用 `http` 代理，并不支持 `https` 和 `socket` 代理。
- `mode` 为 2 表示使用域名转换，将域名转换为 `IP` 地址进行连接，此时 `address` 可填入任意值。国内用户可使用该方式直接连上 Pixiv 。

返回值说明：

- setProxyMode：设置是否成功。
- setTimeout：设置是否成功。
- setConcurrencyNumber：设置是否成功。
- setIntervalTime：设置是否成功。
- setIncrement：设置是否成功。
- getEnvironment：
  - 代理状态：`Direct` 或 `Proxy` 或 `IP` 。
  - 代理地址：`http://*.*.*.*:*` 或 `""` 。
  - 超时超时设置。
  - 单任务并发下载数。
  - 同步查询间隔。

`getEnvironment` 中的返回值的具体含义请参考 [运行机制](#) 。

***

**operation**

|      Path      | Parameter | Method | Need login |              Return               |
| :------------: | :-------: | :----: | :--------: | :-------------------------------: |
|   startTask    | tid: int  |  Post  |    True    |           [ bool, str ]           |
|    stopTask    | tid: int  |  Post  |    True    |           [ bool, str ]           |
|   deleteTask   | tid: int  |  Post  |   False    |               bool                |
|  taskDetails   | tid: int  |  Get   |   False    |            TaskDetails            |
| allTaskDetails |           |  Get   |   False    | [ TaskDetails, TaskDetails, ... ] |

返回值说明：

- startTask：该命令需进行登陆后才可进行操作，若未登陆进行该操作，则 `bool` 将为 `False` ，且 `str` 的值为 `Please login.` 。若登陆后，`str` 的值将会 `""` ，`bool` 值表示是否查找到对应的 `tid` ，操作是否成功。
- stopTask：同上。
- deleteTask：同上。
- taskDetails：返回对应 `tid` 的 `task` 的信息。
- allTaskDetails：返回所有 `task` 的信息。

`TaskDetails` 是一个列表，其包含了一个任务的属性。

```
TaskDetils = [
    Over: bool,
    TID: int,
    TaskName: str,
    TypeName: str,
    SavePath: str,
    StageName: str,
    Stage: str,
    Less: int
]
```

***

**create**

|    Path    |                     Parameter                      | Method | Need login |                    Return                    |
| :--------: | :------------------------------------------------: | :----: | :--------: | :------------------------------------------: |
| singleWork | keyWord: str<br />taskName: str<br />savePath: str |  Post  |   False    | [ False, [] ] or <br />[ True, TaskDetails ] |
| userWorks  | keyWord: str<br />taskName: str<br />savePath: str |  Post  |   False    | [ False, [] ] or <br />[ True, TaskDetails ] |

返回值说明：

- singleWork：列表首项的 `bool` 表示创建任务操作是否成功，若创建成功，则列表的第二项为新创建的 `task` 的信息。
- userWorks：同上。