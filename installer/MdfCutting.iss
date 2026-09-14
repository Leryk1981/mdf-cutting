#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\MDF Cutting"
#endif
#ifndef OutputDir
  #define OutputDir "..\artifacts"
#endif

#define AppName "MDF Cutting"
#define AppExeName "MDF Cutting.exe"

[Setup]
AppId={{9B0205D5-1A7B-4206-9998-E8DB25F9B5D8}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=MDF Cutting
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=MDF Cutting Setup {#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayName={#AppName}

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Запустить {#AppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
