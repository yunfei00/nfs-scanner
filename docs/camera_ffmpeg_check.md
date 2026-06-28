# Camera FFmpeg Check Commands

本文档记录 LRCP  F1080P USB 相机在 Windows DirectShow 下的 FFmpeg / ffplay 验证命令。

> 设备名注意：`LRCP` 与 `F1080P` 之间有 **两个空格**。

## 列出 DirectShow 视频设备

```powershell
ffmpeg -list_devices true -f dshow -i dummy
```

在 stderr 输出中查找：

```text
DirectShow video devices
  "LRCP  F1080P"
```

## 查询设备能力

```powershell
ffmpeg -f dshow -list_options true -i "video=LRCP  F1080P"
```

可查看支持的 `video_size`、`framerate`、`pixel_format` 等组合。

## 单帧拍照测试（推荐 MJPEG 1080P30）

```powershell
ffmpeg -f dshow -video_size 1920x1080 -framerate 30 -vcodec mjpeg -i "video=LRCP  F1080P" -frames:v 1 -update 1 D:\camera_test.jpg
```

## 实时预览测试

```powershell
ffplay -f dshow -video_size 1920x1080 -framerate 30 -vcodec mjpeg -i "video=LRCP  F1080P"
```

## 对比：不推荐 YUYV422 1080P

YUYV422 在 1920x1080 下通常只有约 5fps，例如：

```powershell
ffmpeg -f dshow -video_size 1920x1080 -framerate 5 -pixel_format yuyv422 -i "video=LRCP  F1080P" -frames:v 1 -update 1 D:\camera_test_yuyv.jpg
```

软件默认使用 **MJPEG**，避免 1080P 预览卡顿。

## 相关文档

- [camera.md](./camera.md) — 软件内使用说明与架构
