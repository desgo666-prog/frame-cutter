# PNG Frame Cutter

一个用于处理 PNG 帧序列图的桌面小工具。它可以自动识别精灵图中的独立帧并批量导出，也可以把纯色背景转换为透明背景。

界面基于 Tkinter，图像处理基于 Pillow。项目当前主要面向 Windows 使用，也可以在已安装 Tkinter 的 Python 环境中运行。

## 功能

- 导入单张或多张 PNG 图片，支持拖拽导入
- 自动识别透明图或纯色背景图
- 基于前景连通域自动切分帧，减少等宽切割导致的串帧问题
- 预览识别结果，支持上一帧、下一帧和按 FPS 播放
- 批量导出切割后的帧序列
- 可选在切帧时去除背景
- 单独提供“纯色背景转透明”模式
- 可为每张源图自动创建独立输出子文件夹

## 适用场景

这个工具适合处理背景比较干净的 PNG 精灵图、动作帧序列图、游戏素材草图等。它依赖自动识别前景区域，因此复杂背景、前景互相接触、阴影/特效碎片过多的图片可能需要人工检查导出结果。

## 环境要求

- Python 3.10 或更新版本
- Windows、macOS 或 Linux 桌面环境
- Tkinter

> Windows 官方 Python 通常自带 Tkinter。部分 Linux 发行版需要额外安装 `python3-tk`。

## 快速运行

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python frame_cutter_gui.py
```

Windows 用户也可以直接双击：

```text
run_app.bat
```

## 使用方式

1. 点击“添加图片”，或把 PNG 文件拖到窗口中。
2. 选择“帧切割输出文件夹”和/或“去背景输出文件夹”。
3. 在“导出功能”中选择：
   - `帧切割`：自动识别并导出每一帧。
   - `纯色背景转透明`：整图去背景并输出带 alpha 的 PNG。
4. 根据需要调整“帧切割时去背景”“每张图单独子文件夹”和“序号位数”。
5. 点击“刷新预览”检查结果。
6. 点击“开始导出”。

## 输出规则

帧切割模式会按如下格式保存：

```text
001_source-name.png
002_source-name.png
003_source-name.png
```

如果开启“每张图单独子文件夹”，每张源图会导出到以源文件名命名的子目录中。

去背景模式会按如下格式保存：

```text
source-name_alpha.png
```


Windows 用户可以双击：

```text
build_exe.bat
```

打包产物位于：

```text
dist\FrameCutter.exe
```

## 项目结构

```text
.
├── frame_cutter_gui.py     # 主程序
├── requirements.txt        # 运行依赖
├── requirements-dev.txt    # 打包/开发依赖
├── run_app.bat             # Windows 运行脚本
├── build_exe.bat           # Windows 打包脚本
└── README.md
```

## 开发

```powershell
python -m pip install -r requirements-dev.txt
python -m py_compile frame_cutter_gui.py
```

目前项目是单文件桌面工具，核心逻辑集中在 `FrameCutterApp` 中。欢迎提交更稳定的识别算法、测试样例、跨平台打包配置和界面改进。


## 许可证

本项目使用 MIT License。详见 [LICENSE](LICENSE)。
