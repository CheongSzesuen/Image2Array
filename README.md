# Image2Array(I2A)
>用于ST7735S驱动的TFT_LCD（128*160）屏幕图片的取模 

由于在学习由ESP32 WROOM E为开发板的TFT_LCD1.8英寸屏幕驱动中遇到图片取模问题，而苦于既没有在线的转换也没有Linux下的转换软件，即便通过wine在Linux下使用windows的软件，还有正版注册和生成的C语言数组无法正确显示的问题。于是有了此python脚本来实现取模，现在（2025.5.2 晚）上传GitHub。决定长期开发脚本。
## 适用范围
本脚本适合于ESP32 WROOM E为开发板，ST7735S驱动的TFT_LCD屏幕（尺寸为1.8英寸,RGB,128*160）的渲染图片的学习项目。
之后会变为纯粹的取模脚本，拓展适用范围和平台。
### 硬件来源
此LCD屏幕购于淘宝优信电子销量最高的那条链接。
# 什么是取模？
取模就是把图像的像素颜色变成直接使用的二进制数据，以便TFT LCD的渲染。这个脚本的取模就是负责将RGB888等传统的颜色表示方式RGB转为RGB565的过程。
## 什么是RGB888，什么又是RGB565？
RGB888和RGB565都是表示颜色的两种方式。
|RGB888|RGB565|
|---|---|
|红色（R）：8位（0~255，256级亮度）|红色（R）：5位（0~31，32级亮度）|
|绿色（G）：8位（0~255，256级亮度）|绿色（G）：6位（0~63，64级亮度）|
|蓝色（B）：8位（0~255，256级亮度）|蓝色（B）：5位（0~31，32级亮度）|
|总计：8 + 8 + 8 = 24位（3字节）|总计：5 + 6 + 5 = 16位（2字节）|

>这里的**位**就是**量化位数**，有几位就是由几个0或者1来存储的。
### 你可能会好奇为什么RGB565的绿色有六位
因为人眼对绿色的感知能力比红色和蓝色更强，而且如果红绿蓝都是5位那么16-（5*3）=1  还有一位浪费了。
#### 那你可能又要问为什么RGB888都是8位
因为RGB565位数有限，给绿色分配更多的位数可以更好地捕捉绿色的细微变化，看起来更平滑。而8位已经不用担心了，2^8已经能显示256个不同深度的单位颜色了。
<br>
这里有一个RGB888的例子

```python
# 红色（R=255, G=0, B=0）
red = [0xFF, 0x00, 0x00]  # 十六进制：0xFF0000

# 绿色（R=0, G=255, B=0）
green = [0x00, 0xFF, 0x00]  # 十六进制：0x00FF00

# 蓝色（R=0, G=0, B=255）
blue = [0x00, 0x00, 0xFF]  # 十六进制：0x0000FF
```

这里有一个RGB565的例子
```python
# 红色（R=31, G=0, B=0）
red = 0b11111 000000 00000  # 十六进制：0xF800

# 绿色（R=0, G=63, B=0）
green = 0b00000 111111 00000  # 十六进制：0x07E0

# 蓝色（R=0, G=0, B=31）
blue = 0b00000 000000 11111  # 十六进制：0x001F
```

#### 拓展
除了取模到RGB565、有时候对于特殊的机器还会有其他取模，比如取模到8位灰度（常见墨水屏）、1位灰度（电子价签，低端墨水屏）、4位灰度（古早LCD）。
RGBA8888、RGBA4444、ARGB1555、RGB332、BGR565/BGR888（BGR格式）、RGBX8888、YUV/YCrCb、HSV/HSL、CMYK。

### 什么？你说RGB是什么？~~别学电子信息了~~
众多的LCD屏幕是由RGB控制显示的，R(Red)、G(Green)、B(Blue)，由这三种颜色，再通过控制不同颜色占比多少就可以显示不同颜色。
## 为什么ESP32驱动显示屏需要取模？
1. 硬件
- 通过上面介绍RGB565，并比较了RGB888，就会明白RGB565要比RGB888少三分之一的存储空间，ESP32的RAM和FLASH有限，把图片取模后能提升传输速率和优化存储。
- TFT LCD原生支持RGB565，渲染可以避免大量计算。
2. 性能
- 效率高，字节少了单位时间发了更多了。
- 不消耗算力，因为RGB565可以直接渲染。
3. 兼容
- 嵌入式显示屏（如ST7735、ST7789、ILI9341等控制器）默认支持RGB565。
## 使用
### 使用脚本
#### 1. 克隆仓库
```bash
git clone https://github.com/CheongSzesuen/Image2Array.git
```
#### 2. 进入项目目录
```bash
cd Image2Array #Linux下
手动进入下载的文件夹 #macos或windows
```
#### 3. 安装依赖
linux需要进入venv运行pip
```bash
pip install -r requirements.txt
```
#### 4. 运行程序
```bash
python Image2Array.py
```
>提示：程序会自动记录上次打开的目录，配置文件保存在 ~/.config/Image2Array/config.json
#### 5. 常见问题
```bash
# 如果遇到PyQt5错误：
sudo apt-get install python3-pyqt5  # Ubuntu/Debian
brew install pyqt@5                # macOS

# 如果遇到Pillow错误：
pip install --upgrade pillow
```
### 使用打包的程序
#### 1. 下载程序
进入[Image2Array的Releases](https://github.com/CheongSzesuen/Image2Array/releases)的页面，然后找到标有Latest标签的最新版本下载。
#### 2. 下载对应的版本
提供 Linux (x64/ARM64) | macOS (ARM64/x64) | Windows (x86/x64)
#### 3. 使用可执行程序
Linux需要先让文件作为软件运行（右键文件点属性）再使用
### 在CPP代码中使用数组
#### 1. 将生成的数组文件放进需要的文件夹里
比如放在单片机的工程文件夹根目录
#### 2. 在main.cpp里引入此文件
在`main.cpp`里的头部引入文件。以VScode中的PlatformIO的文件结构做例子。并假设你的数组文件名叫做image_data.h，放在根目录里。
```cpp
#include "../image_data.h"
```
#### 3. 在main.cpp里加入渲染的代码
调用pushImage函数显示图片，此程序目前会将数组名称默认为`image_data`，所以在main.cpp里写
```cpp
tft.pushImage(x, y, IMAGE_WIDTH, IMAGE_HEIGHT, const_cast<uint16_t *>(image_data));
```
这里的x、y是确定图片开始显示位于屏幕的哪里
`IMAGE_WIDTH`和 `IMAGE_HEIGHT`是由I2A生成的`image_data.h`里确定的，这串定义在`image_data.h`文件的末尾。一般不需要更改，因为它是由图片大小决定的。后面的`image_data`就是**数组名称**，不是**文件名称**。

### 仓库文件结构
```
Image2Array/
├── requirements.txt #python打包使用，请忽略
└── Image2Array.py #主程序
```

## To-Do
- [x] 支持更多原始图片格式
- [x] 支持GUI
- [x] 打包为全平台
- [ ] 标准化软件
- [ ] 支持更多取模灰度选择
- [x] 标准化文件结构
- [ ] 支持不同取模顺序
- [ ] 按照屏幕要求的字节顺序排列二进制位
- [ ] 用户自定义转换名称和数组名称
- [ ] 可设置屏幕宽高
- [ ] 可自动获取不同开发板的FLASH来优化缩放
- [ ] 支持裁切（自定义裁切）或不裁切（存疑，不知道怎么弄）
- [ ] 支持批量转换，并能选择同一文件还是多个文件
- [ ] 对windows支持右键添加快捷取模菜单
- [ ] 选择输出数据类型（bin、c、bmp）
- [ ] 支持调色板
- [ ] 支持用户自定义保存路径以及是否每次选择
- [ ] 支持亮度调整

## 作者
WaiJade(CheongSzesuen)
## 许可证
遵循GPL-3.0 license
