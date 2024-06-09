# Worker Client

## How to run
1. Server: Start with `py main.py` (for Server's main.py)
2. Worker: Start with `py main.py [args(see below)]` (for Worker's main.py)
3. Worker: Enter `r` or `register` when prompted to enter command (alternatively add `-ar` or `-autoregister` to Worker args)
4. Wait until registration is complete (can take several seconds)
5. Server: Press enter to send file

### Pass these arguments when calling Workers' main.py:

- Windows:    `-d -server localhost -port 65431 -httphost localhost -httpport 65432 -blenderpath "C:\Program Files\Blender Foundation\[Folder of Blender Version]\blender.exe"`
- MacOS:      `-d -server localhost -port 65431 -httphost localhost -httpport 65432 -blenderpath "/Applications/Blender.app/Contents/MacOs/Blender"`
- Linux:      `-d -server localhost -port 65431 -httphost localhost -httpport 65432 -blenderpath "[Path to Blender]/blender"`

Don't forget to adjust the blender path
Hint for UNIX-based systems: When referring to current user's directory write `~` in front of "". Otherwise it is considered a folder/file name.
Hint for Windows: If a path ends with a `\` (indicating it's a directory), write `\\` if the `\` is followed by a `"` 

## Probleme:
- Beim Starten der main.py des Workers mit PyCharm über die Run- oder Debug-Aktionen wird das Rendering in Blender nicht
ausgeführt. Blender kommt nicht weiter als bis zum Laden der userpref.blend. Beim Aufruf über das Terminal mit
`py main.py *[args]*` funktioniert alles einwandfrei. (Windows 10, PyCharm 2024.1.1, Python 3.12.3)