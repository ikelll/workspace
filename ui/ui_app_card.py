# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'app_card.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_appCard(object):
    def setupUi(self, appCard):
        if not appCard.objectName():
            appCard.setObjectName(u"appCard")
        appCard.resize(168, 188)
        appCard.setMinimumSize(QSize(164, 176))
        appCard.setMaximumSize(QSize(172, 220))
        self.verticalLayout_2 = QVBoxLayout(appCard)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.hlytAppTop = QHBoxLayout()
        self.hlytAppTop.setObjectName(u"hlytAppTop")
        self.btnAppFavorite = QPushButton(appCard)
        self.btnAppFavorite.setObjectName(u"btnAppFavorite")
        self.btnAppFavorite.setMinimumSize(QSize(28, 28))
        self.btnAppFavorite.setMaximumSize(QSize(28, 28))
        self.btnAppFavorite.setText(u"\u2606")

        self.hlytAppTop.addWidget(self.btnAppFavorite)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlytAppTop.addItem(self.horizontalSpacer)

        self.btnAppMenu = QPushButton(appCard)
        self.btnAppMenu.setObjectName(u"btnAppMenu")
        self.btnAppMenu.setMinimumSize(QSize(28, 28))
        self.btnAppMenu.setMaximumSize(QSize(28, 28))
        self.btnAppMenu.setText(u"\u22ef")

        self.hlytAppTop.addWidget(self.btnAppMenu)


        self.verticalLayout_2.addLayout(self.hlytAppTop)

        self.hlyAppIcon = QHBoxLayout()
        self.hlyAppIcon.setObjectName(u"hlyAppIcon")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlyAppIcon.addItem(self.horizontalSpacer_2)

        self.lblAppIcon = QLabel(appCard)
        self.lblAppIcon.setObjectName(u"lblAppIcon")
        self.lblAppIcon.setMinimumSize(QSize(64, 64))
        self.lblAppIcon.setMaximumSize(QSize(64, 64))
        self.lblAppIcon.setText(u"A")
        self.lblAppIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hlyAppIcon.addWidget(self.lblAppIcon)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlyAppIcon.addItem(self.horizontalSpacer_3)


        self.verticalLayout_2.addLayout(self.hlyAppIcon)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.lblAppName = QLabel(appCard)
        self.lblAppName.setObjectName(u"lblAppName")
        self.lblAppName.setText(u"Application")
        self.lblAppName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblAppName.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.lblAppName)


        self.retranslateUi(appCard)

        QMetaObject.connectSlotsByName(appCard)
    # setupUi

    def retranslateUi(self, appCard):
        pass
    # retranslateUi

