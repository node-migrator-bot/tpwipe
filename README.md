TPWIPE
======


To get this to work on a windows architecture with python 3.2

    curl -O http://python-distribute.org/distribute_setup.py
    python distribute_setup.py
    curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    python get-pip.py

After you have installed distribute and pip you will need to add **`C:\Python32\Scripts`** to your wondows enviroment path. Then run:

    pip install requests