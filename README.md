# autokey

Windows 后台按键自动化工具（AutoHotkey v1 版本）。

> 如果你遇到 AHK 在特定窗口失效，建议优先使用本仓库新增的 Python 版 `windows_autokey_py.py`（`PostMessage` 方案）。

## 功能特性

- 向指定窗口标题发送按键序列（`ControlSend`），支持目标窗口在未激活/最小化时运行。
- GUI 可配置：
  - 目标窗口标题
  - 运行中窗口下拉选择 / 一键选择当前活动窗口（锁定句柄）
  - 按键序列（示例：`abc`、`{ENTER}`、`^c`）
  - 按键间隔（毫秒）
  - 循环次数（`0` 表示无限循环）
  - 随机间隔开关与最小/最大范围
  - 随机点击坐标偏移（可选）
  - 开始/停止/清空日志
  - 运行日志显示区

## 运行方式

### 方案A：Python（推荐，针对 AHK 失效场景）

1. 安装 Python 3.9+。
2. 安装依赖：
   ```bash
   pip install pywin32
   ```
3. 运行：
   ```bash
   python windows_autokey_py.py
   ```

Python 版特点：
- 使用 `PostMessage(WM_KEYDOWN/WM_KEYUP)` 直接向窗口句柄发消息；
- 对某些 `ControlSend` 不稳定窗口更友好；
- 仍支持窗口句柄锁定、随机间隔、随机点击、循环次数等配置。

### 方案B：AutoHotkey v1

1. 安装 [AutoHotkey v1.1](https://www.autohotkey.com/)。
2. 双击运行 `windows_autokey.ahk`。
3. 在界面中填写参数后点击“开始”。

## 参数说明

- **目标窗口标题**：支持部分匹配（`SetTitleMatchMode, 2`）。
- **窗口选择方式**：
  - 可手动输入标题匹配；
  - 可点击“刷新窗口列表”并从下拉框选择；
  - 可点击“选择当前活动窗口”后按 Enter，锁定当前活动窗口句柄（更稳定）。
- **按键序列**：
  - Python 版：可自定义（示例：`{TAB}3{ESC}{SPACE}`）；
  - AHK 版：当前按需求固定为 `Tab -> 3 -> Esc -> Space`，每步 `2000ms`。
- **循环次数**：
  - `0` = 无限循环
  - `N` = 执行 N 次后自动停止
- **随机间隔**：启用后，每次发送后在 `[最小, 最大]` 范围随机等待。
- **随机点击偏移**：启用后，每轮先做一次 `ControlClick`，点击坐标为：
  - `X = 基准X ± 偏移范围X`
  - `Y = 基准Y ± 偏移范围Y`

## 打包为 EXE

### Python 打包（推荐）

```bash
pip install pyinstaller
pyinstaller -F -w windows_autokey_py.py
```

生成文件通常位于 `dist/windows_autokey_py.exe`。

可使用 AutoHotkey 自带 **Ahk2Exe**：

1. 打开 Ahk2Exe。
2. Source 选择 `windows_autokey.ahk`。
3. Destination 选择输出路径（如 `windows_autokey.exe`）。
4. 点击 Convert。

## 注意事项

- `ControlSend` 对大部分 Win32 程序有效，但并非所有程序都支持后台输入（尤其是部分游戏/管理员权限程序/UWP 应用）。
- 对 `ControlSend` 不稳定的场景，优先使用“锁定窗口句柄”方式发送（而非仅靠标题匹配），可显著提高固定序列 `{TAB}3{ESC}{SPACE}` 的成功率。
- 若目标程序以管理员权限运行，建议本工具也以管理员权限运行。
