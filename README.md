# 主列表识别（ischannel）
-------------

> 关于我
  简书：[Tony带不带水](https://www.jianshu.com/u/83c7ce3fa495)  邮箱：[lhzhang.Lyon@gmail.com](mailto:lhzhang.Lyon@gmail.com)   
欢迎关注联系合作

此项目下代码为简化列表识别代码，功能为提取主列表元素，爬虫相关。
#### 结果示例:  
红色区域为识别结果。
![列表识别结果图](http://upload-images.jianshu.io/upload_images/9232536-bb4eceee405047e9.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

###原理说明
[Python爬虫:细说列表识别提取](https://www.jianshu.com/p/fee79753cf9f)

### 下载安装适用
将本项目代码置于同一目录下。
安装依赖库
``` 
pip install -r requirements.txt
```
运行demo代码
```
python yourPath/find_channel.py
```
demo中识别的url为[https://www.jianshu.com/u/83c7ce3fa495](https://www.jianshu.com/u/83c7ce3fa495),将输出主列表xpath

### 接口说明
- is_channel_judge
  - 判断当前页是否为频道（有且只有一个主列表的定义为频道）
  - 返回值[ [isChannel(bool, 是否为频道页), hasMore(bool)], [listXpath(string)] ]
- get_list_xpath
  - 若是列表的话返回主列表Xpath
  - 返回值[ [listXpath(string)] ]

### 注意事项
- 基于python3
- 由于需要取位置信息，基于浏览器，项目中使用的是Chrome，在driver_common.py可以自行更改
- 支持chrmoe的headless模式
- 如果你运行不成功请检查你是否能正常初始化浏览器
- 若还有问题[请发邮件给我](mailto:lhzhang.Lyon@gmail.com) 

### TODO
如有时间会继续维护优化此代码，也欢迎大家提交维护，代码中注释比较详细。
优化或重构一下方面：
1.  列表扫描方法
2.  某些过滤条件（类似列表中有图片等等），考虑提取链接特征来优化
