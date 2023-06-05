import QtQuick.Layouts 1.4
import QtQuick 2.4
import QtQuick.Controls 2.0
import org.kde.kirigami 2.4 as Kirigami

import Mycroft 1.0 as Mycroft

WeatherDelegate {
    id: root

    GridLayout {
        id: sunriseSunset
        anchors.top: parent.top
        anchors.topMargin: parent.parent.locBoxHeight
        anchors.bottom: parent.bottom
        rows: 2
        columns: 1
        rowSpacing: 0
        width: parent.width

        RowLayout {
            id: sunrise

            Rectangle {
                id: sunriseBackground
                color: "transparent"
                Layout.preferredWidth: sunriseSunset.width * 0.15
                Layout.preferredHeight: sunriseSunset.width * 0.15
                Layout.leftMargin: sunriseSunset.width * 0.15
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter

                Image {
                    id: sunriseImage
                    source: "images/sunrise.svg"
                    anchors.fill: parent
                }
            }

            Label {
                id: sunriseTime
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.weight: Font.Bold
                font.pixelSize: sunriseSunset.width * 0.1
                color: dayNightTime == "day" ? "black" : "white"
                text: sessionData.sunrise
            }
        }

        RowLayout {
            id: sunset

            Rectangle {
                id: sunsetBackground
                color: "transparent"
                Layout.preferredWidth: sunriseSunset.width * 0.15
                Layout.preferredHeight: sunriseSunset.width * 0.15
                Layout.leftMargin: sunriseSunset.width * 0.15
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter

                Image {
                    id: sunsetImage
                    source: "images/sunset.svg"
                    anchors.fill: parent
                }
            }

            Label {
                id: sunsetTime
                // Layout.fillWidth: true
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.weight: Font.Bold
                font.pixelSize: sunriseSunset.width * 0.1
                color: dayNightTime == "day" ? "black" : "white"
                text: sessionData.sunset
            }
        }
    }
}
