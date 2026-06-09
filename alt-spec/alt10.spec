name:           GorizontVS-VDI-Client-Setup
Version:        1.8
Release:        alt10
Summary:        GorizontVS VDI Client Setup for ALT Linux

Group:          Applications/Networking
License:        LGPLv2+
URL:            https://gorizont-vs.ru
Packager:       GorizontVS Dev Team

# Зависимости ALT Linux
Requires: gstreamer1.0
Requires: gstreamer
Requires: gstreamer1.0-utils
Requires: gst-plugins-base1.0
Requires: gst-plugins-ugly1.0
Requires: libqt5-gui
Requires: libqt5-widgets
Requires: libqt5-core
Requires: qt5-base-common
Requires: qt5-qtbase-gui
Requires: libxcbutil
Requires: libxcbutil-cursor
Requires: libxcbutil-icccm
Requires: libxcbutil-image
Requires: libxcbutil-keysyms
Requires: libxcb-render-util
Requires: gst-plugins-good1.0


AutoReqProv:    no

BuildArch:      x86_64
BuildRoot:      %_tmppath/%name-%version-buildroot

%description
GorizontVS VDI Client Setup for ALT Linux.


%prep
# nothing


%build
# nothing


%install
mkdir -p %buildroot/

cp -a %{_sourcedir}/build/* %buildroot/

# ALT Linux: выставляем setuid для USB ACL helper
chmod 4755 %buildroot/usr/libexec/spice-client-glib-usb-acl-helper


%clean
rm -rf %buildroot


%files
%defattr(755,root,root,755)

# bin
/usr/bin/GorizontVS-VDI
/usr/bin/spicy
/usr/bin/spicy-screenshot
/usr/bin/spicy-stats
/usr/bin/usbredirect

# libraries
/usr/lib64/libspice-client-glib-2.0.so.8.8.2
/usr/lib64/libspice-client-glib-2.0.so*
/usr/lib64/libspice-client-gtk-3.0.so.5.1.1
/usr/lib64/libspice-client-gtk-3.0.so*
/usr/lib64/libusbredirhost.so.1.0.3
/usr/lib64/libusbredirhost.so*
/usr/lib64/libusbredirparser.so.1.2.1
/usr/lib64/libusbredirparser.so*

# pkgconfig
/usr/lib64/pkgconfig/spice-client-glib-2.0.pc
/usr/lib64/pkgconfig/spice-client-gtk-3.0.pc
/usr/lib64/pkgconfig/libusbredirhost.pc
/usr/lib64/pkgconfig/libusbredirparser-0.5.pc

# usb acl helper
%attr(4755,root,root) /usr/libexec/spice-client-glib-usb-acl-helper

# includes
/usr/include/spice-client-glib-2.0/*
/usr/include/spice-client-gtk-3.0/*
/usr/include/usbredir*

# share
/usr/share/GorizontVS-VDI/images/logo.ico
/usr/share/GorizontVS-VDI/VERSION
/usr/share/applications/GorizontVS-VDI.desktop
/usr/share/polkit-1/actions/org.spice-space.lowlevelusbaccess.policy

# locales
/usr/share/locale/*/LC_MESSAGES/spice-gtk.mo

# man


%changelog
* Wed Apr 28 2026 GorizontVS Team <pangeo-gorizont.ru> - 1.8-alt10
- Initial ALT Linux packaging


