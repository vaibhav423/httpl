import React, { useEffect } from 'react';
import { AppRegistry } from 'react-native';
import BackgroundTimer from 'react-native-background-timer';
import dgram from 'react-native-udp';
import { Linking } from 'react-native';

const App = () => {
  useEffect(() => {
    // Start the background timer
    BackgroundTimer.runBackgroundTimer(() => {
      // Create a UDP socket
      const socket = dgram.createSocket('udp4');

      socket.bind(9898);

      socket.on('message', (msg, rinfo) => {
        console.log(`Message received: ${msg}`);
        // Open YouTube app
        Linking.openURL('vnd.youtube://');
      });

      socket.on('error', (err) => {
        console.error(`Socket error: ${err}`);
      });

      return () => {
        socket.close();
      };
    }, 1000);

    return () => {
      BackgroundTimer.stopBackgroundTimer();
    };
  }, []);

  return null; // No UI needed
};

AppRegistry.registerComponent('PersistentPortListener', () => App);
export default App;
