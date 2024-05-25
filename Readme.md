# Worker Client

# Pass these arguments when calling main.py:

Windows:    -d -server localhost -port 65431 -httphost localhost -httpport 65432 -blenderpath "C:\Program Files\Blender Foundation\[Folder of Blender Version]\blender.exe"
MacOS:      -d -server localhost -port 65431 -httphost localhost -httpport 65432 -blenderpath "/Applications/Blender.app/Contents/MacOs/Blender"
Linux:      -d -server localhost -port 65431 -httphost localhost -httpport 65432 -blenderpath "[Path to Blender]/blender"

You will probably have to adjust the blender path

# Probleme:
- Beim Starten der main.py des Workers mit PyCharm über die Run- oder Debug-Aktionen wird das Rendering in Blender nicht
ausgeführt. Blender kommt nicht weiter als bis zum Laden der userpref.blend. Beim Aufruf über das Terminal mit
py main.py [args] funktioniert alles einwandfrei.