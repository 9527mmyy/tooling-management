; ============================================================
;  工装管理系统 · 单机版 安装脚本（Inno Setup 6）
;  由 build_installer.bat 调用
;  源文件：build\dist\ToolingManagement（PyInstaller onedir 产物）
;
;  形态：纯单机。程序只监听 127.0.0.1，不对外开放；本机访问免登录。
; ============================================================

#define MyAppName "工装管理系统"
#define MyAppDirName "ToolingManagement"
#define MyAppVersion "2.2"
#define MyAppPublisher "Moy"
#define MyAppExeName "ToolingManagement.exe"

[Setup]
AppId={{7C4E1A62-3B8D-4F51-9E2A-6D5C8B0A4F31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppDirName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir=build\installer
; 带构建日期：不覆盖上一版安装包，方便现场留存与回滚
OutputBaseFilename={#MyAppDirName}-Setup-{#MyAppVersion}-20261104
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
PrivilegesRequired=admin
CloseApplications=yes
CloseApplicationsFilter=*.exe

[Languages]
Name: "chinese"; MessagesFile: "tools\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务："

[Files]
Source: "build\dist\{#MyAppDirName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; 程序目录设为只读：普通用户无法替换或篡改程序文件，只有管理员可写。
; 程序自身的数据不写在这里（数据在 %LOCALAPPDATA%），因此只读不影响运行。
Name: "{app}"; Permissions: users-readexec admins-full

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
var
  pv: String;
begin
  Result := True;
  if not RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', pv) then
    if not RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', pv) then
      if not RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', pv) then
        if SuppressibleMsgBox('未检测到 Microsoft Edge WebView2 运行库，程序的界面可能无法显示。'
                  + #13#10 + #13#10
                  + 'Win10 / Win11 通常随 Edge 浏览器自带；如缺失，可联网运行 Windows 更新，'
                  + '或从微软官网安装 WebView2 Runtime 后重试。'
                  + #13#10 + #13#10 + '是否仍要继续安装？',
                  mbConfirmation, MB_YESNO, IDYES) = IDNO then
          Result := False;
end;

// 卸载只清除程序本体。台账数据在 %LOCALAPPDATA%\ToolingManagement，一律保留，
// 便于以后重装继续使用；需要连同数据一起清理时请手动删除该目录。

// ---- 升级前数据快照 --------------------------------------------------
// 覆盖安装只写 {app}（程序目录），台账数据一律不碰。这里额外在 ssInstall
// 阶段（此时 CloseApplications 已关掉旧程序，SQLite WAL 已收尾）复制一份
// 数据库快照到数据目录下，万一升级异常可直接回滚。
// uploads 附件不在安装范围内，不会被覆盖或删除，故不需复制。

procedure BackupExistingData();
var
  dataDir, bakDir, stamp: String;
  files: array[0..4] of String;
  i: Integer;
begin
  dataDir := ExpandConstant('{localappdata}\ToolingManagement');
  if not DirExists(dataDir) then Exit;

  stamp := GetDateTimeString('yyyymmddhhnnss', '-', '-');
  bakDir := dataDir + '\backup_before_upgrade_' + stamp;
  if not ForceDirectories(bakDir) then Exit;

  files[0] := 'tooling.db';
  files[1] := 'tooling.db-wal';
  files[2] := 'tooling.db-shm';
  files[3] := 'config.json';
  files[4] := 'secret.key';
  for i := 0 to 4 do
    if FileExists(dataDir + '\' + files[i]) then
      FileCopy(dataDir + '\' + files[i], bakDir + '\' + files[i], False);

  Log('Upgrade snapshot: ' + bakDir);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then BackupExistingData();
end;
