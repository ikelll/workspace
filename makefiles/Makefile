PREFIX ?= /usr
DESTDIR ?= /opt/build/spice
BUILD_DIR ?= build

.PHONY: all alt usbredir spice-protocol spice spice-gtk install clean

all: usbredir spice-protocol spice spice-gtk check install
alt: alt-usb alt-protocol alt-spice alt-gtk

usbredir:
	cd usbredir && \
        rm -rf $(BUILD_DIR) && \
        meson setup $(BUILD_DIR) --prefix=$(PREFIX) && \
        ninja -C $(BUILD_DIR) && \
        ninja -C $(BUILD_DIR) install && \
        DESTDIR=$(DESTDIR) ninja -C $(BUILD_DIR) install 

spice-protocol:
	cd spice-protocol && \
        rm -rf $(BUILD_DIR) && \
        meson setup $(BUILD_DIR) --prefix=$(PREFIX) && \
        ninja -C $(BUILD_DIR) && \
        ninja -C $(BUILD_DIR) install

spice:
	cd spice && \
        rm -rf $(BUILD_DIR) && \
        meson setup $(BUILD_DIR) --prefix=$(PREFIX) -Dtests=false && \
        ninja -C $(BUILD_DIR) && \
        ninja -C $(BUILD_DIR) install

spice-gtk:
	cd spice-gtk && \
	rm -rf $(BUILD_DIR) && \
	meson setup $(BUILD_DIR) -Dwebdav=enabled -Dsmartcard=disabled -Dsasl=disabled -Dusbredir=enabled --prefix=$(PREFIX) && \
	ninja -C $(BUILD_DIR) && \
	ninja -C $(BUILD_DIR) install && \
	cd po && \
	msgfmt ru.po -o spice-gtk.mo && \
	cd .. && \
	cp po/spice-gtk.mo build/po/ru/LC_MESSAGES/ && \
	cp po/spice-gtk.mo /opt/build/build/usr/share/locale/ru/LC_MESSAGES/ && \
	DESTDIR=$(DESTDIR) ninja -C $(BUILD_DIR) install


alt-usb:
	cd usbredir && \
	cp meson.build.alt meson.build && \
	rm -rf $(BUILD_DIR) && \
	meson setup $(BUILD_DIR) -Dwerror=false --prefix=$(PREFIX) && \
	ninja -C $(BUILD_DIR) && \
	ninja -C $(BUILD_DIR) install && \
	DESTDIR=$(DESTDIR) ninja -C $(BUILD_DIR) install 

alt-protocol:	
	cd spice-protocol && \
	rm -rf $(BUILD_DIR) && \
	meson setup $(BUILD_DIR) --prefix=$(PREFIX) && \
	ninja -C $(BUILD_DIR) && \
	ninja -C $(BUILD_DIR) install

alt-spice:	
	cd spice && \
	rm -rf $(BUILD_DIR) && \
	meson setup build --prefix=/usr -Dtests=false -Dspice-common:tests=false && \
	ninja -C $(BUILD_DIR) && \
	ninja -C $(BUILD_DIR) install

alt-gtk:
	cat /etc/os-release
	cd spice-gtk && \
	rm -rf $(BUILD_DIR) && \
	meson setup $(BUILD_DIR) -Dsasl=disabled -Dusbredir=enabled --prefix=$(PREFIX) && \
	ninja -C $(BUILD_DIR) && \
	ninja -C $(BUILD_DIR) install && \
	cd po && \
	msgfmt ru.po -o spice-gtk.mo && \
	cd .. && \
	cp po/spice-gtk.mo build/po/ru/LC_MESSAGES/ && \
	cp po/spice-gtk.mo /opt/build/build/usr/share/locale/ru/LC_MESSAGES/ && \
	DESTDIR=$(DESTDIR) ninja -C $(BUILD_DIR) install
	@echo "✅ Всё собрано и установлено в: $(DESTDIR)"
	chmod u+s /opt/build/spice/usr/libexec/spice-client-glib-usb-acl-helper


install:
	@echo "✅ Всё собрано и установлено в: $(DESTDIR)"

check:
	chmod u+s /opt/build/spice/usr/libexec/spice-client-glib-usb-acl-helper

clean:
	rm -rf */$(BUILD_DIR)


