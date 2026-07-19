#define MyAppName "NFS Scanner"
#define MyAppVersion GetFileVersion("..\..\dist\NFSScanner\NFSScanner.exe")
#define MyAppPublisher "NFS Scanner"
#define MyAppExeName "NFSScanner.exe"

[Setup]
AppId={{A05B2584-9A07-4D47-B155-5E333F0E2326}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\NFS Scanner
DefaultGroupName=NFS Scanner
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=NFSScanner-{#MyAppVersion}-windows-x64-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "..\..\dist\NFSScanner\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\NFS Scanner"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\NFS Scanner"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标："; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 NFS Scanner"; Flags: nowait postinstall skipifsilent
