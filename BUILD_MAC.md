cd /Users/kirillvasiukov/Desktop/workspace/workspace                     

python3.11 -m venv venv
source venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install "PySide6==6.9.*" "Nuitka==2.7.11" ordered-set zstandard

python -c "import sys; print(sys.executable)"
python -m pip show PySide6 Nuitka pyspnego cryptography
./rebuild.sh
venv/bin/pyside6-deploy -c pysidedeploy.mac.spec









Распакуйте файлы в корень проекта.
Создайте и активируйте venv.
Установите зависимости проекта, а также PySide6, Nuitka, ordered-set, zstandard, pyspnego.
Запустите rebuild.bat.
Соберите через:
venv\Scripts\pyside6-deploy -c pysidedeploy.windows.spec