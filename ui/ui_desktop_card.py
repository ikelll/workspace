# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'desktop_card.ui'
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

class Ui_desktopCard(object):
    def setupUi(self, desktopCard):
        if not desktopCard.objectName():
            desktopCard.setObjectName(u"desktopCard")
        desktopCard.resize(360, 116)
        desktopCard.setMinimumSize(QSize(360, 116))
        desktopCard.setMaximumSize(QSize(360, 116))
        self.horizontalLayout_2 = QHBoxLayout(desktopCard)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.btnDesktopFavorite = QPushButton(desktopCard)
        self.btnDesktopFavorite.setObjectName(u"btnDesktopFavorite")
        self.btnDesktopFavorite.setMinimumSize(QSize(28, 28))
        self.btnDesktopFavorite.setMaximumSize(QSize(28, 28))
        self.btnDesktopFavorite.setText(u"\u2606")

        self.verticalLayout_5.addWidget(self.btnDesktopFavorite)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)


        self.horizontalLayout_2.addLayout(self.verticalLayout_5)

        self.lblDesktopIcon = QLabel(desktopCard)
        self.lblDesktopIcon.setObjectName(u"lblDesktopIcon")
        self.lblDesktopIcon.setMinimumSize(QSize(64, 64))
        self.lblDesktopIcon.setMaximumSize(QSize(64, 64))
        self.lblDesktopIcon.setText(u"D")
        self.lblDesktopIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.lblDesktopIcon)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.vlytDesktopText = QVBoxLayout()
        self.vlytDesktopText.setSpacing(4)
        self.vlytDesktopText.setObjectName(u"vlytDesktopText")
        self.lblDesktopName = QLabel(desktopCard)
        self.lblDesktopName.setObjectName(u"lblDesktopName")
        self.lblDesktopName.setText(u"Desktop")
        self.lblDesktopName.setWordWrap(True)

        self.vlytDesktopText.addWidget(self.lblDesktopName)


        self.horizontalLayout_2.addLayout(self.vlytDesktopText)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.lblDesktopSubtitle = QLabel(desktopCard)
        self.lblDesktopSubtitle.setObjectName(u"lblDesktopSubtitle")
        self.lblDesktopSubtitle.setText(u"Virtual desktop")
        self.lblDesktopSubtitle.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.lblDesktopSubtitle)

        self.lblDesktopTransport = QLabel(desktopCard)
        self.lblDesktopTransport.setObjectName(u"lblDesktopTransport")

        self.verticalLayout_3.addWidget(self.lblDesktopTransport)


        self.horizontalLayout_2.addLayout(self.verticalLayout_3)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.vlytDesktopRight = QVBoxLayout()
        self.vlytDesktopRight.setSpacing(8)
        self.vlytDesktopRight.setObjectName(u"vlytDesktopRight")
        self.btnDesktopMenu = QPushButton(desktopCard)
        self.btnDesktopMenu.setObjectName(u"btnDesktopMenu")
        self.btnDesktopMenu.setMinimumSize(QSize(28, 28))
        self.btnDesktopMenu.setMaximumSize(QSize(28, 28))
        self.btnDesktopMenu.setText(u"\u22ef")

        self.vlytDesktopRight.addWidget(self.btnDesktopMenu)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlytDesktopRight.addItem(self.verticalSpacer)


        self.horizontalLayout_2.addLayout(self.vlytDesktopRight)


        self.retranslateUi(desktopCard)

        QMetaObject.connectSlotsByName(desktopCard)
    # setupUi

    def retranslateUi(self, desktopCard):
        self.lblDesktopTransport.setText(QCoreApplication.translate("desktopCard", u"Transport", None))
        pass
    # retranslateUi

