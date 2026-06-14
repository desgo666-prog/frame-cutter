# Contributing

感谢你愿意改进 PNG Frame Cutter。

## 本地开发

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python frame_cutter_gui.py
```

提交前建议至少运行：

```powershell
python -m py_compile frame_cutter_gui.py
```

## 贡献方向

- 改进复杂精灵图的自动识别效果
- 增加测试素材和可重复的处理结果验证
- 改进跨平台运行和打包流程
- 优化界面布局和交互文案
- 修复导出异常、预览异常或性能问题

## 提交建议

- 保持改动聚焦，一次提交解决一个问题。
- 如果修改识别算法，请说明适用的素材类型和可能影响。
- 不要提交 `.venv/`、`build/`、`dist/` 或 EXE 文件。
- 如果提交截图或样例素材，请确认你拥有发布权限。
