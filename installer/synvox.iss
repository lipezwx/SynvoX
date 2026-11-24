; Inno Setup script: Windows installer for Synvox Invoice Extractor.
; Build (after PyInstaller):  iscc installer\synvox.iss
; Version can be overridden:  iscc /DAppVersion=1.2.3 installer\synvox.iss

#ifndef AppVersion
  #define AppVersion "1.2.0"
#endif
#define AppName      "Synvox Invoice Extractor"
#define AppPublisher "Synvox"
#define AppExe       "SynvoxInvoiceExtractor.exe"

[Setup]
AppId={{6F0D2C7A-5B1E-4C39-9A6E-2D8B7A41C5F3}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Synvox\InvoiceExtractor
DefaultGroupName=Synvox
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Synvox-Invoice-Extractor-Setup-{#AppVersion}
SetupIconFile=..\src\synvox_invoice\assets\synvox_icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardImageBackColor=#0D1311

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\SynvoxInvoiceExtractor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
