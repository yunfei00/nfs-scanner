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
2. 选择设备与参数
3. 点击 **开始预览**
4. 点击 **拍照**

默认保存目录：

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
  qt_image.py        # BGR -> QImage

nfs_scanner/ui/commercial/views/vision_view.py
```

## 自动化测试

```bash
python -m unittest tests.test_camera_opencv -v
```

- 无相机环境：大部分测试仍可运行
- 真实硬件联调：设置 `NFS_SCANNER_CAMERA_TEST=1`（Windows）

## 常见问题

1. **预览黑屏**：确认未被其他软件占用；尝试降到 1280x720 / 15fps
2. **找不到设备**：检查 USB 连接；用 FFmpeg 列出设备名并核对空格
3. **OpenCV 报错**：执行 `pip install opencv-python`
4. **1080P 卡顿**：确认使用 MJPEG 而非 YUYV422
