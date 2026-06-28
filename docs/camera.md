# USB Camera / Vision

本文档说明 NFS Scanner 商业版 UI 中的 USB UVC 相机预览与拍照功能（Camera v0.1）。

## 当前支持范围

- **相机类型**：普通 USB UVC 摄像头（Windows DirectShow）
- **采集后端**：OpenCV + `cv2.CAP_DSHOW`
- **当前测试设备**：`LRCP  F1080P`（注意 `LRCP` 与 `F1080P` 之间有 **两个空格**）
- **硬件 ID**：`USB\VID_1BCF&PID_2CC8&MI_00`

本阶段 **不包含** 标定、图像识别、复杂视觉算法。

## 推荐参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 编码 | MJPEG (`MJPG`) | 1080P 下可稳定 30fps |
| 分辨率 | 1920x1080 | 默认工作分辨率 |
| 帧率 | 30 fps | 与 MJPEG 配合最佳 |

### 不推荐参数

- **YUYV422 + 1920x1080**：实测仅约 **5 fps**，不适合实时预览
- 1080P 预览请优先使用 **MJPEG**，不要默认 YUYV422

## LRCP  F1080P 实测能力摘要

### MJPEG

| 分辨率 | 帧率 |
|--------|------|
| 1920x1080 | 5–30 fps |
| 1280x720 | 5–30 fps |
| 1280x960 | 5–30 fps |
| 800x600 | 5–30 fps |
| 640x480 | 5–30 fps |
| 320x240 | 5–30 fps |

### YUYV422

| 分辨率 | 帧率 |
|--------|------|
| 1920x1080 | 5 fps |
| 1280x720 | 5–10 fps |
| 1280x960 | 5 fps |
| 800x600 | 5–15 fps |
| 640x480 | 5–30 fps |
| 320x240 | 5–30 fps |

## 依赖安装

### Python 依赖

```bash
pip install -r requirements.txt
```

其中包含 `opencv-python`，用于 DirectShow 采集。

### FFmpeg（可选，用于设备枚举与独立验证）

Windows 推荐 [gyan.dev FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/) 或 `winget install Gyan.FFmpeg`。

安装后确认：

```powershell
ffmpeg -version
ffplay -version
```

详细命令见 [camera_ffmpeg_check.md](./camera_ffmpeg_check.md)。

## 为什么 OpenCV 只能看到 Camera 0 / Camera 1

OpenCV 在 Windows 下通过 DirectShow 打开相机时，API 形式是：

```python
cv2.VideoCapture(0, cv2.CAP_DSHOW)
cv2.VideoCapture(1, cv2.CAP_DSHOW)
```

它只暴露 **数字索引**，不会直接返回 DirectShow 的友好设备名。因此如果只用 OpenCV 探测，UI 只能显示：

```text
Camera 0 (#0)
Camera 1 (#1)
```

用户无法区分 **笔记本内置相机** 与 **外接 LRCP  F1080P**。

## 为什么 Windows 下需要 FFmpeg 辅助枚举

FFmpeg 的 DirectShow 列表命令：

```powershell
ffmpeg -list_devices true -f dshow -i dummy
```

会输出真实设备名与 Alternative name，例如：

```text
"Integrated Webcam"
    Alternative name "@device_pnp_\\?\usb#vid_0bda&pid_5520&mi_00#..."

"LRCP  F1080P"
    Alternative name "@device_pnp_\\?\usb#vid_1bcf&pid_2cc8&mi_00#..."
```

NFS Scanner 在 Windows 下 **优先使用 FFmpeg 解析上述信息**，再与 OpenCV 索引按顺序配对，UI 显示格式例如：

```text
Integrated Webcam (#0, VID_0BDA&PID_5520)
LRCP  F1080P (#1, VID_1BCF&PID_2CC8, Recommended)
```

若 FFmpeg 不可用，则回退到 OpenCV 索引枚举，并在 UI 提示：

```text
FFmpeg not found, device names unavailable.
```

## 如何区分内置相机与外接 LRCP

| 设备 | DirectShow 名称 | VID/PID |
|------|-----------------|---------|
| 笔记本内置 | `Integrated Webcam` | `VID_0BDA&PID_5520` |
| 外接 LRCP | `LRCP  F1080P`（双空格） | `VID_1BCF&PID_2CC8` |

软件默认选中规则：

1. 名称包含 `LRCP`
2. 或 VID/PID 为 `VID_1BCF&PID_2CC8`
3. 若都找不到，回退到 `#0`

推荐始终选择 **LRCP  F1080P / VID_1BCF&PID_2CC8** 作为近场扫描外接相机。

## 如何列出相机设备

### 方式 1：FFmpeg（推荐，可看到完整 DirectShow 名称）

```powershell
ffmpeg -list_devices true -f dshow -i dummy
```

在输出中查找 **DirectShow video devices** 段落，例如：

```text
"LRCP  F1080P"
```

### 方式 2：软件内

1. 启动商业版 UI
2. 打开 **相机 / 视觉** 标签页
3. 点击 **刷新设备**

## 如何查询相机能力

```powershell
ffmpeg -f dshow -list_options true -i "video=LRCP  F1080P"
```

注意设备名必须用引号包裹，并保留 **双空格**。

## 如何拍照测试

### FFmpeg 单帧拍照

```powershell
ffmpeg -f dshow -video_size 1920x1080 -framerate 30 -vcodec mjpeg -i "video=LRCP  F1080P" -frames:v 1 -update 1 D:\camera_test.jpg
```

### 软件内拍照

1. 打开 **相机 / 视觉**
2. 选择设备（如 `LRCP  F1080P` 或 `Camera 1`）
3. 分辨率选择 `1920x1080`，帧率选择 `30 fps`，编码 `MJPG`
4. 点击 **开始预览**，确认右侧有实时画面
5. 点击 **拍照**
6. 在底部日志查看：`[CAMERA] Snapshot saved: outputs/camera/camera_YYYYMMDD_HHMMSS.jpg`
7. 在控制区底部查看：**最近拍照：outputs/camera/...**

## 拍照功能

### 保存位置

```text
outputs/camera/
```

### 文件名格式

```text
camera_YYYYMMDD_HHMMSS.jpg
```

示例：

```text
outputs/camera/camera_20260628_233500.jpg
```

### 使用步骤

1. 选择设备
2. 选择 1920x1080 / 30fps / MJPG
3. 点击 **开始预览**
4. 确认有实时画面
5. 点击 **拍照**
6. 到 `outputs/camera/` 查看 JPG

### 实现说明

- 保存的是 **原始 OpenCV BGR 帧**（如 1920x1080），不是预览 QLabel 的缩放图
- 预览运行时 Worker 线程 emit 帧，UI 主线程保存 `last_frame_bgr`
- 必须先 **开始预览** 才能拍照

### 拍照常见问题

| 现象 | 处理 |
|------|------|
| 点击拍照没有反应 | 确认已开始预览；预览中「拍照」按钮才会启用 |
| 图片没有生成 | 检查 `outputs/camera/` 目录写入权限 |
| 图片尺寸太小 | 不应保存 QLabel 缩放图；应检查原始 BGR 帧分辨率 |
| 颜色异常 | `cv2.imwrite` 使用 BGR 帧，预览转换仅在显示层做 RGB |

默认保存目录（重复说明）：

```text
outputs/camera/camera_YYYYMMDD_HHMMSS.jpg
```

## 如何排查设备名空格问题

DirectShow / FFmpeg 对设备名 **大小写与空格敏感**。

| 写法 | 结果 |
|------|------|
| `LRCP  F1080P`（两个空格） | 正确 |
| `LRCP F1080P`（一个空格） | 可能找不到设备 |
| 未加引号 | PowerShell 可能截断或拆分参数 |

建议：

1. 先用 `ffmpeg -list_devices true -f dshow -i dummy` 复制 **完全一致** 的名称
2. PowerShell 中始终使用双引号：`"video=LRCP  F1080P"`

代码中的默认常量定义在：

```text
nfs_scanner/devices/camera/constants.py
```

## 如何在软件中启动相机预览

### 启动商业版 UI

```powershell
$env:NFS_SCANNER_UI="commercial"
python -m nfs_scanner.main
```

### 操作步骤

1. 切换到 **相机 / 视觉** 标签页
2. 在 **设备** 下拉框选择 `LRCP  F1080P`（若存在）
3. 分辨率选择 `1920x1080`，帧率选择 `30 fps`
4. 点击 **开始预览**
5. 需要保存时点击 **拍照**
6. 完成后点击 **停止预览**

## 与 Mock Demo 的关系

- 相机预览 **不会** 在启动时自动连接设备
- Mock 扫描、Mock 设备中心、Dry Run 闭环 **不受影响**
- 工具栏「拍照」仍是对实时画布截屏；USB 拍照在 **相机 / 视觉** 面板内完成

## 代码结构

```text
nfs_scanner/devices/camera/
  constants.py       # 默认设备名与推荐参数
  enumeration.py     # FFmpeg + OpenCV 枚举
  opencv_camera.py   # OpenCVCameraDevice
  manager.py         # CameraManager
  worker.py          # CameraWorker (QThread)
  snapshot.py        # save_camera_snapshot()
  qt_image.py        # BGR -> QImage

nfs_scanner/ui/commercial/views/vision_view.py
```

## 自动化测试

```bash
python -m unittest tests.test_camera_opencv tests.test_camera_snapshot -v
```

- 无相机环境：大部分测试仍可运行
- 真实硬件联调：设置 `NFS_SCANNER_CAMERA_TEST=1`（Windows）

## 常见问题

1. **预览黑屏**：确认未被其他软件占用；尝试降到 1280x720 / 15fps
2. **找不到设备**：检查 USB 连接；用 FFmpeg 列出设备名并核对空格
3. **OpenCV 报错**：执行 `pip install opencv-python`
4. **1080P 卡顿**：确认使用 MJPEG 而非 YUYV422
