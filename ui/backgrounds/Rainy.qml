/*
    SPDX-FileCopyrightText: 2023 Aditya Mehra <aix.m@outlook.com>
    SPDX-License-Identifier: Apache-2.0
*/

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Shapes 1.15
import org.kde.kirigami 2.19 as Kirigami
import "components"

Rectangle {
    property bool inView: visible
    color: "transparent"

    Rain {
        anchors.fill: parent
        inView: parent.inView
    }
}
