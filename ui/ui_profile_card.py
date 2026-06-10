# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'profile_card.ui'
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
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_profileCard(object):
    def setupUi(self, profileCard):
        if not profileCard.objectName():
            profileCard.setObjectName(u"profileCard")
        profileCard.resize(320, 80)
        profileCard.setMinimumSize(QSize(320, 72))
        self.horizontalLayout_2 = QHBoxLayout(profileCard)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lblAvatar = QLabel(profileCard)
        self.lblAvatar.setObjectName(u"lblAvatar")
        self.lblAvatar.setMinimumSize(QSize(44, 44))
        self.lblAvatar.setMaximumSize(QSize(44, 44))
        self.lblAvatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.lblAvatar)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.lblUsername = QLabel(profileCard)
        self.lblUsername.setObjectName(u"lblUsername")

        self.verticalLayout_2.addWidget(self.lblUsername)

        self.lblDetail = QLabel(profileCard)
        self.lblDetail.setObjectName(u"lblDetail")

        self.verticalLayout_2.addWidget(self.lblDetail)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.btnDelete = QPushButton(profileCard)
        self.btnDelete.setObjectName(u"btnDelete")
        self.btnDelete.setMinimumSize(QSize(28, 28))
        self.btnDelete.setMaximumSize(QSize(28, 28))
        self.btnDelete.setText(u"x")

        self.horizontalLayout.addWidget(self.btnDelete)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)


        self.retranslateUi(profileCard)

        QMetaObject.connectSlotsByName(profileCard)
    # setupUi

    def retranslateUi(self, profileCard):
        profileCard.setWindowTitle("")
        self.lblAvatar.setText("")
        self.lblUsername.setText("")
        self.lblDetail.setText("")
    # retranslateUi

