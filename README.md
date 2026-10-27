# ESP32-S3：DeepSeek 角色彩屏动画

为 1.8 英寸 128×160 ST7735 彩屏制作的 MicroPython 循环动画。电脑端从两张源图生成 32 帧、10 FPS 的 `hd_idle.dsv`；板子读取这种自定义压缩帧格式逐帧显示。`hd_idle_preview.mp4` 只供电脑预览，**不能直接交给 ESP32 播放**。

## 本动画版本的接线

该动画代码使用以下引脚，和同一块二号板后来的“桌面信息屏”项目引脚有区别。若二号板现在按桌面信息屏接线，直接刷本项目会黑屏；先断电，再按本表和实物丝印核对，不要带电改线。

| 彩屏引脚 | ESP32-S3 GPIO / 电源 |
| --- | --- |
| LED 背光 | 7 |
| SCK | 12 |
| SDA / MOSI | 11 |
| A0 / DC | 9 |
| RESET | 10 |
| CS | 8 |
| VCC / GND | 按所用彩屏模块的额定电压与板卡丝印接线，共地 |

代码里对应 `TFT(spi, 9, 10, 8)`。桌面信息屏项目后来验证的参数是 `TFT(spi, 10, 8, 9)`，两套接线不可混用。

## 运行

刷入适配 ESP32-S3 的 MicroPython，固件需提供 `deflate` 模块。将 `ST7735.py`、`hd_video.py`、`hd_idle.dsv` 上传到板上文件系统根目录，最后上传 `main.py` 并重启。`main.py` 负责调用 `hd_video.run()`。可通过 Thonny 按 Ctrl+C 停止动画。

电脑端重新生成资源：安装 Python 包 `Pillow`、`numpy`、`opencv-python`，并让 `ffmpeg` 在 PATH 中可用，然后执行 `python make_hd_loop.py`。生成脚本用到 `deepseek_open.png`、`deepseek_mid.png` 和 `probe_arm_morph.py`。仓库已经附有可直接使用的 `hd_idle.dsv`，因此只想在板上播放时无须安装这些电脑依赖。

`examples/` 保留早期像素版动画和最初的 ESP32-S3 MicroPython 入门脚本，不是高清版本的开机入口。`ST7735.py` 的文件头保留了原驱动作者的署名。本仓库记录了该动画方案；是否能在你**当前**的二号板接线上运行，需要先确认引脚是否按上表连接。
