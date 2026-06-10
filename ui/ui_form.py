# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.10.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QSpacerItem, QStackedWidget,
    QVBoxLayout, QWidget)

from src.svg_background import SvgBackgroundWidget
from src.widgets.unified_combobox import UnifiedComboBox

class Ui_Widget(object):
    def setupUi(self, Widget):
        if not Widget.objectName():
            Widget.setObjectName(u"Widget")
        Widget.resize(910, 575)
        Widget.setMinimumSize(QSize(910, 575))
        Widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        Widget.setAutoFillBackground(False)
        self.gridLayout = QGridLayout(Widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.stackedWidget = QStackedWidget(Widget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setMinimumSize(QSize(0, 0))
        self.pageLogin = SvgBackgroundWidget()
        self.pageLogin.setObjectName(u"pageLogin")
        self.pageLogin.setMinimumSize(QSize(0, 0))
        self.pageLogin.setBaseSize(QSize(700, 480))
        self.pageLogin.setProperty(u"svgPath", u":/img/static/login-bg.svg")
        self.verticalLayout_2 = QVBoxLayout(self.pageLogin)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.stackedWidgetLogin = QStackedWidget(self.pageLogin)
        self.stackedWidgetLogin.setObjectName(u"stackedWidgetLogin")
        self.stackedWidgetLogin.setMinimumSize(QSize(100, 100))
        self.stackedWidgetLogin.setMaximumSize(QSize(500, 16777215))
        self.stackedWidgetLogin.setStyleSheet(u"")
        self.pageServer = QWidget()
        self.pageServer.setObjectName(u"pageServer")
        self.gridLayout_2 = QGridLayout(self.pageServer)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.btnConnect = QPushButton(self.pageServer)
        self.btnConnect.setObjectName(u"btnConnect")
        self.btnConnect.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_2.addWidget(self.btnConnect, 6, 1, 1, 1)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_7, 6, 2, 1, 1)

        self.lblServerErrorBanner = QLabel(self.pageServer)
        self.lblServerErrorBanner.setObjectName(u"lblServerErrorBanner")
        self.lblServerErrorBanner.setProperty(u"hidden", True)

        self.gridLayout_2.addWidget(self.lblServerErrorBanner, 10, 1, 1, 1)

        self.verticalSpacer_9 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_9, 5, 1, 1, 1)

        self.leServerUrl = QLineEdit(self.pageServer)
        self.leServerUrl.setObjectName(u"leServerUrl")

        self.gridLayout_2.addWidget(self.leServerUrl, 4, 1, 1, 1)

        self.verticalSpacer_11 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_11, 8, 1, 1, 1)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_8, 6, 0, 1, 1)

        self.verticalSpacer_12 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer_12, 0, 1, 1, 1)

        self.verticalSpacer_21 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_21, 3, 1, 1, 1)

        self.lblServerLogo = QLabel(self.pageServer)
        self.lblServerLogo.setObjectName(u"lblServerLogo")
        self.lblServerLogo.setMinimumSize(QSize(0, 40))

        self.gridLayout_2.addWidget(self.lblServerLogo, 2, 1, 1, 1)

        self.verticalSpacer_22 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_22, 13, 1, 1, 1)

        self.btnBackToProfiles = QPushButton(self.pageServer)
        self.btnBackToProfiles.setObjectName(u"btnBackToProfiles")
        self.btnBackToProfiles.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_2.addWidget(self.btnBackToProfiles, 12, 1, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer_3, 11, 1, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 80, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.verticalSpacer_2, 1, 1, 1, 1)

        self.stackedWidgetLogin.addWidget(self.pageServer)
        self.pageCreds = QWidget()
        self.pageCreds.setObjectName(u"pageCreds")
        self.pageCreds.setStyleSheet(u"")
        self.gridLayout_5 = QGridLayout(self.pageCreds)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.btnCredsBack = QPushButton(self.pageCreds)
        self.btnCredsBack.setObjectName(u"btnCredsBack")
        self.btnCredsBack.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_5.addWidget(self.btnCredsBack, 13, 1, 1, 1)

        self.leCredsPass = QLineEdit(self.pageCreds)
        self.leCredsPass.setObjectName(u"leCredsPass")
        self.leCredsPass.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_5.addWidget(self.leCredsPass, 7, 1, 1, 1)

        self.verticalSpacer_8 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_5.addItem(self.verticalSpacer_8, 10, 1, 1, 1)

        self.btnCredsLogin = QPushButton(self.pageCreds)
        self.btnCredsLogin.setObjectName(u"btnCredsLogin")
        self.btnCredsLogin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_5.addWidget(self.btnCredsLogin, 9, 1, 1, 1)

        self.lblCredsErrorBanner = QLabel(self.pageCreds)
        self.lblCredsErrorBanner.setObjectName(u"lblCredsErrorBanner")
        self.lblCredsErrorBanner.setProperty(u"hidden", True)

        self.gridLayout_5.addWidget(self.lblCredsErrorBanner, 11, 1, 1, 1)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_5.addItem(self.horizontalSpacer_10, 5, 0, 1, 1)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_5, 12, 1, 1, 1)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_5.addItem(self.horizontalSpacer_9, 5, 2, 1, 1)

        self.verticalSpacer_13 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_5.addItem(self.verticalSpacer_13, 8, 1, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_4, 0, 1, 1, 1)

        self.lblCredsLogo = QLabel(self.pageCreds)
        self.lblCredsLogo.setObjectName(u"lblCredsLogo")

        self.gridLayout_5.addWidget(self.lblCredsLogo, 2, 1, 1, 1)

        self.cmbAuthenticator = UnifiedComboBox(self.pageCreds)
        self.cmbAuthenticator.setObjectName(u"cmbAuthenticator")
        self.cmbAuthenticator.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cmbAuthenticator.setMaxVisibleItems(66)

        self.gridLayout_5.addWidget(self.cmbAuthenticator, 5, 1, 1, 1)

        self.lblCredsServer = QLabel(self.pageCreds)
        self.lblCredsServer.setObjectName(u"lblCredsServer")
        font = QFont()
        self.lblCredsServer.setFont(font)

        self.gridLayout_5.addWidget(self.lblCredsServer, 4, 1, 1, 1)

        self.leCredsUser = QLineEdit(self.pageCreds)
        self.leCredsUser.setObjectName(u"leCredsUser")

        self.gridLayout_5.addWidget(self.leCredsUser, 6, 1, 1, 1)

        self.verticalSpacer_20 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_5.addItem(self.verticalSpacer_20, 3, 1, 1, 1)

        self.verticalSpacer_23 = QSpacerItem(20, 105, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_5.addItem(self.verticalSpacer_23, 1, 1, 1, 1)

        self.stackedWidgetLogin.addWidget(self.pageCreds)
        self.pagePassword = QWidget()
        self.pagePassword.setObjectName(u"pagePassword")
        self.gridLayout_6 = QGridLayout(self.pagePassword)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_6.addItem(self.horizontalSpacer_12, 4, 0, 1, 1)

        self.btnDeleteProfile = QPushButton(self.pagePassword)
        self.btnDeleteProfile.setObjectName(u"btnDeleteProfile")
        self.btnDeleteProfile.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_6.addWidget(self.btnDeleteProfile, 12, 1, 1, 1)

        self.verticalSpacer_17 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_6.addItem(self.verticalSpacer_17, 7, 1, 1, 1)

        self.lblPasswordLogo = QLabel(self.pagePassword)
        self.lblPasswordLogo.setObjectName(u"lblPasswordLogo")

        self.gridLayout_6.addWidget(self.lblPasswordLogo, 2, 1, 1, 1)

        self.leProfilePass = QLineEdit(self.pagePassword)
        self.leProfilePass.setObjectName(u"leProfilePass")
        self.leProfilePass.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_6.addWidget(self.leProfilePass, 5, 1, 1, 1)

        self.verticalSpacer_18 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_6.addItem(self.verticalSpacer_18, 9, 1, 1, 1)

        self.verticalSpacer_10 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_6.addItem(self.verticalSpacer_10, 3, 1, 1, 1)

        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_6.addItem(self.verticalSpacer_7, 0, 1, 1, 1)

        self.wPasswordIdentity = QWidget(self.pagePassword)
        self.wPasswordIdentity.setObjectName(u"wPasswordIdentity")
        self.verticalLayout_6 = QVBoxLayout(self.wPasswordIdentity)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalSpacer_19 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_6.addItem(self.verticalSpacer_19)

        self.lytPasswordIdentity = QVBoxLayout()
        self.lytPasswordIdentity.setObjectName(u"lytPasswordIdentity")

        self.verticalLayout_6.addLayout(self.lytPasswordIdentity)


        self.gridLayout_6.addWidget(self.wPasswordIdentity, 4, 1, 1, 1)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_6.addItem(self.horizontalSpacer_11, 4, 2, 1, 1)

        self.verticalSpacer_16 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_6.addItem(self.verticalSpacer_16, 11, 1, 1, 1)

        self.btnSwitchAccount = QPushButton(self.pagePassword)
        self.btnSwitchAccount.setObjectName(u"btnSwitchAccount")
        self.btnSwitchAccount.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_6.addWidget(self.btnSwitchAccount, 8, 1, 1, 1)

        self.btnProfileLogin = QPushButton(self.pagePassword)
        self.btnProfileLogin.setObjectName(u"btnProfileLogin")
        self.btnProfileLogin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_6.addWidget(self.btnProfileLogin, 6, 1, 1, 1)

        self.lblPwErrorBanner = QLabel(self.pagePassword)
        self.lblPwErrorBanner.setObjectName(u"lblPwErrorBanner")
        self.lblPwErrorBanner.setProperty(u"hidden", True)

        self.gridLayout_6.addWidget(self.lblPwErrorBanner, 10, 1, 1, 1)

        self.verticalSpacer_6 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_6.addItem(self.verticalSpacer_6, 13, 1, 1, 1)

        self.verticalSpacer_24 = QSpacerItem(20, 70, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_6.addItem(self.verticalSpacer_24, 1, 1, 1, 1)

        self.stackedWidgetLogin.addWidget(self.pagePassword)
        self.pageProfiles = QWidget()
        self.pageProfiles.setObjectName(u"pageProfiles")
        self.gridLayout_7 = QGridLayout(self.pageProfiles)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.scrollProfiles = QScrollArea(self.pageProfiles)
        self.scrollProfiles.setObjectName(u"scrollProfiles")
        self.scrollProfiles.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.PointingHandCursor))
        self.scrollProfiles.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 98, 50))
        self.verticalLayout_5 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.wProfilesListHost = QWidget(self.scrollAreaWidgetContents)
        self.wProfilesListHost.setObjectName(u"wProfilesListHost")
        self.verticalLayout_7 = QVBoxLayout(self.wProfilesListHost)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.lytProfilesList = QVBoxLayout()
        self.lytProfilesList.setObjectName(u"lytProfilesList")

        self.verticalLayout_7.addLayout(self.lytProfilesList)


        self.verticalLayout_5.addWidget(self.wProfilesListHost)

        self.scrollProfiles.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_7.addWidget(self.scrollProfiles, 2, 0, 1, 1)

        self.lblProfilesTitle = QLabel(self.pageProfiles)
        self.lblProfilesTitle.setObjectName(u"lblProfilesTitle")

        self.gridLayout_7.addWidget(self.lblProfilesTitle, 1, 0, 1, 1)

        self.btnAddProfile = QPushButton(self.pageProfiles)
        self.btnAddProfile.setObjectName(u"btnAddProfile")
        self.btnAddProfile.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.gridLayout_7.addWidget(self.btnAddProfile, 3, 0, 1, 1)

        self.verticalSpacer_14 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_7.addItem(self.verticalSpacer_14, 0, 0, 1, 1)

        self.verticalSpacer_15 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_7.addItem(self.verticalSpacer_15, 4, 0, 1, 1)

        self.stackedWidgetLogin.addWidget(self.pageProfiles)

        self.horizontalLayout.addWidget(self.stackedWidgetLogin)

        self.frameLoginTools = QFrame(self.pageLogin)
        self.frameLoginTools.setObjectName(u"frameLoginTools")
        self.frameLoginTools.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameLoginTools.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.frameLoginTools)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.vlyframeLoginTools = QVBoxLayout()
        self.vlyframeLoginTools.setObjectName(u"vlyframeLoginTools")
        self.hlyframeLoginTools = QHBoxLayout()
        self.hlyframeLoginTools.setObjectName(u"hlyframeLoginTools")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlyframeLoginTools.addItem(self.horizontalSpacer)

        self.btnLoginLanguage = QPushButton(self.frameLoginTools)
        self.btnLoginLanguage.setObjectName(u"btnLoginLanguage")
        self.btnLoginLanguage.setMinimumSize(QSize(45, 35))
        self.btnLoginLanguage.setMaximumSize(QSize(45, 35))
        self.btnLoginLanguage.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hlyframeLoginTools.addWidget(self.btnLoginLanguage)

        self.btnLoginThemeToggle = QPushButton(self.frameLoginTools)
        self.btnLoginThemeToggle.setObjectName(u"btnLoginThemeToggle")
        self.btnLoginThemeToggle.setMinimumSize(QSize(45, 35))
        self.btnLoginThemeToggle.setMaximumSize(QSize(45, 35))
        self.btnLoginThemeToggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hlyframeLoginTools.addWidget(self.btnLoginThemeToggle)


        self.vlyframeLoginTools.addLayout(self.hlyframeLoginTools)

        self.verticalSpacer_26 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlyframeLoginTools.addItem(self.verticalSpacer_26)


        self.horizontalLayout_9.addLayout(self.vlyframeLoginTools)


        self.horizontalLayout.addWidget(self.frameLoginTools)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.stackedWidget.addWidget(self.pageLogin)
        self.pageLoad = SvgBackgroundWidget()
        self.pageLoad.setObjectName(u"pageLoad")
        self.pageLoad.setStyleSheet(u"")
        self.pageLoad.setProperty(u"svgPath", u":/img/static/login-bg-white.svg")
        self.lytLoadingRoot = QVBoxLayout(self.pageLoad)
        self.lytLoadingRoot.setObjectName(u"lytLoadingRoot")
        self.lytLoadingRoot.setContentsMargins(0, 0, 0, 0)
        self.vspacerLoadingTop = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.lytLoadingRoot.addItem(self.vspacerLoadingTop)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 1, 1, 1, 1)

        self.svgLogoSmall = QSvgWidget(self.pageLoad)
        self.svgLogoSmall.setObjectName(u"svgLogoSmall")
        self.svgLogoSmall.setMinimumSize(QSize(142, 150))
        self.svgLogoSmall.setMaximumSize(QSize(142, 150))

        self.gridLayout_3.addWidget(self.svgLogoSmall, 0, 1, 1, 1)

        self.spinnerHost = QWidget(self.pageLoad)
        self.spinnerHost.setObjectName(u"spinnerHost")
        self.spinnerHost.setMinimumSize(QSize(80, 100))

        self.gridLayout_3.addWidget(self.spinnerHost, 2, 1, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_4, 2, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_2, 2, 2, 1, 1)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_5, 0, 2, 1, 1)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_6, 0, 0, 1, 1)


        self.lytLoadingRoot.addLayout(self.gridLayout_3)

        self.vspacerLoadingBottom = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.lytLoadingRoot.addItem(self.vspacerLoadingBottom)

        self.stackedWidget.addWidget(self.pageLoad)
        self.pageMain = SvgBackgroundWidget()
        self.pageMain.setObjectName(u"pageMain")
        self.pageMain.setStyleSheet(u"")
        self.pageMain.setProperty(u"svgPath", u":/img/static/login-bg-white.svg")
        self.verticalLayout = QVBoxLayout(self.pageMain)
#ifndef Q_OS_MAC
        self.verticalLayout.setSpacing(-1)
#endif
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.vlytMainRoot = QVBoxLayout()
        self.vlytMainRoot.setObjectName(u"vlytMainRoot")
        self.frameTopBar = QFrame(self.pageMain)
        self.frameTopBar.setObjectName(u"frameTopBar")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frameTopBar.sizePolicy().hasHeightForWidth())
        self.frameTopBar.setSizePolicy(sizePolicy)
        self.frameTopBar.setMinimumSize(QSize(72, 90))
        self.frameTopBar.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameTopBar.setFrameShadow(QFrame.Shadow.Plain)
        self.frameTopBar.setLineWidth(0)
        self.horizontalLayout_3 = QHBoxLayout(self.frameTopBar)
#ifndef Q_OS_MAC
        self.horizontalLayout_3.setSpacing(-1)
#endif
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.hlytTopBar = QHBoxLayout()
        self.hlytTopBar.setObjectName(u"hlytTopBar")
        self.frameTopBrand = QFrame(self.frameTopBar)
        self.frameTopBrand.setObjectName(u"frameTopBrand")
        self.frameTopBrand.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameTopBrand.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.frameTopBrand)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.hlytTopBrand = QHBoxLayout()
        self.hlytTopBrand.setObjectName(u"hlytTopBrand")
        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.hlytTopBrand.addItem(self.horizontalSpacer_16)

        self.lblTopLogo = QLabel(self.frameTopBrand)
        self.lblTopLogo.setObjectName(u"lblTopLogo")

        self.hlytTopBrand.addWidget(self.lblTopLogo)


        self.horizontalLayout_5.addLayout(self.hlytTopBrand)


        self.hlytTopBar.addWidget(self.frameTopBrand)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlytTopBar.addItem(self.horizontalSpacer_3)

        self.frameTopSearch = QFrame(self.frameTopBar)
        self.frameTopSearch.setObjectName(u"frameTopSearch")
        self.frameTopSearch.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameTopSearch.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frameTopSearch)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.leWorkspaceSearch = QLineEdit(self.frameTopSearch)
        self.leWorkspaceSearch.setObjectName(u"leWorkspaceSearch")
        self.leWorkspaceSearch.setMinimumSize(QSize(320, 40))
        self.leWorkspaceSearch.setMaximumSize(QSize(420, 16777215))
        self.leWorkspaceSearch.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.leWorkspaceSearch)


        self.hlytTopBar.addWidget(self.frameTopSearch)

        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlytTopBar.addItem(self.horizontalSpacer_13)

        self.btnUserAvatar = QPushButton(self.frameTopBar)
        self.btnUserAvatar.setObjectName(u"btnUserAvatar")
        self.btnUserAvatar.setMinimumSize(QSize(40, 40))
        self.btnUserAvatar.setMaximumSize(QSize(40, 40))
        self.btnUserAvatar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hlytTopBar.addWidget(self.btnUserAvatar)

        self.horizontalSpacer_17 = QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.hlytTopBar.addItem(self.horizontalSpacer_17)


        self.horizontalLayout_3.addLayout(self.hlytTopBar)


        self.vlytMainRoot.addWidget(self.frameTopBar)

        self.hlytMainBody = QHBoxLayout()
        self.hlytMainBody.setObjectName(u"hlytMainBody")
        self.hlytMainBody.setContentsMargins(-1, 0, -1, -1)
        self.frameSidebar = QFrame(self.pageMain)
        self.frameSidebar.setObjectName(u"frameSidebar")
        self.frameSidebar.setMinimumSize(QSize(0, 0))
        self.frameSidebar.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSidebar.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frameSidebar)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.vlytSidebar = QVBoxLayout()
        self.vlytSidebar.setSpacing(0)
        self.vlytSidebar.setObjectName(u"vlytSidebar")
        self.vlytSidebar.setContentsMargins(0, 12, 0, 0)
        self.frameHomeNav = QFrame(self.frameSidebar)
        self.frameHomeNav.setObjectName(u"frameHomeNav")
        self.frameHomeNav.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.frameHomeNav.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameHomeNav.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.frameHomeNav)
        self.horizontalLayout_11.setSpacing(16)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 12, 0)
        self.frameHomeIndicator = QFrame(self.frameHomeNav)
        self.frameHomeIndicator.setObjectName(u"frameHomeIndicator")
        self.frameHomeIndicator.setMinimumSize(QSize(4, 0))
        self.frameHomeIndicator.setMaximumSize(QSize(4, 16777215))
        self.frameHomeIndicator.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameHomeIndicator.setFrameShadow(QFrame.Shadow.Raised)

        self.horizontalLayout_11.addWidget(self.frameHomeIndicator)

        self.btnHomeIcon = QPushButton(self.frameHomeNav)
        self.btnHomeIcon.setObjectName(u"btnHomeIcon")
        self.btnHomeIcon.setMinimumSize(QSize(20, 20))
        self.btnHomeIcon.setMaximumSize(QSize(20, 20))
        self.btnHomeIcon.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_11.addWidget(self.btnHomeIcon)

        self.btnHome = QPushButton(self.frameHomeNav)
        self.btnHome.setObjectName(u"btnHome")
        self.btnHome.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_11.addWidget(self.btnHome)

        self.horizontalSpacer_19 = QSpacerItem(12, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_19)


        self.vlytSidebar.addWidget(self.frameHomeNav)

        self.frameAppsNav = QFrame(self.frameSidebar)
        self.frameAppsNav.setObjectName(u"frameAppsNav")
        self.frameAppsNav.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.frameAppsNav.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameAppsNav.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_12 = QHBoxLayout(self.frameAppsNav)
        self.horizontalLayout_12.setSpacing(16)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(0, 0, 12, 0)
        self.frameAppsIndicator = QFrame(self.frameAppsNav)
        self.frameAppsIndicator.setObjectName(u"frameAppsIndicator")
        self.frameAppsIndicator.setMinimumSize(QSize(4, 0))
        self.frameAppsIndicator.setMaximumSize(QSize(4, 16777215))
        self.frameAppsIndicator.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameAppsIndicator.setFrameShadow(QFrame.Shadow.Raised)

        self.horizontalLayout_12.addWidget(self.frameAppsIndicator)

        self.btnAppsIcon = QPushButton(self.frameAppsNav)
        self.btnAppsIcon.setObjectName(u"btnAppsIcon")
        self.btnAppsIcon.setMinimumSize(QSize(20, 20))
        self.btnAppsIcon.setMaximumSize(QSize(20, 20))
        self.btnAppsIcon.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_12.addWidget(self.btnAppsIcon)

        self.btnApps = QPushButton(self.frameAppsNav)
        self.btnApps.setObjectName(u"btnApps")
        self.btnApps.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_12.addWidget(self.btnApps)

        self.horizontalSpacer_20 = QSpacerItem(12, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_20)


        self.vlytSidebar.addWidget(self.frameAppsNav)

        self.frameDesktopsNav = QFrame(self.frameSidebar)
        self.frameDesktopsNav.setObjectName(u"frameDesktopsNav")
        self.frameDesktopsNav.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameDesktopsNav.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_13 = QHBoxLayout(self.frameDesktopsNav)
        self.horizontalLayout_13.setSpacing(16)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(0, 0, 12, 0)
        self.frameDesktopsIndicator = QFrame(self.frameDesktopsNav)
        self.frameDesktopsIndicator.setObjectName(u"frameDesktopsIndicator")
        self.frameDesktopsIndicator.setMinimumSize(QSize(4, 0))
        self.frameDesktopsIndicator.setMaximumSize(QSize(4, 16777215))
        self.frameDesktopsIndicator.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameDesktopsIndicator.setFrameShadow(QFrame.Shadow.Raised)

        self.horizontalLayout_13.addWidget(self.frameDesktopsIndicator)

        self.btnDesktopsIcon = QPushButton(self.frameDesktopsNav)
        self.btnDesktopsIcon.setObjectName(u"btnDesktopsIcon")
        self.btnDesktopsIcon.setMinimumSize(QSize(20, 20))
        self.btnDesktopsIcon.setMaximumSize(QSize(20, 20))
        self.btnDesktopsIcon.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_13.addWidget(self.btnDesktopsIcon)

        self.btnDesktops = QPushButton(self.frameDesktopsNav)
        self.btnDesktops.setObjectName(u"btnDesktops")
        self.btnDesktops.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout_13.addWidget(self.btnDesktops)

        self.horizontalSpacer_21 = QSpacerItem(12, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_21)


        self.vlytSidebar.addWidget(self.frameDesktopsNav)


        self.verticalLayout_4.addLayout(self.vlytSidebar)

        self.verticalSpacer_25 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_25)


        self.hlytMainBody.addWidget(self.frameSidebar)

        self.stackedWidgetMainContent = QStackedWidget(self.pageMain)
        self.stackedWidgetMainContent.setObjectName(u"stackedWidgetMainContent")
        self.pageDesktops = QWidget()
        self.pageDesktops.setObjectName(u"pageDesktops")
        self.verticalLayout_12 = QVBoxLayout(self.pageDesktops)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.vlytDesktopsPage = QVBoxLayout()
        self.vlytDesktopsPage.setObjectName(u"vlytDesktopsPage")
        self.frameDesktopsHeader = QFrame(self.pageDesktops)
        self.frameDesktopsHeader.setObjectName(u"frameDesktopsHeader")
        self.frameDesktopsHeader.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameDesktopsHeader.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.frameDesktopsHeader)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.hlytDesktopsHeader = QHBoxLayout()
        self.hlytDesktopsHeader.setObjectName(u"hlytDesktopsHeader")
        self.lblDesktopsTitle = QLabel(self.frameDesktopsHeader)
        self.lblDesktopsTitle.setObjectName(u"lblDesktopsTitle")

        self.hlytDesktopsHeader.addWidget(self.lblDesktopsTitle)

        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlytDesktopsHeader.addItem(self.horizontalSpacer_15)

        self.lblDesktopsSort = QLabel(self.frameDesktopsHeader)
        self.lblDesktopsSort.setObjectName(u"lblDesktopsSort")

        self.hlytDesktopsHeader.addWidget(self.lblDesktopsSort)

        self.cmbDesktopsSort = UnifiedComboBox(self.frameDesktopsHeader)
        self.cmbDesktopsSort.setObjectName(u"cmbDesktopsSort")
        self.cmbDesktopsSort.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hlytDesktopsHeader.addWidget(self.cmbDesktopsSort)


        self.horizontalLayout_10.addLayout(self.hlytDesktopsHeader)


        self.vlytDesktopsPage.addWidget(self.frameDesktopsHeader)

        self.scrollDesktops = QScrollArea(self.pageDesktops)
        self.scrollDesktops.setObjectName(u"scrollDesktops")
        self.scrollDesktops.setWidgetResizable(True)
        self.wDesktopsScrollHost = QWidget()
        self.wDesktopsScrollHost.setObjectName(u"wDesktopsScrollHost")
        self.wDesktopsScrollHost.setGeometry(QRect(0, 0, 98, 70))
        self.gridLayout_4 = QGridLayout(self.wDesktopsScrollHost)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.lblDesktopsEmpty = QLabel(self.wDesktopsScrollHost)
        self.lblDesktopsEmpty.setObjectName(u"lblDesktopsEmpty")
        self.lblDesktopsEmpty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblDesktopsEmpty.setWordWrap(True)

        self.verticalLayout_16.addWidget(self.lblDesktopsEmpty)


        self.gridLayout_4.addLayout(self.verticalLayout_16, 0, 0, 1, 1)

        self.gridDesktopsCards = QGridLayout()
        self.gridDesktopsCards.setObjectName(u"gridDesktopsCards")

        self.gridLayout_4.addLayout(self.gridDesktopsCards, 1, 0, 1, 1)

        self.scrollDesktops.setWidget(self.wDesktopsScrollHost)

        self.vlytDesktopsPage.addWidget(self.scrollDesktops)


        self.verticalLayout_12.addLayout(self.vlytDesktopsPage)

        self.stackedWidgetMainContent.addWidget(self.pageDesktops)
        self.pageApps = QWidget()
        self.pageApps.setObjectName(u"pageApps")
        self.verticalLayout_11 = QVBoxLayout(self.pageApps)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.vlytAppsPage = QVBoxLayout()
        self.vlytAppsPage.setObjectName(u"vlytAppsPage")
        self.frameAppsHeader = QFrame(self.pageApps)
        self.frameAppsHeader.setObjectName(u"frameAppsHeader")
        self.frameAppsHeader.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameAppsHeader.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frameAppsHeader)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.hlytAppsHeader = QHBoxLayout()
        self.hlytAppsHeader.setObjectName(u"hlytAppsHeader")
        self.lblAppsTitle = QLabel(self.frameAppsHeader)
        self.lblAppsTitle.setObjectName(u"lblAppsTitle")

        self.hlytAppsHeader.addWidget(self.lblAppsTitle)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlytAppsHeader.addItem(self.horizontalSpacer_14)

        self.lblAppsSort = QLabel(self.frameAppsHeader)
        self.lblAppsSort.setObjectName(u"lblAppsSort")

        self.hlytAppsHeader.addWidget(self.lblAppsSort)

        self.cmbAppsSort = UnifiedComboBox(self.frameAppsHeader)
        self.cmbAppsSort.setObjectName(u"cmbAppsSort")
        self.cmbAppsSort.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.hlytAppsHeader.addWidget(self.cmbAppsSort)


        self.horizontalLayout_6.addLayout(self.hlytAppsHeader)


        self.vlytAppsPage.addWidget(self.frameAppsHeader)

        self.scrollApps = QScrollArea(self.pageApps)
        self.scrollApps.setObjectName(u"scrollApps")
        self.scrollApps.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollApps.setWidgetResizable(True)
        self.wAppsScrollHost = QWidget()
        self.wAppsScrollHost.setObjectName(u"wAppsScrollHost")
        self.wAppsScrollHost.setGeometry(QRect(0, 0, 99, 70))
        self.gridLayout_8 = QGridLayout(self.wAppsScrollHost)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.lblAppsEmpty = QLabel(self.wAppsScrollHost)
        self.lblAppsEmpty.setObjectName(u"lblAppsEmpty")
        self.lblAppsEmpty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblAppsEmpty.setWordWrap(True)

        self.verticalLayout_17.addWidget(self.lblAppsEmpty)


        self.gridLayout_8.addLayout(self.verticalLayout_17, 0, 0, 1, 1)

        self.gridAppsCards = QGridLayout()
        self.gridAppsCards.setSpacing(20)
        self.gridAppsCards.setObjectName(u"gridAppsCards")

        self.gridLayout_8.addLayout(self.gridAppsCards, 1, 0, 1, 1)

        self.scrollApps.setWidget(self.wAppsScrollHost)

        self.vlytAppsPage.addWidget(self.scrollApps)


        self.verticalLayout_11.addLayout(self.vlytAppsPage)

        self.stackedWidgetMainContent.addWidget(self.pageApps)
        self.pageHome = QWidget()
        self.pageHome.setObjectName(u"pageHome")
        self.verticalLayout_13 = QVBoxLayout(self.pageHome)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.vlytHomePage = QVBoxLayout()
        self.vlytHomePage.setObjectName(u"vlytHomePage")
        self.frameHomeHeader = QFrame(self.pageHome)
        self.frameHomeHeader.setObjectName(u"frameHomeHeader")
        self.frameHomeHeader.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameHomeHeader.setFrameShadow(QFrame.Shadow.Raised)
        self.frameHomeHeader.setLineWidth(0)
        self.horizontalLayout_8 = QHBoxLayout(self.frameHomeHeader)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.hlyHomeHeader = QHBoxLayout()
        self.hlyHomeHeader.setObjectName(u"hlyHomeHeader")
        self.lblHomeTitle = QLabel(self.frameHomeHeader)
        self.lblHomeTitle.setObjectName(u"lblHomeTitle")

        self.hlyHomeHeader.addWidget(self.lblHomeTitle)

        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlyHomeHeader.addItem(self.horizontalSpacer_18)


        self.horizontalLayout_8.addLayout(self.hlyHomeHeader)


        self.vlytHomePage.addWidget(self.frameHomeHeader)

        self.scrollHome = QScrollArea(self.pageHome)
        self.scrollHome.setObjectName(u"scrollHome")
        self.scrollHome.setWidgetResizable(True)
        self.wHomeScrollHost = QWidget()
        self.wHomeScrollHost.setObjectName(u"wHomeScrollHost")
        self.wHomeScrollHost.setGeometry(QRect(0, 0, 98, 70))
        self.verticalLayout_15 = QVBoxLayout(self.wHomeScrollHost)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_18 = QVBoxLayout()
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.lblHomeEmpty = QLabel(self.wHomeScrollHost)
        self.lblHomeEmpty.setObjectName(u"lblHomeEmpty")
        self.lblHomeEmpty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblHomeEmpty.setWordWrap(True)

        self.verticalLayout_18.addWidget(self.lblHomeEmpty)


        self.verticalLayout_15.addLayout(self.verticalLayout_18)

        self.vlytHomeContent = QVBoxLayout()
        self.vlytHomeContent.setObjectName(u"vlytHomeContent")

        self.verticalLayout_15.addLayout(self.vlytHomeContent)

        self.scrollHome.setWidget(self.wHomeScrollHost)

        self.vlytHomePage.addWidget(self.scrollHome)


        self.verticalLayout_13.addLayout(self.vlytHomePage)

        self.stackedWidgetMainContent.addWidget(self.pageHome)
        self.pageSettings = QWidget()
        self.pageSettings.setObjectName(u"pageSettings")
        self.verticalLayout_8 = QVBoxLayout(self.pageSettings)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.frameSettingsPage = QFrame(self.pageSettings)
        self.frameSettingsPage.setObjectName(u"frameSettingsPage")
        self.frameSettingsPage.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSettingsPage.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_14 = QHBoxLayout(self.frameSettingsPage)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.hlySettingsPageHeader = QHBoxLayout()
        self.hlySettingsPageHeader.setObjectName(u"hlySettingsPageHeader")
        self.hlySettingsPageHeader.setContentsMargins(0, 12, -1, -1)
        self.lblSettingsTitle = QLabel(self.frameSettingsPage)
        self.lblSettingsTitle.setObjectName(u"lblSettingsTitle")

        self.hlySettingsPageHeader.addWidget(self.lblSettingsTitle)

        self.horizontalSpacer_22 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlySettingsPageHeader.addItem(self.horizontalSpacer_22)


        self.horizontalLayout_14.addLayout(self.hlySettingsPageHeader)


        self.verticalLayout_8.addWidget(self.frameSettingsPage)

        self.frameSettingsTabs = QFrame(self.pageSettings)
        self.frameSettingsTabs.setObjectName(u"frameSettingsTabs")
        self.frameSettingsTabs.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSettingsTabs.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frameSettingsTabs)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayoutSettingsTabs = QHBoxLayout()
        self.horizontalLayoutSettingsTabs.setObjectName(u"horizontalLayoutSettingsTabs")
        self.btnSettingsTabAuthentication = QPushButton(self.frameSettingsTabs)
        self.btnSettingsTabAuthentication.setObjectName(u"btnSettingsTabAuthentication")

        self.horizontalLayoutSettingsTabs.addWidget(self.btnSettingsTabAuthentication)


        self.horizontalLayout_4.addLayout(self.horizontalLayoutSettingsTabs)


        self.verticalLayout_8.addWidget(self.frameSettingsTabs)

        self.frameSettingsPanel = QFrame(self.pageSettings)
        self.frameSettingsPanel.setObjectName(u"frameSettingsPanel")
        self.frameSettingsPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSettingsPanel.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.frameSettingsPanel)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayoutSettingsPanel = QVBoxLayout()
        self.verticalLayoutSettingsPanel.setObjectName(u"verticalLayoutSettingsPanel")
        self.lblSettingsSectionTitle = QLabel(self.frameSettingsPanel)
        self.lblSettingsSectionTitle.setObjectName(u"lblSettingsSectionTitle")

        self.verticalLayoutSettingsPanel.addWidget(self.lblSettingsSectionTitle)

        self.lblSettingsSectionDescription = QLabel(self.frameSettingsPanel)
        self.lblSettingsSectionDescription.setObjectName(u"lblSettingsSectionDescription")

        self.verticalLayoutSettingsPanel.addWidget(self.lblSettingsSectionDescription)

        self.rbSettingsActiveDirectory = QRadioButton(self.frameSettingsPanel)
        self.rbSettingsActiveDirectory.setObjectName(u"rbSettingsActiveDirectory")

        self.verticalLayoutSettingsPanel.addWidget(self.rbSettingsActiveDirectory)

        self.rbSettingsAuthentik = QRadioButton(self.frameSettingsPanel)
        self.rbSettingsAuthentik.setObjectName(u"rbSettingsAuthentik")

        self.verticalLayoutSettingsPanel.addWidget(self.rbSettingsAuthentik)

        self.rbSettingsDefault = QRadioButton(self.frameSettingsPanel)
        self.rbSettingsDefault.setObjectName(u"rbSettingsDefault")

        self.verticalLayoutSettingsPanel.addWidget(self.rbSettingsDefault)

        self.frameSettingsStatus = QFrame(self.frameSettingsPanel)
        self.frameSettingsStatus.setObjectName(u"frameSettingsStatus")
        self.frameSettingsStatus.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameSettingsStatus.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.frameSettingsStatus)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.horizontalLayoutSettingsStatus = QVBoxLayout()
        self.horizontalLayoutSettingsStatus.setObjectName(u"horizontalLayoutSettingsStatus")
        self.lblSettingsStatusBadge = QLabel(self.frameSettingsStatus)
        self.lblSettingsStatusBadge.setObjectName(u"lblSettingsStatusBadge")

        self.horizontalLayoutSettingsStatus.addWidget(self.lblSettingsStatusBadge)

        self.lblSettingsStatusHint = QLabel(self.frameSettingsStatus)
        self.lblSettingsStatusHint.setObjectName(u"lblSettingsStatusHint")

        self.horizontalLayoutSettingsStatus.addWidget(self.lblSettingsStatusHint)


        self.verticalLayout_10.addLayout(self.horizontalLayoutSettingsStatus)


        self.verticalLayoutSettingsPanel.addWidget(self.frameSettingsStatus)


        self.verticalLayout_9.addLayout(self.verticalLayoutSettingsPanel)


        self.verticalLayout_8.addWidget(self.frameSettingsPanel)

        self.verticalSpacer_27 = QSpacerItem(20, 67, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_27)

        self.stackedWidgetMainContent.addWidget(self.pageSettings)

        self.hlytMainBody.addWidget(self.stackedWidgetMainContent)


        self.vlytMainRoot.addLayout(self.hlytMainBody)


        self.verticalLayout.addLayout(self.vlytMainRoot)

        self.stackedWidget.addWidget(self.pageMain)

        self.gridLayout.addWidget(self.stackedWidget, 0, 0, 1, 1)


        self.retranslateUi(Widget)

        self.stackedWidget.setCurrentIndex(2)
        self.stackedWidgetLogin.setCurrentIndex(2)
        self.stackedWidgetMainContent.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Gorizont-VS VDI", None))
        self.btnConnect.setText(QCoreApplication.translate("Widget", u"Continue", None))
        self.lblServerErrorBanner.setText("")
        self.leServerUrl.setText("")
        self.leServerUrl.setPlaceholderText(QCoreApplication.translate("Widget", u"Enter the server url or token", None))
        self.lblServerLogo.setText("")
        self.btnBackToProfiles.setText(QCoreApplication.translate("Widget", u"\u2190 Back to profiles", None))
        self.btnCredsBack.setText(QCoreApplication.translate("Widget", u"\u2190 Back", None))
        self.leCredsPass.setText("")
        self.leCredsPass.setPlaceholderText(QCoreApplication.translate("Widget", u"Password", None))
        self.btnCredsLogin.setText(QCoreApplication.translate("Widget", u"Login", None))
        self.lblCredsErrorBanner.setText("")
        self.lblCredsLogo.setText("")
        self.cmbAuthenticator.setProperty(u"comboVariant", QCoreApplication.translate("Widget", u"primary", None))
        self.lblCredsServer.setText("")
        self.leCredsUser.setText("")
        self.leCredsUser.setPlaceholderText(QCoreApplication.translate("Widget", u"Username", None))
        self.btnDeleteProfile.setText(QCoreApplication.translate("Widget", u"Delete a profile", None))
        self.lblPasswordLogo.setText("")
        self.leProfilePass.setText("")
        self.leProfilePass.setPlaceholderText(QCoreApplication.translate("Widget", u"Password", None))
        self.btnSwitchAccount.setText(QCoreApplication.translate("Widget", u"Another account", None))
        self.btnProfileLogin.setText(QCoreApplication.translate("Widget", u"Login", None))
        self.lblPwErrorBanner.setText("")
        self.lblProfilesTitle.setText(QCoreApplication.translate("Widget", u"Select a profile", None))
        self.btnAddProfile.setText(QCoreApplication.translate("Widget", u"+ Add connection", None))
        self.btnLoginLanguage.setText("")
        self.btnLoginThemeToggle.setText("")
        self.lblTopLogo.setText("")
        self.leWorkspaceSearch.setPlaceholderText(QCoreApplication.translate("Widget", u"Search in Gorizont-VS VDI", None))
        self.btnUserAvatar.setText("")
        self.btnHomeIcon.setText("")
        self.btnHome.setText(QCoreApplication.translate("Widget", u"Home", None))
        self.btnAppsIcon.setText("")
        self.btnApps.setText(QCoreApplication.translate("Widget", u"Apps", None))
        self.btnDesktopsIcon.setText("")
        self.btnDesktops.setText(QCoreApplication.translate("Widget", u"Desktops", None))
        self.lblDesktopsTitle.setText(QCoreApplication.translate("Widget", u"All Desktops", None))
        self.lblDesktopsSort.setText(QCoreApplication.translate("Widget", u"Sort by:", None))
        self.cmbDesktopsSort.setProperty(u"comboVariant", QCoreApplication.translate("Widget", u"compact", None))
        self.lblDesktopsEmpty.setText(QCoreApplication.translate("Widget", u"No desktops", None))
        self.lblAppsTitle.setText(QCoreApplication.translate("Widget", u"All Apps", None))
        self.lblAppsSort.setText(QCoreApplication.translate("Widget", u"Sort by:", None))
        self.cmbAppsSort.setProperty(u"comboVariant", QCoreApplication.translate("Widget", u"compact", None))
        self.lblAppsEmpty.setText(QCoreApplication.translate("Widget", u"No applications", None))
        self.lblHomeTitle.setText(QCoreApplication.translate("Widget", u"Home", None))
        self.lblHomeEmpty.setText(QCoreApplication.translate("Widget", u"Home is empty", None))
        self.lblSettingsTitle.setText(QCoreApplication.translate("Widget", u"Settings", None))
        self.btnSettingsTabAuthentication.setText(QCoreApplication.translate("Widget", u"Authentication", None))
        self.lblSettingsSectionTitle.setText("")
        self.lblSettingsSectionDescription.setText("")
        self.rbSettingsActiveDirectory.setText("")
        self.rbSettingsAuthentik.setText("")
        self.rbSettingsDefault.setText("")
        self.lblSettingsStatusBadge.setText("")
        self.lblSettingsStatusHint.setText("")
    # retranslateUi

