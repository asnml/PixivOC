## 这是什么？

&emsp;&emsp;PixivOC 是一个Pixiv图片下载器的服务端，其大致的运行模式跟普通的下载器没什么区别。



## 特点

- 远程操作：PixivOC 采用 Socket 通讯来与其他软件进行交互，这意味着你可以在服务器上部署该应用，并随时随地使用客户端来浏览下载情况。
- 境内无需翻墙即可访问：在境内是无法直接访问 Pixiv 的，该内核通过更改网站域名为IP的方式，实现了境内无需代理即可访问。
- 高性能异步下载图片：下载图片时采用了 aiohttp 库进行异步下载，用户可以通过简单的调节参数更改并发数实现改变下载速度。



## 依赖库

- requests
- aiohttp



## 客户端

&emsp;&emsp;**库中实现了一个简易的命令行客户端~~（因为没维护已经出bug了）~~，使用PyQt5编写的客户端点[这里](https://github.com/asnml/PixivOC-Client)，客户端编写请参阅[服务器编写](#[https://github.com/asnml/PixivOC/blob/master/docs/%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%BC%96%E5%86%99.md](https://github.com/asnml/PixivOC/blob/master/docs/服务器编写.md))。**



## 使用说明

&emsp;&emsp;这只是一个服务端，具体使用方法请参阅[客户端](https://github.com/asnml/PixivOC-Client)，具体运行机制请参考[文档](https://github.com/asnml/PixivOC/tree/master/docs)。
