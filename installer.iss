; Руслан Саруханов
; === Inno Setup Script ===
; Инсталлятор GorizontVS-VDI-Client + UsbDk + GStreamer поддержка
; Переменные PATH и GST_PLUGIN_PATH
; URL scheme handlers: gorizontvs://, gorizontvss://
; WARNING внимательно меняйте пути до файлов на свой путь C:\Users\gorizont\Desktop\client-1.7.5\
; Актуальная версия spicy находится на рабочем столе в папке spice, оно же - финальная папка где лежит все необходимое для конечной сборки, нужно обновить vdi клиент и spicy.exe libspice-client-glib-2.0-8.dll libspice-client-gtk-3.0-5.dll - при необходимости пересобать spicy


[Setup]
AppId={{a827c859-e2f7-4b60-8d14-b8ad9527e10wa}
AppName=GorizontVS-VDI-Client
AppVersion=1.8
DefaultDirName={pf}\GorizontVS-VDI-Client
DefaultGroupName=GorizontVS-VDI-Client
OutputDir=installer
OutputBaseFilename=ГоризонтВС-VDI-Клиент_1.8_x64
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=resources\static\app.ico
WizardStyle=modern
UsePreviousLanguage=no
PrivilegesRequired=admin
UninstallDisplayIcon={app}\GorizontVS-VDI.exe
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
AppName=GorizontVS-VDI-Client
AppName_english=GorizontVS-VDI-Client
AppName_russian=ГоризонтВС-VDI-Клиент

GroupName=GorizontVS-VDI-Client
GroupName_english=GorizontVS-VDI-Client
GroupName_russian=ГоризонтВС-VDI-Клиент

ShortcutDesc=GorizontVS-VDI-Client
ShortcutDesc_english=Run GorizontVS VDI Client
ShortcutDesc_russian=Запустить ГоризонтВС VDI Клиент

UsbDkMsg=Установка драйвера UsbDk...
UsbDkMsg_english=Installing UsbDk driver...
UsbDkMsg_russian=Установка драйвера UsbDk...

[Files]
; Основной клиент и Spicy
Source: "spice\bin\spicy.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist-win\GorizontVS-VDI.exe"; DestDir: "{app}"; Flags: ignoreversion
; usb.ids
Source: "spice\usb.ids"; DestDir: "{app}\share\hwdata"; Flags: ignoreversion

; Все DLL + кодеки + GTK
;Source: "spice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "spice\bin\*.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "spice\gst-plugin-scanner.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "spice\gst-inspect-1.0.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "spice\*.dll"; DestDir: "{app}"; Flags: ignoreversion
;Source: "spice\lib\gstreamer-1.0\*"; DestDir: "{app}\lib\gstreamer-1.0"; Flags: ignoreversion recursesubdirs createallsubdirs
;Source: "spice\include\*"; DestDir: "{app}\include"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "spice\share\locale\*"; DestDir: "{app}\locale"; Flags: ignoreversion recursesubdirs createallsubdirs

; Весь GStreamer (включая libgstopenh264, opus, audio, video)
;Source: "C:\Users\gorizont\Desktop\client-1.7.5\client\source\spice\gstreamer-1.0\*"; DestDir: "{app}\gstreamer-1.0"; Flags: ignoreversion recursesubdirs createallsubdirs

; Иконка
Source: "resources\static\app.ico"; DestDir: "{app}"; Flags: ignoreversion

; UsbDk драйвер
Source: "spice\UsbDk_1.0.22_x64.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\ГоризонтВС VDI Клиент"; \
    Filename: "{app}\GorizontVS-VDI.exe"; \
    IconFilename: "{app}\app.ico"; \
    Comment: "Запустить ГоризонтВС VDI Клиент"

Name: "{commondesktop}\ГоризонтВС VDI Клиент"; \
    Filename: "{app}\GorizontVS-VDI.exe"; \
    IconFilename: "{app}\app.ico"; \
    Comment: "Запустить ГоризонтВС VDI Клиент"

[Run]
;Устанавливаем UsbDk бесшумно
Filename: "msiexec.exe"; \
  Parameters: "/i ""{tmp}\UsbDk_1.0.22_x64.msi"" /qn /norestart"; \
  StatusMsg: "{cm:UsbDkMsg}"; \
  Flags: runhidden

; Запуск клиента после установки
Filename: "{app}\GorizontVS-VDI.exe"; Description: "{cm:ShortcutDesc}"; Flags: nowait postinstall skipifsilent

[Registry]
; Добавляем {app} в PATH для запуска клиента и загрузки runtime DLL
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; \
    Check: NeedsAddPath('{app}')

Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: none; ValueName: "GST_PLUGIN_PATH"; \
    Flags: deletevalue

Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "GST_PLUGIN_PATH_1_0"; ValueData: "{app}"; \
    Flags: uninsdeletevalue

Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "GST_PLUGIN_SYSTEM_PATH_1_0"; ValueData: "{app}"; \
    Flags: uninsdeletevalue

Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "GST_PLUGIN_SCANNER"; ValueData: "{app}\gst-plugin-scanner.exe"; \
    Flags: uninsdeletevalue

; =========================
; URL Protocol handlers
; gorizontvs://  and  gorizontvss://
; =========================

; --- gorizontvs ---
Root: HKCR; Subkey: "gorizontvs"; ValueType: string; ValueName: ""; ValueData: "URL:GorizontVS Protocol"; Flags: uninsdeletekey
Root: HKCR; Subkey: "gorizontvs"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCR; Subkey: "gorizontvs\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\GorizontVS-VDI.exe"",0"
Root: HKCR; Subkey: "gorizontvs\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\GorizontVS-VDI.exe"" ""%1"""

; --- gorizontvss ---
Root: HKCR; Subkey: "gorizontvss"; ValueType: string; ValueName: ""; ValueData: "URL:GorizontVSS Protocol"; Flags: uninsdeletekey
Root: HKCR; Subkey: "gorizontvss"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCR; Subkey: "gorizontvss\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\GorizontVS-VDI.exe"",0"
Root: HKCR; Subkey: "gorizontvss\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\GorizontVS-VDI.exe"" ""%1"""

[Code]

function NormalizePathItem(S: string): string;
begin
  Result := LowerCase(Trim(S));

  while (Length(Result) > 0) and (Copy(Result, Length(Result), 1) = '\') do
    Delete(Result, Length(Result), 1);
end;

function PathContains(AppDir: string; OrigPath: string): Boolean;
var
  Item: string;
  P: Integer;
begin
  Result := False;
  AppDir := NormalizePathItem(AppDir);
  OrigPath := OrigPath + ';';

  while Pos(';', OrigPath) > 0 do
  begin
    P := Pos(';', OrigPath);
    Item := Copy(OrigPath, 1, P - 1);
    Delete(OrigPath, 1, P);

    if NormalizePathItem(Item) = AppDir then
    begin
      Result := True;
      exit;
    end;
  end;
end;

function NeedsAddPath(AppDir: string): Boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(
    HKLM,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path',
    OrigPath
  ) then
  begin
    Result := True;
    exit;
  end;

  Result := not PathContains(AppDir, OrigPath);
end;

procedure RemoveFromPath(AppDir: string);
var
  OrigPath, NewPath, Item: string;
  P: Integer;
begin
  if not RegQueryStringValue(
    HKLM,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path',
    OrigPath
  ) then
    exit;

  NewPath := '';
  AppDir := NormalizePathItem(AppDir);
  OrigPath := OrigPath + ';';

  while Pos(';', OrigPath) > 0 do
  begin
    P := Pos(';', OrigPath);
    Item := Copy(OrigPath, 1, P - 1);
    Delete(OrigPath, 1, P);

    if (Trim(Item) <> '') and (NormalizePathItem(Item) <> AppDir) then
    begin
      if NewPath <> '' then
        NewPath := NewPath + ';';

      NewPath := NewPath + Trim(Item);
    end;
  end;

  RegWriteExpandStringValue(
    HKLM,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path',
    NewPath
  );
end;

procedure RefreshEnvironment;
var
  ResultCode: Integer;
  GstPath: string;
begin
  GstPath := ExpandConstant('{app}\');

  Exec(
    'powershell.exe',
    '-Command "& {[Environment]::SetEnvironmentVariable(''GST_PLUGIN_PATH'', ''' + GstPath + ''', ''Machine'')}"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  Exec(
    'powershell.exe',
    '-Command "& {[Environment]::SetEnvironmentVariable(''GST_PLUGIN_SYSTEM_PATH_1_0'', ''' + GstPath + ''', ''Machine'')}"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    RefreshEnvironment;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemoveFromPath(ExpandConstant('{app}'));
end;

