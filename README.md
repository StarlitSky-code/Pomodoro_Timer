# Pomodoro Timer

番茄钟应用 - 帮助你提高工作效率的时间管理工具

## 功能

- 番茄钟计时
- 自定义工作/休息时间
- 桌面提醒

## 使用方法

### 源代码运行

```bash
python Pomodoro_Timer.py
```

### 直接运行

直接双击 `Pomodoro_Timer.exe` 运行

## 版本

- v1.0 - 初始版本

## 环境要求

- Python 3.13.9
- pygame 2.6.1

## 构建

使用 PyInstaller 构建：

```bash
pyinstaller --icon="R-C.ico" --onefile --clean Pomodoro_Timer.py
```