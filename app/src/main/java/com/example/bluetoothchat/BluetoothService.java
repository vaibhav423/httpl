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
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

public class BluetoothService {
    private static final String TAG = "BluetoothService";
    private static final String APP_NAME = "BluetoothChat";
    private static final UUID APP_UUID = UUID.fromString("fa87c0d0-afac-11de-8a39-0800200c9a66");
    private static final String PREF_LAST_DEVICE = "last_connected_device";
    private static final int MAX_BUFFER_SIZE = 1024;

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
    private final Object lock = new Object();

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

    public synchronized void start() {
        Log.d(TAG, "start");

        // Cancel any current connections
        cancelConnectThread();
        cancelConnectedThread();

        // Start the accept thread
        if (acceptThread == null) {
            acceptThread = new AcceptThread();
            acceptThread.start();
            updateStatus(ConnectionStatus.LISTENING, null);
        }
    }

    public synchronized void connect(BluetoothDevice device) {
        Log.d(TAG, "Connecting to: " + device.getName());

        // Cancel any current attempts to connect
        if (status == ConnectionStatus.CONNECTING) {
            cancelConnectThread();
        }

        // Cancel any current connections
        if (connectedThread != null) {
            cancelConnectedThread();
        }

        // Start the connection thread
        connectThread = new ConnectThread(device);
        connectThread.start();
        updateStatus(ConnectionStatus.CONNECTING, device);
    }

    public synchronized void connected(BluetoothSocket socket) {
        Log.d(TAG, "Connected to " + socket.getRemoteDevice().getName());

        // Cancel any current threads
        cancelConnectThread();
        cancelConnectedThread();
        cancelAcceptThread();

        // Start the connected thread
        connectedThread = new ConnectedThread(socket);
        connectedThread.start();

        // Save device and update status
        BluetoothDevice device = socket.getRemoteDevice();
        saveLastConnectedDevice(device.getAddress());
        updateStatus(ConnectionStatus.CONNECTED, device);
    }

    public synchronized void stop() {
        Log.d(TAG, "stop");
        cancelConnectThread();
        cancelConnectedThread();
        cancelAcceptThread();
        updateStatus(ConnectionStatus.NONE, null);
    }

    private void cancelConnectThread() {
        if (connectThread != null) {
            connectThread.cancel();
            connectThread = null;
        }
    }

    private void cancelConnectedThread() {
        if (connectedThread != null) {
            connectedThread.cancel();
            connectedThread = null;
        }
    }

    private void cancelAcceptThread() {
        if (acceptThread != null) {
            acceptThread.cancel();
            acceptThread = null;
        }
    }

    private synchronized void connectionFailed() {
        updateStatus(ConnectionStatus.NONE, null);
        start();
    }

    private synchronized void connectionLost() {
        updateStatus(ConnectionStatus.NONE, null);
        start();
    }

    public synchronized void sendMessage(String message) {
        if (status != ConnectionStatus.CONNECTED || connectedThread == null) {
            Log.w(TAG, "Cannot send message - not connected");
            return;
        }
        
        // Convert message to bytes and add length prefix
        byte[] messageBytes = message.getBytes(StandardCharsets.UTF_8);
        ByteBuffer buffer = ByteBuffer.allocate(4 + messageBytes.length);
        buffer.putInt(messageBytes.length);
        buffer.put(messageBytes);
        
        // Send the message
        connectedThread.write(buffer.array());
    }

    public boolean isConnected() {
        return status == ConnectionStatus.CONNECTED;
    }

    private void updateStatus(ConnectionStatus newStatus, BluetoothDevice device) {
        synchronized (lock) {
            if (status != newStatus || (device != null && !device.equals(connectedDevice))) {
                Log.d(TAG, "Status change: " + status + " -> " + newStatus);
                status = newStatus;
                connectedDevice = device;
                if (connectionCallback != null) {
                    connectionCallback.onConnectionStatusChanged(status, device);
                }
            }
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

    private class AcceptThread extends Thread {
        private final BluetoothServerSocket serverSocket;
        private volatile boolean isRunning;

        public AcceptThread() {
            BluetoothServerSocket tmp = null;
            try {
                tmp = bluetoothAdapter.listenUsingRfcommWithServiceRecord(APP_NAME, APP_UUID);
            } catch (IOException e) {
                Log.e(TAG, "Socket's listen() method failed", e);
            }
            serverSocket = tmp;
            isRunning = true;
        }

        public void run() {
            setName("AcceptThread");
            BluetoothSocket socket;

            while (isRunning) {
                try {
                    if (serverSocket == null) break;
                    socket = serverSocket.accept();
                    
                    if (socket != null) {
                        synchronized (BluetoothService.this) {
                            switch (status) {
                                case LISTENING:
                                case CONNECTING:
                                    // Normal connection scenario
                                    connected(socket);
                                    break;
                                case NONE:
                                case CONNECTED:
                                    // Not ready for connection or already connected
                                    try {
                                        socket.close();
                                    } catch (IOException e) {
                                        Log.e(TAG, "Could not close unwanted socket", e);
                                    }
                                    break;
                            }
                        }
                    }
                } catch (IOException e) {
                    if (isRunning) {
                        Log.e(TAG, "Accept failed", e);
                    }
                    break;
                }
            }
        }

        public void cancel() {
            isRunning = false;
            try {
                if (serverSocket != null) {
                    serverSocket.close();
                }
            } catch (IOException e) {
                Log.e(TAG, "Could not close the connect socket", e);
            }
        }
    }

    private class ConnectThread extends Thread {
        private final BluetoothSocket socket;
        private final BluetoothDevice device;

        public ConnectThread(BluetoothDevice device) {
            this.device = device;
            BluetoothSocket tmp = null;
            try {
                tmp = device.createRfcommSocketToServiceRecord(APP_UUID);
            } catch (IOException e) {
                Log.e(TAG, "Socket's create() method failed", e);
            }
            socket = tmp;
        }

        public void run() {
            setName("ConnectThread");
            bluetoothAdapter.cancelDiscovery();

            try {
                if (socket == null) throw new IOException("Socket is null");
                socket.connect();
            } catch (IOException e) {
                Log.e(TAG, "Connection failed", e);
                try {
                    socket.close();
                } catch (IOException closeException) {
                    Log.e(TAG, "Could not close the client socket", closeException);
                }
                connectionFailed();
                return;
            }

            synchronized (BluetoothService.this) {
                connectThread = null;
            }

            connected(socket);
        }

        public void cancel() {
            try {
                if (socket != null) {
                    socket.close();
                }
            } catch (IOException e) {
                Log.e(TAG, "Could not close the client socket", e);
            }
        }
    }

    private class ConnectedThread extends Thread {
        private final BluetoothSocket socket;
        private final InputStream inputStream;
        private final OutputStream outputStream;
        private volatile boolean isRunning;

        public ConnectedThread(BluetoothSocket socket) {
            this.socket = socket;
            InputStream tmpIn = null;
            OutputStream tmpOut = null;

            try {
                tmpIn = socket.getInputStream();
                tmpOut = socket.getOutputStream();
            } catch (IOException e) {
                Log.e(TAG, "Error creating temp streams", e);
            }

            inputStream = tmpIn;
            outputStream = tmpOut;
            isRunning = true;
        }

        public void run() {
            byte[] lengthBuffer = new byte[4];
            byte[] messageBuffer = new byte[MAX_BUFFER_SIZE];

            while (isRunning) {
                try {
                    // Read message length first
                    readFully(inputStream, lengthBuffer, 0, 4);
                    int messageLength = ByteBuffer.wrap(lengthBuffer).getInt();

                    if (messageLength <= 0 || messageLength > MAX_BUFFER_SIZE) {
                        throw new IOException("Invalid message length: " + messageLength);
                    }

                    // Read the message
                    readFully(inputStream, messageBuffer, 0, messageLength);
                    String message = new String(messageBuffer, 0, messageLength, StandardCharsets.UTF_8);
                    
                    Log.d(TAG, "Message received: " + message);
                    messageCallback.onMessageReceived(message);

                } catch (IOException e) {
                    if (isRunning) {
                        Log.e(TAG, "Connection lost", e);
                        connectionLost();
                    }
                    break;
                }
            }
        }

        private void readFully(InputStream input, byte[] buffer, int offset, int length) throws IOException {
            int bytesRead = 0;
            while (bytesRead < length) {
                int result = input.read(buffer, offset + bytesRead, length - bytesRead);
                if (result == -1) {
                    throw new IOException("End of stream");
                }
                bytesRead += result;
            }
        }

        public void write(byte[] buffer) {
            try {
                synchronized (this) {
                    outputStream.write(buffer);
                    outputStream.flush();
                }
                Log.d(TAG, "Message sent successfully");
            } catch (IOException e) {
                Log.e(TAG, "Error sending message", e);
                connectionLost();
            }
        }

        public void cancel() {
            isRunning = false;
            try {
                socket.close();
            } catch (IOException e) {
                Log.e(TAG, "Could not close the connect socket", e);
            }
        }
    }
}
