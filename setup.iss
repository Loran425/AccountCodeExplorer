[Setup]
; Basic information
AppName=Account Code Explorer
AppVersion=1.0.4
AppPublisher=Andrew Arneson
AppPublisherURL=https://www.github.com/Loran425
AppSupportURL=https://github.com/Loran425/AccountCodeExplorer/issues
AppUpdatesURL=http://www.github.com/Loran425/AccountCodeExplorer/releases
AppCopyright=Copyright © 2024 Andrew Arneson
DefaultDirName={localappdata}\Account Code Explorer
DefaultGroupName=Account Code Explorer
OutputDir=output
OutputBaseFilename=AccountCodeExplorerSetup
SetupIconFile=AccountCodeExplorer.ico
PrivilegesRequired=lowest

[Files]
; Include all files from the build directory
Source: "build\exe.win-amd64-3.12\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "default_config.ini"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
; Create shortcuts
Name: "{group}\Account Code Explorer"; Filename: "{app}\Account Code Explorer.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall Account Code Explorer"; Filename: "{uninstallexe}"

[Run]
; Run the application after installation
Filename: "{app}\Account Code Explorer.exe"; Description: "Launch Account Code Explorer"; Flags: nowait postinstall skipifsilent

[Code]
procedure CreateDefaultConfig;
var
  AppDataPath: string;
  ConfigFilePath: string;
begin
  // Get the path to the Roaming AppData folder
  AppDataPath := ExpandConstant('{userappdata}\Account Code Explorer');
  
  // Ensure the directory exists
  if not DirExists(AppDataPath) then
    ForceDirectories(AppDataPath);

  // Define the path for the default_config.ini file
  ConfigFilePath := AppDataPath + '\default_config.ini';

  // Copy the file from the installation directory to the Roaming AppData folder
  if not FileCopy(ExpandConstant('{app}\default_config.ini'), ConfigFilePath, False) then
    MsgBox('Failed to create default_config.ini in the Roaming AppData folder.', mbError, mb_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    CreateDefaultConfig;
end;