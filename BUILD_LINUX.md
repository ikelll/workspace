sudo apt update
sudo apt install -y python3 python3-venv build-essential patchelf
apt install -y libkrb5-dev или dnf install -y krb5-devel
cd /path/to/your/project

python3 -m venv venv
source venv/bin/activate

python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install "PySide6==6.9.*" "Nuitka==2.7.11" ordered-set zstandard pyspnego krb5

chmod +x rebuild.sh
./rebuild.sh

mkdir dist-linux


source venv/bin/activate
venv/bin/pyside6-deploy -c pysidedeploy.linux.spec

