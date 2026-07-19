# 相机模块

相机能力位于 `nfs_scanner/devices/camera/`，当前统一主界面未提供相机工作区。

模块保留以下独立能力：

- 安全枚举 UVC/DirectShow 设备；
- Mock 相机；
- OpenCV 设备打开和帧读取；
- BGR → QImage 转换；
- 快照路径生成与 JPEG 保存；
- `CameraManager` 生命周期管理。

默认枚举不会通过 OpenCV 逐个打开设备。只有显式设置 `NFS_SCANNER_CAMERA_PROBE=1` 才允许探测索引；真实硬件测试还需要 `NFS_SCANNER_CAMERA_TEST=1`。

```powershell
python -m pytest -q tests\test_camera_opencv.py tests\test_camera_snapshot.py
```

后续若在唯一 UI 中增加相机页面，应复用这些模块，并作为 `MainWindow` 下的组件接入，不能新建第二套窗口。
