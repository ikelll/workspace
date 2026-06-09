APP_NAME        := GorizontVS-VDI-Client-Setup
BUILD_DIR       := build
DIST_DIR        := dist
OUTPUT_DIR      := /mnt/output
SOURCE_BINARY	:= dist-linux/GorizontVS-VDI
SPICE_DIR	:= /opt/build/spice/usr/
BUILD_USR	:= /opt/build/build/usr


RAW_VERSION     := $(shell sed -n '1{s/^[vV]//;p;q}' VERSION 2>/dev/null)
VERSION         ?= $(RAW_VERSION)
ifeq ($(strip $(VERSION)),)
  VERSION := 0.0.0
endif
SANITIZED_VERSION := $(shell printf '%s' "$(VERSION)" | sed 's/[^0-9A-Za-z.+~-]/-/g')

ARCH := amd64

.PHONY: rule clean check astra debian redos ubuntu
# ===================== Debian 12 =====================
sync:
	@echo "=== Синхронизация /opt/spice/usr → /opt/client/linux-build/build/usr ==="
	rsync -a $(SPICE_DIR) $(BUILD_USR)
	
rule:
	ls -la $(BUILD_USR)/libexec/spice-client-glib-usb-acl-helper
	chmod u+s $(BUILD_USR)/libexec/spice-client-glib-usb-acl-helper

debian12: check sync rule
	@mkdir -p "$(DIST_DIR)" "$(OUTPUT_DIR)"
	chmod +x packaging/postinst.sh
	chmod +x packaging/postrm.sh
	chmod +x /opt/build/dist-linux/GorizontVS-VDI.bin
	install /opt/build/dist-linux/GorizontVS-VDI.bin /opt/build/build/usr/bin/GorizontVS-VDI
	cp VERSION build/usr/share/GorizontVS-VDI/VERSION
	cat build/usr/share/GorizontVS-VDI/VERSION
	fpm -s dir -t deb \
                -n $(APP_NAME) \
                -v $(SANITIZED_VERSION) \
                --architecture $(ARCH) \
                --prefix=/ \
                --url "https://pangeo-gorizont.ru" \
                --description "GorizontVS VDI Client Setup for Debian, Ubuntu, Astra Linux OS" \
                --maintainer "https://pangeo-gorizont.ru" \
		--depends libphodav-3.0-0 \
		--depends gstreamer1.0-pulseaudio \
		--depends gstreamer1.0-x \
		--depends gstreamer1.0-plugins-bad \
		--depends gstreamer1.0-gtk3 \
		--depends gstreamer1.0-libav \
		--depends gstreamer1.0-alsa \
		--depends libcacard0 \
		--depends "libjpeg62-turbo | libjpeg62 | libjpeg-turbo8" \
		--deb-recommends gstreamer1.0-plugins-bad-apps \
		--after-install packaging/postinst.sh \
                --after-remove packaging/postrm.sh \
                -C $(BUILD_DIR) \
                -p "$(DIST_DIR)/$(APP_NAME)-$(SANITIZED_VERSION)-debian.deb"
	cp "$(DIST_DIR)/$(APP_NAME)-$(SANITIZED_VERSION)-debian.deb" "$(OUTPUT_DIR)/"


alt10:
	@mkdir -p "$(DIST_DIR)" "$(OUTPUT_DIR)"
	env VIRTUAL_ENV=/opt/venv \
		PATH=/opt/venv/bin:/usr/sbin:/usr/bin:/sbin:/bin \
		PYTHONHOME= \
		PYTHONPATH= \
		./rebuild.sh

	env VIRTUAL_ENV=/opt/venv \
		PATH=/opt/venv/bin:/usr/sbin:/usr/bin:/sbin:/bin \
		PYTHONHOME= \
		PYTHONPATH= \
	/opt/venv/bin/pyside6-deploy -c pysidedeploy.linux.spec -f
	rsync -a /opt/build/spice/ /opt/build/build
	rsync -a /opt/build/build/ /home/rpmb/RPM/SOURCES/build/
	chmod +x /opt/build/GorizontVS-VDI.bin
	install /opt/build/GorizontVS-VDI.bin /home/rpmb/RPM/SOURCES/build/usr/bin/GorizontVS-VDI
	cp VERSION /home/rpmb/RPM/SOURCES/build/usr/share/GorizontVS-VDI/VERSION
	ls -la /home/rpmb/RPM/SOURCES/build/usr/bin/
	ls -la /home/rpmb/RPM/SOURCES/build/usr/share/GorizontVS-VDI/
	runuser rpmb -c "rpmbuild -bb /home/rpmb/RPM/SPECS/alt10.spec"
	cp /home/rpmb/RPM/RPMS/x86_64/GorizontVS-VDI-Client-Setup-$(SANITIZED_VERSION)-alt10* "$(OUTPUT_DIR)/"



alt11:
	@mkdir -p "$(DIST_DIR)" "$(OUTPUT_DIR)"
	env VIRTUAL_ENV=/opt/build/venv \
            PATH=/opt/build/venv/bin:/usr/sbin:/usr/bin:/sbin:/bin \
            PYTHONHOME= \
            PYTHONPATH= \
            ./rebuild.sh
	env VIRTUAL_ENV=/opt/build/venv \
            PATH=/opt/build/venv/bin:/usr/sbin:/usr/bin:/sbin:/bin \
            PYTHONHOME= \
            PYTHONPATH= \
            /opt/build/venv/bin/pyside6-deploy -c pysidedeploy.linux.spec -f

	rsync -a /opt/build/spice/ /opt/build/build
	rsync -a /opt/build/build/ /home/rpmb/RPM/SOURCES/build/
	chmod +x /opt/build/dist-linux/GorizontVS-VDI.bin
	install /opt/build/dist-linux/GorizontVS-VDI.bin /home/rpmb/RPM/SOURCES/build/usr/bin/GorizontVS-VDI
	cp VERSION /home/rpmb/RPM/SOURCES/build/usr/share/GorizontVS-VDI/VERSION
	ls -la /home/rpmb/RPM/SOURCES/build/usr/bin/
	ls -la /home/rpmb/RPM/SOURCES/build/usr/share/GorizontVS-VDI/
	runuser rpmb -c "rpmbuild -bb /home/rpmb/RPM/SPECS/alt11.spec"
	cp /home/rpmb/RPM/RPMS/x86_64/GorizontVS-VDI-Client-Setup-$(SANITIZED_VERSION)-alt11* "$(OUTPUT_DIR)/"

redos: check sync rule
	@mkdir -p "$(DIST_DIR)" "$(OUTPUT_DIR)"
	chmod +x packaging/postinst.sh
	chmod +x packaging/postrm.sh
	chmod +x /opt/build/dist-linux/GorizontVS-VDI.bin
	install /opt/build/dist-linux/GorizontVS-VDI.bin /opt/build/build/usr/bin/GorizontVS-VDI
	cp VERSION build/usr/share/GorizontVS-VDI/VERSION
	cat build/usr/share/GorizontVS-VDI/VERSION
	fpm -s dir -t rpm \
		-n $(APP_NAME) \
		-v $(SANITIZED_VERSION) \
		--architecture $(ARCH) \
		--rpm-rpmbuild-define "_build_id_links none" \
		--prefix=/ \
		--url "https://gorizont-vs.ru" \
		--description "GorizontVS VDI Client Setup for RedOS" \
		--maintainer "https://gorizont-vs.ru" \
		--depends gstreamer1-svt-av1 \
		--depends gstreamer1-svt-vp9 \
		--depends gstreamer1-libav \
		--depends libphodav \
		--depends gstreamer1-plugin-openh264 \
		--depends gstreamer1-plugins-good \
		--depends gstreamer1-plugins-ugly \
		--depends gstreamer1-plugins-good-extras \
		--depends gstreamer1-plugins-base \
		--after-install packaging/postinst.sh \
		--after-remove packaging/postrm.sh \
		-C $(BUILD_DIR) \
		-p "$(DIST_DIR)/$(APP_NAME)-$(SANITIZED_VERSION)-redos.rpm"
	cp "$(DIST_DIR)/$(APP_NAME)-$(SANITIZED_VERSION)-redos.rpm" "$(OUTPUT_DIR)/"



check:
	@command -v fpm >/dev/null || { echo "ERROR: fpm not found. Install: gem install fpm"; exit 1; }
	@test -d "$(BUILD_DIR)" || { echo "ERROR: $(BUILD_DIR) not found. Put files there (e.g., $(BUILD_DIR)/usr/bin/yourfile)"; exit 1; }

clean:
	rm -rf "$(DIST_DIR)"

