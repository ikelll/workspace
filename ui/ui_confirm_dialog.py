# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'confirm_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_dlgConfirm(object):
    def setupUi(self, dlgConfirm):
        if not dlgConfirm.objectName():
            dlgConfirm.setObjectName(u"dlgConfirm")
        dlgConfirm.resize(420, 220)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dlgConfirm.sizePolicy().hasHeightForWidth())
        dlgConfirm.setSizePolicy(sizePolicy)
        dlgConfirm.setMinimumSize(QSize(420, 220))
        dlgConfirm.setMaximumSize(QSize(420, 220))
        dlgConfirm.setModal(True)
        self.verticalLayout_2 = QVBoxLayout(dlgConfirm)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frameDialogSurface = QFrame(dlgConfirm)
        self.frameDialogSurface.setObjectName(u"frameDialogSurface")
        self.frameDialogSurface.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameDialogSurface.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frameDialogSurface)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayoutSurface = QVBoxLayout()
        self.verticalLayoutSurface.setSpacing(11)
        self.verticalLayoutSurface.setObjectName(u"verticalLayoutSurface")
        self.verticalLayoutSurface.setContentsMargins(10, 10, 10, 10)
        self.lblDialogIcon = QLabel(self.frameDialogSurface)
        self.lblDialogIcon.setObjectName(u"lblDialogIcon")
        self.lblDialogIcon.setMinimumSize(QSize(48, 48))
        self.lblDialogIcon.setText(u"!")
        self.lblDialogIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayoutSurface.addWidget(self.lblDialogIcon)

        self.lblDialogTitle = QLabel(self.frameDialogSurface)
        self.lblDialogTitle.setObjectName(u"lblDialogTitle")
        self.lblDialogTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayoutSurface.addWidget(self.lblDialogTitle)

        self.lblDialogText = QLabel(self.frameDialogSurface)
        self.lblDialogText.setObjectName(u"lblDialogText")
        self.lblDialogText.setMinimumSize(QSize(0, 44))
        self.lblDialogText.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayoutSurface.addWidget(self.lblDialogText)

        self.lineSeparator = QFrame(self.frameDialogSurface)
        self.lineSeparator.setObjectName(u"lineSeparator")
        self.lineSeparator.setFrameShape(QFrame.Shape.HLine)
        self.lineSeparator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayoutSurface.addWidget(self.lineSeparator)

        self.horizontalLayoutButtons = QHBoxLayout()
        self.horizontalLayoutButtons.setSpacing(10)
        self.horizontalLayoutButtons.setObjectName(u"horizontalLayoutButtons")
        self.btnDialogCancel = QPushButton(self.frameDialogSurface)
        self.btnDialogCancel.setObjectName(u"btnDialogCancel")
        self.btnDialogCancel.setMinimumSize(QSize(100, 40))
        self.btnDialogCancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayoutButtons.addWidget(self.btnDialogCancel)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutButtons.addItem(self.horizontalSpacer)

        self.btnDialogConfirm = QPushButton(self.frameDialogSurface)
        self.btnDialogConfirm.setObjectName(u"btnDialogConfirm")
        self.btnDialogConfirm.setMinimumSize(QSize(100, 40))
        self.btnDialogConfirm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayoutButtons.addWidget(self.btnDialogConfirm)


        self.verticalLayoutSurface.addLayout(self.horizontalLayoutButtons)


        self.verticalLayout_4.addLayout(self.verticalLayoutSurface)


        self.verticalLayout.addWidget(self.frameDialogSurface)


        self.verticalLayout_2.addLayout(self.verticalLayout)


        self.retranslateUi(dlgConfirm)

        QMetaObject.connectSlotsByName(dlgConfirm)
    # setupUi

    def retranslateUi(self, dlgConfirm):
        dlgConfirm.setWindowTitle(QCoreApplication.translate("dlgConfirm", u"Confirm action", None))
        self.lblDialogTitle.setText("")
        self.lblDialogText.setText("")
        self.btnDialogCancel.setText(QCoreApplication.translate("dlgConfirm", u"Cancel", None))
        self.btnDialogConfirm.setText(QCoreApplication.translate("dlgConfirm", u"OK", None))
    # retranslateUi

