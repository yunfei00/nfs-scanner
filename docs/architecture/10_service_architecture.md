# 10 应用装配

`ApplicationContext` 是唯一组合根：

```python
@dataclass(slots=True)
class ApplicationContext:
    device_manager: DeviceManager
    scan_manager: ScanManager
```

`MainWindow` 支持注入 context，生产启动使用 `create_application_context()`，测试可注入已经配置好的管理器。

当前不额外包装原有管理器接口。只有当多个 UI 组件确实需要同一工作流且已有测试保护时，才增加应用服务；不得为抽象而抽象。
