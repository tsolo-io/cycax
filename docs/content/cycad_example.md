# CyCAD example

Basic Example of installing CyCAx and using CyCAD
-------------------------------------------------

We will assume you are working from $HOME/src. And that git, python>=3.10, and python hatch is installed.

Git clone CyCAx
===============

```
cd ~/src
git clone https://github.com/tsolo-io/cycax.git
```

Build CyCAx
===========
```
cd ~/src/cycax
hatch build
```

Create playpen
==============

```
mkdir ~/src/playpen
cd ~/src/playpen
python3 -m venv .venv
source .venv/bin/activate
pip install --force-reinstall $(ls ../cycax/dist/cycax-*.whl | sort | head -n1)
```

Example assembly
================

Create the file *~/src/playpen/main.py* with the following content.

``` py
#!/usr/bin/env python3

from cycax.cycad import Assembly
from cycax.cycad import Part3dPrint

class ConnCube(Part3dPrint):

    def __init__(self):
        super().__init__(name="ConnCube")

assembly = Assembly("test")
conn_cube = ConnCube()
conn_cube.save()
conn_cube.render()
assembly.save()
assembly.render()
```

Update and run example assembly
===============================

```
cd ~/src/playpen
chmod a+x main.py
pip install --force-reinstall $(ls ../cycax/dist/cycax-*.whl | sort | head -n1)
./main.py
```

