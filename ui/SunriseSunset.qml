/*
    SPDX-FileCopyrightText: 2023 Aditya Mehra <aix.m@outlook.com>
    SPDX-License-Identifier: Apache-2.0
*/

import QtQuick.Layouts 1.15
import QtQuick 2.15
import QtQuick.Controls 2.15
import org.kde.kirigami 2.19 as Kirigami
import Mycroft 1.0 as Mycroft

WeatherDelegate {
    id: root

    GridLayout {
        id: sunriseSunset
        anchors.top: parent.top
        anchors.topMargin: root.locBoxHeight
        anchors.bottom: parent.bottom
        width: parent.width
        columns: 2
        columnSpacing: Mycroft.Units.gridUnit * 2

        ColumnLayout {
            id: sunrise
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Mycroft.Units.gridUnit

            Image {
                Layout.preferredWidth: width
                Layout.preferredHeight: width
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                id: sunriseImage
                source: "images/sunrise.svg"
            }

            Label {
                id: sunriseTime
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                font.weight: Font.Bold
                font.pixelSize: width * 0.3
                color: dayNightTime == "day" ? "black" : "white"
                text: sessionData.sunrise
            }

            Label {
                id: sunriseAm
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                font.styleName: "Thin"
                font.pixelSize: width * 0.25
                visible: sessionData.ampm
                enabled: sessionData.ampm
                color: dayNightTime == "day" ? "black" : "white"
                text: sessionData.ampm ? "AM" : ""
            }
        }

        ColumnLayout {
            id: sunset
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Mycroft.Units.gridUnit

            Image {
                Layout.preferredWidth: width
                Layout.preferredHeight: width
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                id: sunsetImage
                source: "images/sunset.svg"
            }

            Label {
                id: sunsetTime
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                font.weight: Font.Bold
                font.pixelSize: width * 0.3
                color: dayNightTime == "day" ? "black" : "white"
                text: sessionData.sunset
            }

            Label {
                id: sunsetPm
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                font.styleName: "Thin"
                font.pixelSize: width * 0.25
                visible: sessionData.ampm
                enabled: sessionData.ampm
                color: dayNightTime == "day" ? "black" : "white"
                text: sessionData.ampm ? "PM" : ""
            }
        }
    }
}
