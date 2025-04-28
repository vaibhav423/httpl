package com.example.bluetoothchat;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.content.Context;
import android.util.Log;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

public class BluetoothService {
    private static final String TAG = "BluetoothService";
    private static final String APP_NAME = "BluetoothChat";
    private static final String APP_UUID = "fa87c0d0-afac-11de-8a39-0800200c9a66";
    private static final String PREF_LAST_DEVICE = "last_connected_device";
    
    public enum ConnectionStatus {
        NONE,
        LISTENING,
        CONNECTING,
        CONNECTED
    }

    private final BluetoothAdapter bluetoothAdapter;
    private final Context context;
    private final MessageCallback messageCallback;
    private final ConnectionCallback connectionCallback;
    private AcceptThread acceptThread;
    private ConnectThread connectThread;
    private ConnectedThread connectedThread;
    private ConnectionStatus status;
    private BluetoothDevice connectedDevice;

    public interface MessageCallback {
        void onMessageReceived(String message);
    }

    public interface ConnectionCallback {
        void onConnectionStatusChanged(ConnectionStatus status, BluetoothDevice device);
    }

    public BluetoothService(Context context, MessageCallback messageCallback, ConnectionCallback connectionCallback) {
        this.context = context;
        this.messageCallback = messageCallback;
        this.connectionCallback = connectionCallback;
        this.bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        this.status = ConnectionStatus.NONE;
    }

    public void start() {
        Log.d(TAG, "start");
        
        // Cancel any thread attempting to make a connection
        if (connectThread != null) {
            connectThread.cancel();
            connectThread = null;
        }

        // Cancel any thread currently running a connection
        if (connectedThread != null) {
            connectedThread.cancel();
            connectedThread = null;
        }

        // Start the thread to listen on a BluetoothServerSocket
        if (acceptThread == null) {
            acceptThread = new AcceptThread();
            acceptThread.start();
            updateStatus(ConnectionStatus.LISTENING, null);
        }

        // Try to reconnect to last device
        String lastDeviceAddress = getLastConnectedDevice();
        if (lastDeviceAddress != null) {
            BluetoothDevice device = bluetoothAdapter.getRemoteDevice(lastDeviceAddress);
            connect(device);
        }
    }

    private String getLastConnectedDevice() {
        return context.getSharedPreferences(APP_NAME, Context.MODE_PRIVATE)
                .getString(PREF_LAST_DEVICE, null);
    }

    private void saveLastConnectedDevice(String address) {
        context.getSharedPreferences(APP_NAME, Context.MODE_PRIVATE)
                .edit()
                .putString(PREF_LAST_DEVICE, address)
                .apply();
    }

    private void updateStatus(ConnectionStatus newStatus, BluetoothDevice device) {
        status = newStatus;
        connectedDevice = device;
        if (connectionCallback != null) {
            connectionCallback.onConnectionStatusChanged(status, device);
        }
    }

    public void connect(BluetoothDevice device) {
        Log.d(TAG, "connect to: " + device);

        // Cancel any thread attempting to make a connection
        if (status == ConnectionStatus.CONNECTING) {
            if (connectThread != null) {
                connectThread.cancel();
                connectThread = null;
            }
        }

        // Cancel any thread currently running a connection
        if (connectedThread != null) {
            connectedThread.cancel();
            connectedThread = null;
        }

        // Start the thread to connect with the given device
        connectThread = new ConnectThread(device);
        connectThread.start();
        updateStatus(ConnectionStatus.CONNECTING, device);
    }

    public void sendMessage(String message) {
        if (connectedThread != null) {
            connectedThread.write(message.getBytes());
        }
    }

    public void stop() {
        Log.d(TAG, "stop");

        // Cancel any thread attempting to make a connection
        if (connectThread != null) {
            connectThread.cancel();
            connectThread = null;
        }

        // Cancel any thread currently running a connection
        if (connectedThread != null) {
            connectedThread.cancel();
            connectedThread = null;
        }

        // Cancel the accept thread
        if (acceptThread != null) {
            acceptThread.cancel();
            acceptThread = null;
        }

        updateStatus(ConnectionStatus.NONE, null);
    }

    public boolean isConnected() {
        return status == ConnectionStatus.CONNECTED;
    }

    public BluetoothDevice getConnectedDevice() {
        return connectedDevice;
    }

    public ConnectionStatus getStatus() {
        return status;
    }

    private class AcceptThread extends Thread {
        private final BluetoothServerSocket serverSocket;

        public AcceptThread() {
            BluetoothServerSocket tmp = null;
            try {
                tmp = bluetoothAdapter.listenUsingRfcommWithServiceRecord(APP_NAME, APP_UUID);
            } catch (IOException e) {
                Log.e(TAG, "Socket's listen() method failed", e);
            }
            serverSocket = tmp;
        }

        public void run() {
            if (serverSocket == null) {
                Log.e(TAG, "ServerSocket was not initialized properly");
                return;
            }

            BluetoothSocket socket = null;
            
            while (!Thread.currentThread().isInterrupted()) {
                try {
                    Log.d(TAG, "Waiting for Bluetooth connection...");
                    socket = serverSocket.accept(10000); // 10 second timeout
                    
                    if (socket != null) {
                        Log.d(TAG, "Connection accepted");
                        connected(socket);
                        try {
                            serverSocket.close();
                        } catch (IOException e) {
                            Log.e(TAG, "Could not close the connect socket", e);
                        }
                        break;
                    }
                } catch (IOException e) {
                    if (e.getMessage() != null && e.getMessage().contains("timeout")) {
                        Log.d(TAG, "Connection timeout, retrying...");
                        continue;
                    }
                    Log.e(TAG, "Fatal error in accept()", e);
                    break;
                }
            }
            
            if (Thread.currentThread().isInterrupted()) {
                Log.d(TAG, "AcceptThread interrupted");
            }
        }

        public void cancel() {
            try {
                serverSocket.close();
            } catch (IOException e) {
                Log.e(TAG, "Could not close the connect socket", e);
            }
        }
    }

    private class ConnectThread extends Thread {
        private final BluetoothSocket socket;

        public ConnectThread(BluetoothDevice device) {
            BluetoothSocket tmp = null;
            try {
                tmp = device.createRfcommSocketToServiceRecord(APP_UUID);
            } catch (IOException e) {
                Log.e(TAG, "Socket's create() method failed", e);
            }
            socket = tmp;
        }

        public void run() {
            bluetoothAdapter.cancelDiscovery();

            try {
                socket.connect();
            } catch (IOException connectException) {
                try {
                    socket.close();
                } catch (IOException closeException) {
                    Log.e(TAG, "Could not close the client socket", closeException);
                }
                return;
            }

            connected(socket);
        }

        public void cancel() {
            try {
                socket.close();
            } catch (IOException e) {
                Log.e(TAG, "Could not close the client socket", e);
            }
        }
    }

    private class ConnectedThread extends Thread {
        private final BluetoothSocket socket;
        private final InputStream inputStream;
        private final OutputStream outputStream;

        public ConnectedThread(BluetoothSocket socket) {
            if (socket == null) {
                throw new IllegalArgumentException("Socket cannot be null");
            }
            this.socket = socket;
            InputStream tmpIn = null;
            OutputStream tmpOut = null;

            try {
                tmpIn = socket.getInputStream();
                tmpOut = socket.getOutputStream();
            } catch (IOException e) {
                Log.e(TAG, "Error occurred when creating input/output streams", e);
            }

            if (tmpIn == null || tmpOut == null) {
                Log.e(TAG, "Failed to create input/output streams");
                try {
                    socket.close();
                } catch (IOException e) {
                    Log.e(TAG, "Could not close the connect socket", e);
                }
                throw new IllegalStateException("Failed to initialize streams");
            }

            inputStream = tmpIn;
            outputStream = tmpOut;
        }

        public void run() {
            if (inputStream == null || outputStream == null) {
                Log.e(TAG, "Input or output stream is null");
                return;
            }

            byte[] buffer = new byte[1024];
            int numBytes;

            while (true) {
                try {
                    numBytes = inputStream.read(buffer);
                    String message = new String(buffer, 0, numBytes);
                    messageCallback.onMessageReceived(message);
                } catch (IOException e) {
                    Log.e(TAG, "Input stream was disconnected", e);
                    break;
                }
            }
        }

        public void write(byte[] bytes) {
            if (outputStream == null) {
                Log.e(TAG, "Output stream is null");
                return;
            }
            try {
                outputStream.write(bytes);
                outputStream.flush();
            } catch (IOException e) {
                Log.e(TAG, "Error occurred when sending data", e);
            }
        }

        public void cancel() {
            try {
                socket.close();
            } catch (IOException e) {
                Log.e(TAG, "Could not close the connect socket", e);
            }
        }
    }

    private void connected(BluetoothSocket socket) {
        Log.d(TAG, "connected");

        // Cancel the thread that completed the connection
        if (connectThread != null) {
            connectThread.cancel();
            connectThread = null;
        }

        // Cancel any thread currently running a connection
        if (connectedThread != null) {
            connectedThread.cancel();
            connectedThread = null;
        }

        // Cancel the accept thread since we only want to connect to one device
        if (acceptThread != null) {
            acceptThread.cancel();
            acceptThread = null;
        }

        // Start the thread to manage the connection and perform transmissions
        connectedThread = new ConnectedThread(socket);
        connectedThread.start();

        // Save the connected device and update status
        BluetoothDevice device = socket.getRemoteDevice();
        saveLastConnectedDevice(device.getAddress());
        updateStatus(ConnectionStatus.CONNECTED, device);
    }
}
