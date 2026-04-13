#NoEnv
#SingleInstance Force
#Persistent
SetBatchLines, -1
SetTitleMatchMode, 2

; ==============================
; Windows 后台按键自动化工具 (AutoHotkey v1)
; - 使用 ControlSend 向后台/最小化窗口发按键
; - 支持随机间隔、循环次数、运行日志
; - 支持可选随机点击偏移 (ControlClick)
; ==============================

global gRunning := false
global gSentCount := 0
global gStartTick := 0
global gWindowTitle := ""
global gWindowHwnd := 0
global gKeySeq := ""
global gBaseInterval := 1000
global gLoopCount := 0
global gUseRandomInterval := 0
global gRandMin := 800
global gRandMax := 1200
global gUseRandomClick := 0
global gClickBaseX := 0
global gClickBaseY := 0
global gClickOffsetX := 10
global gClickOffsetY := 10
global gCurrentLoop := 0
global gWindowMap := {}

Gui, Font, s9, Microsoft YaHei UI
Gui, Add, Text, x20 y20 w120 h20, 目标窗口标题:
Gui, Add, Edit, x150 y18 w360 vTargetTitle, 记事本
Gui, Add, Button, x20 y48 w120 h28 gPickActiveWindow, 选择当前活动窗口
Gui, Add, Button, x150 y48 w120 h28 gRefreshWindowList, 刷新窗口列表
Gui, Add, Button, x280 y48 w120 h28 gUseSelectedWindow, 使用所选窗口
Gui, Add, DropDownList, x20 y80 w520 vWindowSelector, 
Gui, Add, Text, x20 y108 w520 h20 vSelectedInfo, 当前未锁定窗口句柄

Gui, Add, Text, x20 y140 w120 h20, 按键序列:
Gui, Add, Edit, x150 y138 w360 vKeySequence ReadOnly, {TAB} -> 3 -> {ESC} -> {SPACE} (每步延迟2000ms)

Gui, Add, Text, x20 y175 w120 h20, 按键间隔(ms):
Gui, Add, Edit, x150 y173 w120 vBaseInterval, 1000

Gui, Add, Text, x20 y210 w120 h20, 循环次数(0=无限):
Gui, Add, Edit, x150 y208 w120 vLoopCount, 0

Gui, Add, CheckBox, x20 y243 vUseRandomInterval gOnToggleRandomInterval, 启用随机间隔
Gui, Add, Text, x220 y243 w70 h20, 最小(ms):
Gui, Add, Edit, x290 y241 w80 vRandMin Disabled, 800
Gui, Add, Text, x390 y243 w70 h20, 最大(ms):
Gui, Add, Edit, x460 y241 w80 vRandMax Disabled, 1200

Gui, Add, CheckBox, x20 y275 vUseRandomClick gOnToggleRandomClick, 启用随机点击坐标偏移
Gui, Add, Text, x220 y275 w55 h20, 基准X:
Gui, Add, Edit, x275 y273 w55 vClickBaseX Disabled, 200
Gui, Add, Text, x340 y275 w55 h20, 基准Y:
Gui, Add, Edit, x395 y273 w55 vClickBaseY Disabled, 200
Gui, Add, Text, x20 y305 w95 h20, 偏移范围X(±):
Gui, Add, Edit, x120 y303 w70 vClickOffsetX Disabled, 10
Gui, Add, Text, x210 y305 w95 h20, 偏移范围Y(±):
Gui, Add, Edit, x310 y303 w70 vClickOffsetY Disabled, 10

Gui, Add, Button, x20 y340 w120 h32 gStartSend, 开始
Gui, Add, Button, x155 y340 w120 h32 gStopSend, 停止
Gui, Add, Button, x290 y340 w120 h32 gClearLog, 清空日志

Gui, Add, Text, x20 y385 w120 h20, 运行状态日志:
Gui, Add, Edit, x20 y407 w520 h220 vLogBox ReadOnly -Wrap

Gui, Show, w560 h650, Windows 后台按键自动化工具
Gosub, RefreshWindowList
AppendLog("程序已启动。请配置参数后点击【开始】。")
return

PickActiveWindow:
Gui, Hide
MsgBox, 64, 选择提示, 请先点击目标程序窗口使其激活，`n然后按下 Enter 键完成选择。
KeyWait, Enter, D
pickedHwnd := WinExist("A")
Gui, Show
if (!pickedHwnd) {
    AppendLog("未获取到活动窗口。")
    return
}
WinGetTitle, pickedTitle, ahk_id %pickedHwnd%
if (pickedTitle = "")
    pickedTitle := "(无标题窗口)"
gWindowHwnd := pickedHwnd
gWindowTitle := pickedTitle
GuiControl,, TargetTitle, %pickedTitle%
GuiControl,, SelectedInfo, % "已锁定窗口句柄: " . pickedHwnd
AppendLog("已选择活动窗口: [" . pickedHwnd . "] " . pickedTitle)
return

RefreshWindowList:
gWindowMap := {}
listText := ""
WinGet, idList, List
Loop, %idList% {
    thisHwnd := idList%A_Index%
    WinGetTitle, thisTitle, ahk_id %thisHwnd%
    WinGet, mm, MinMax, ahk_id %thisHwnd%
    if (thisTitle = "")
        continue
    ; 过滤工具窗口/脚本自身窗口
    if (thisTitle = "Windows 后台按键自动化工具")
        continue
    item := "[" . thisHwnd . "] " . thisTitle
    listText .= (listText = "" ? "" : "|") . item
    gWindowMap[item] := thisHwnd
}
if (listText = "")
    listText := "(未找到可选窗口)"
GuiControl,, WindowSelector, |%listText%
GuiControl, Choose, WindowSelector, 1
AppendLog("窗口列表已刷新。")
return

UseSelectedWindow:
Gui, Submit, NoHide
if (WindowSelector = "" || WindowSelector = "(未找到可选窗口)") {
    AppendLog("请先刷新并选择有效窗口。")
    return
}
picked := gWindowMap[WindowSelector]
if (!picked) {
    AppendLog("所选窗口无效，请刷新列表后重试。")
    return
}
WinGetTitle, pickedTitle, ahk_id %picked%
gWindowHwnd := picked
gWindowTitle := pickedTitle
GuiControl,, TargetTitle, %pickedTitle%
GuiControl,, SelectedInfo, % "已锁定窗口句柄: " . picked
AppendLog("已从列表选择窗口: [" . picked . "] " . pickedTitle)
return

OnToggleRandomInterval:
Gui, Submit, NoHide
if (UseRandomInterval) {
    GuiControl, Enable, RandMin
    GuiControl, Enable, RandMax
} else {
    GuiControl, Disable, RandMin
    GuiControl, Disable, RandMax
}
return

OnToggleRandomClick:
Gui, Submit, NoHide
if (UseRandomClick) {
    GuiControl, Enable, ClickBaseX
    GuiControl, Enable, ClickBaseY
    GuiControl, Enable, ClickOffsetX
    GuiControl, Enable, ClickOffsetY
} else {
    GuiControl, Disable, ClickBaseX
    GuiControl, Disable, ClickBaseY
    GuiControl, Disable, ClickOffsetX
    GuiControl, Disable, ClickOffsetY
}
return

StartSend:
if (gRunning) {
    AppendLog("任务已在运行中。")
    return
}

Gui, Submit, NoHide

; 参数校验
gWindowTitle := TargetTitle
gKeySeq := "{TAB} -> 3 -> {ESC} -> {SPACE}"
gBaseInterval := BaseInterval + 0
gLoopCount := LoopCount + 0
gUseRandomInterval := UseRandomInterval + 0
gRandMin := RandMin + 0
gRandMax := RandMax + 0
gUseRandomClick := UseRandomClick + 0
gClickBaseX := ClickBaseX + 0
gClickBaseY := ClickBaseY + 0
gClickOffsetX := ClickOffsetX + 0
gClickOffsetY := ClickOffsetY + 0

if (gWindowTitle = "") {
    MsgBox, 48, 参数错误, 目标窗口标题不能为空。
    return
}
if (gBaseInterval < 0) {
    MsgBox, 48, 参数错误, 按键间隔不能小于0。
    return
}
if (gLoopCount < 0) {
    MsgBox, 48, 参数错误, 循环次数不能小于0。
    return
}
if (gUseRandomInterval) {
    if (gRandMin < 0 || gRandMax < 0) {
        MsgBox, 48, 参数错误, 随机间隔不能为负数。
        return
    }
    if (gRandMin > gRandMax) {
        MsgBox, 48, 参数错误, 随机间隔最小值不能大于最大值。
        return
    }
}
if (gUseRandomClick) {
    if (gClickOffsetX < 0 || gClickOffsetY < 0) {
        MsgBox, 48, 参数错误, 坐标偏移范围不能为负数。
        return
    }
}

resolvedHwnd := 0
if (gWindowHwnd) {
    if WinExist("ahk_id " . gWindowHwnd) {
        resolvedHwnd := gWindowHwnd
    } else {
        AppendLog("已锁定句柄失效，尝试按标题重新匹配。")
        gWindowHwnd := 0
    }
}
if (!resolvedHwnd) {
    resolvedHwnd := WinExist(gWindowTitle)
    if (!resolvedHwnd) {
        MsgBox, 48, 未找到窗口, 未找到匹配窗口标题:`n%gWindowTitle%
        AppendLog("未找到窗口，启动失败。")
        return
    }
    gWindowHwnd := resolvedHwnd
}

gRunning := true
gSentCount := 0
gCurrentLoop := 0
gStartTick := A_TickCount
AppendLog("任务开始：窗口=【" . gWindowTitle . "】, 句柄=" . gWindowHwnd . ", 固定序列=【Tab -> 3 -> Esc -> Space】")
SetTimer, WorkerTick, -10
return

StopSend:
if (!gRunning) {
    AppendLog("当前没有正在运行的任务。")
    return
}
gRunning := false
AppendLog("收到停止指令。")
return

WorkerTick:
if (!gRunning)
    return

if !WinExist("ahk_id " . gWindowHwnd) {
    AppendLog("目标窗口已不存在，任务停止。")
    gRunning := false
    return
}

if (gLoopCount != 0 && gCurrentLoop >= gLoopCount) {
    gRunning := false
    elapsed := (A_TickCount - gStartTick) // 1000
    AppendLog("任务完成。总次数=" . gSentCount . "，耗时=" . elapsed . "秒")
    return
}

; 可选随机点击（可用于先激活目标控件区域，支持后台NA模式）
if (gUseRandomClick) {
    Random, dx, -%gClickOffsetX%, %gClickOffsetX%
    Random, dy, -%gClickOffsetY%, %gClickOffsetY%
    rx := gClickBaseX + dx
    ry := gClickBaseY + dy
    ; NA 参数避免激活窗口
    ControlClick, x%rx% y%ry%, ahk_id %gWindowHwnd%, , Left, 1, NA
    AppendLog("随机点击: (" . rx . "," . ry . ")")
}

; 固定步骤发送：
; 1) Tab -> 延迟2000ms
; 2) 3   -> 延迟2000ms
; 3) Esc -> 延迟2000ms
; 4) Space -> 延迟2000ms
if (!SendKeyStep("{TAB}", 2000))
    AppendLog("步骤发送失败: {TAB}")
else if (!SendKeyStep("3", 2000))
    AppendLog("步骤发送失败: 3")
else if (!SendKeyStep("{ESC}", 2000))
    AppendLog("步骤发送失败: {ESC}")
else if (!SendKeyStep("{SPACE}", 2000))
    AppendLog("步骤发送失败: {SPACE}")
else {
    gSentCount += 1
    gCurrentLoop += 1
    AppendLog("固定序列发送成功，第 " . gSentCount . " 次。")
}

sleepMs := gBaseInterval
if (gUseRandomInterval) {
    Random, sleepMs, %gRandMin%, %gRandMax%
}

if (sleepMs < 0)
    sleepMs := 0

SetTimer, WorkerTick, -%sleepMs%
return

ClearLog:
GuiControl,, LogBox,
AppendLog("日志已清空。")
return

AppendLog(msg) {
    FormatTime, nowText,, yyyy-MM-dd HH:mm:ss
    GuiControlGet, oldLog,, LogBox
    newLine := "[" . nowText . "] " . msg . "`r`n"
    GuiControl,, LogBox, % oldLog . newLine
}

SendKeyStep(stepKey, delayMs) {
    global gWindowHwnd
    SetKeyDelay, 30, 30
    ControlGetFocus, focusedCtl, ahk_id %gWindowHwnd%
    if (focusedCtl != "") {
        ControlSend, %focusedCtl%, %stepKey%, ahk_id %gWindowHwnd%
    } else {
        ControlSend,, %stepKey%, ahk_id %gWindowHwnd%
    }
    if (ErrorLevel) {
        return false
    }
    Sleep, %delayMs%
    return true
}

GuiClose:
ExitApp
