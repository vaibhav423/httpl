package com.example.bluetoothchat;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

public class ChatService extends Service {
    private static final String TAG = "ChatService";
    public static final String ACTION_TALK = "action:talk";
    public static final String ACTION_LISTEN = "action:listen";
    public static final String EXTRA_MESSAGE = "message";
    private static final String CHANNEL_ID = "BluetoothChat";
    private static final int NOTIFICATION_ID = 1;
    
    private BluetoothService bluetoothService;
    private DatabaseHelper databaseHelper;
    private String username = "User"; // Default username

    private final BroadcastReceiver talkReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (ACTION_TALK.equals(intent.getAction())) {
                String message = intent.getStringExtra(EXTRA_MESSAGE);
                if (message != null && bluetoothService != null && bluetoothService.isConnected()) {
                    sendMessage(message);
                }
            }
        }
    };

    private final BluetoothService.MessageCallback messageCallback = message -> {
        // Save received message
        if (bluetoothService != null && bluetoothService.getConnectedDevice() != null) {
            String deviceAddress = bluetoothService.getConnectedDevice().getAddress();
            databaseHelper.saveMessage(message, false, deviceAddress, username);

            // Broadcast received message
            Intent intent = new Intent(ACTION_LISTEN);
            intent.putExtra(EXTRA_MESSAGE, message);
            sendBroadcast(intent);

            // Update notification
            updateNotification("New message from " + 
                bluetoothService.getConnectedDevice().getName());
        }
    };

    private final BluetoothService.ConnectionCallback connectionCallback = (status, device) -> {
        String action = "com.example.bluetoothchat.CONNECTION_STATUS_CHANGED";
        Intent intent = new Intent(action);
        intent.putExtra("status", status.name());
        if (device != null) {
            intent.putExtra("device_name", device.getName());
            intent.putExtra("device_address", device.getAddress());
        }
        sendBroadcast(intent);

        // Update notification
        updateNotification(getStatusText(status, device));
    };

    @Override
    public void onCreate() {
        super.onCreate();
        databaseHelper = new DatabaseHelper(this);
        
        // Register for message broadcasts
        IntentFilter filter = new IntentFilter(ACTION_TALK);
        registerReceiver(talkReceiver, filter, Context.RECEIVER_NOT_EXPORTED);

        createNotificationChannel();
        startForeground(NOTIFICATION_ID, createNotification("Starting service..."));
        
        // Initialize Bluetooth service
        initializeBluetoothService();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            if (intent.hasExtra("username")) {
                username = intent.getStringExtra("username");
            }
            if (intent.hasExtra("connect_device") && bluetoothService != null) {
                String deviceAddress = intent.getStringExtra("connect_device");
                BluetoothDevice device = bluetoothService.getBluetoothAdapter()
                    .getRemoteDevice(deviceAddress);
                bluetoothService.connect(device);
            }
        }
        
        return START_STICKY;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Bluetooth Chat",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Bluetooth Chat Service");
            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(channel);
        }
    }

    private Notification createNotification(String text) {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent, 
            PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Bluetooth Chat")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
            .setContentIntent(pendingIntent)
            .build();
    }

    private void updateNotification(String text) {
        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.notify(NOTIFICATION_ID, createNotification(text));
    }

    private String getStatusText(BluetoothService.ConnectionStatus status, BluetoothDevice device) {
        switch (status) {
            case NONE:
                return "Disconnected";
            case LISTENING:
                return "Waiting for connection";
            case CONNECTING:
                return "Connecting to " + (device != null ? device.getName() : "device");
            case CONNECTED:
                return "Connected to " + (device != null ? device.getName() : "device");
            default:
                return "Unknown status";
        }
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void initializeBluetoothService() {
        bluetoothService = new BluetoothService(this, messageCallback, connectionCallback);
        bluetoothService.start();
    }

    private void sendMessage(String message) {
        if (bluetoothService != null && bluetoothService.isConnected()) {
            // Save message to database
            BluetoothDevice device = bluetoothService.getConnectedDevice();
            databaseHelper.saveMessage(message, true, device.getAddress(), username);

            // Send message via Bluetooth
            bluetoothService.sendMessage(message);
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(talkReceiver);
        } catch (IllegalArgumentException e) {
            // Receiver not registered
        }
        if (bluetoothService != null) {
            bluetoothService.stop();
        }
    }
}
