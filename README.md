# 主列表识别（isChannel）

基于 Selenium 的主列表区域识别工具，用于从页面中提取主要列表容器的 XPath。

## 功能

- 判断当前页面是否可视为“频道页 / 列表页”
- 提取主列表区域 XPath
- 返回是否存在“更多”按钮等附加信息

## 结果示例

红色区域为识别结果。  
![列表识别结果图](http://upload-images.jianshu.io/upload_images/9232536-bb4eceee405047e9.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## 原理说明

[Python 爬虫：细说列表识别提取](https://www.jianshu.com/p/fee79753cf9f)

## 环境要求

- Python 3
- Chrome 浏览器
- 可用的 ChromeDriver（或系统已配置 Selenium Manager）

安装依赖：

```bash
pip install -r requirements.txt
```

运行示例：

```bash
python find_channel.py
```

示例脚本默认识别：
[https://www.jianshu.com/u/83c7ce3fa495](https://www.jianshu.com/u/83c7ce3fa495)

## 接口说明

### `is_channel_judge(chrome_driver, policyid, list_download=False)`

判断当前页是否为频道页（这里的定义是：页面中只识别出一个主列表）。

返回值：

```python
[[isChannel, hasMore], [listXpath]]
```

### `get_list_xpath(chrome_driver, policyid, list_download=False)`

若页面包含主列表，返回主列表区域 XPath。

返回值：

```python
[[listXpath]]
```

## 注意事项

- 项目依赖浏览器定位信息，核心逻辑运行在 Chrome 驱动之上。
- 当前版本已补充对 Selenium 4 的兼容处理。
- 如果浏览器初始化失败，请优先检查 Chrome / ChromeDriver 是否可正常启动。
- `driver_common.py` 中保留了浏览器相关配置，可按环境自行调整。

## 已做的兼容性优化

- 依赖版本从严格锁死改为较宽松范围，降低安装失败概率。
- 补充 Selenium 4 的 `find_element(s)_by_xpath` 兼容层。
- 更新 Chrome 初始化逻辑，兼容新的 headless 模式。
- 用明确异常替代裸 `assert`，便于排查页面加载失败。

## TODO

- 继续优化列表扫描策略
- 继续改进过滤条件，例如图片列表、链接特征等特殊场景
