package com.example.bluetoothchat;

import android.annotation.SuppressLint;
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
import android.content.pm.ServiceInfo;
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
    
    private static final String CHANNEL_ID = "BluetoothChatChannel";
    private static final int NOTIFICATION_ID = 1;
    
    private BluetoothService bluetoothService;
    private DatabaseHelper databaseHelper;
    private NotificationManager notificationManager;
    private String username = "User";
    private boolean isServiceStarted = false;

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
        if (bluetoothService != null && bluetoothService.getConnectedDevice() != null) {
            BluetoothDevice device = bluetoothService.getConnectedDevice();
            
            // Save received message
            databaseHelper.saveMessage(message, false, device.getAddress(), username);

            // Broadcast received message
            Intent intent = new Intent(ACTION_LISTEN);
            intent.putExtra(EXTRA_MESSAGE, message);
            sendBroadcast(intent);

            // Update notification
            updateNotification(getString(R.string.new_message, device.getName()));
        }
    };

    private final BluetoothService.ConnectionCallback connectionCallback = (status, device) -> {
        // Broadcast status change
        Intent intent = new Intent("com.example.bluetoothchat.CONNECTION_STATUS_CHANGED");
        intent.putExtra("status", status.name());
        if (device != null) {
            intent.putExtra("device_name", device.getName());
            intent.putExtra("device_address", device.getAddress());
        }
        sendBroadcast(intent);

        // Update notification
        updateNotification(getStatusString(status, device));
    };

    @Override
    public void onCreate() {
        super.onCreate();
        databaseHelper = new DatabaseHelper(this);
        notificationManager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        
        // Initialize notification channel first
        createNotificationChannel();

        // Register receiver
        registerReceiver(talkReceiver, new IntentFilter(ACTION_TALK), Context.RECEIVER_NOT_EXPORTED);
        
        // Initialize Bluetooth service
        initializeBluetoothService();
    }

    @SuppressLint("NewApi")
    private void startForegroundService() {
        if (!isServiceStarted) {
            Notification notification = createNotification(getString(R.string.starting_service));
            
            if (Build.VERSION.SDK_INT >= 34) { // Android 14 (UPSIDE_DOWN_CAKE)
                startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
            } else {
                startForeground(NOTIFICATION_ID, notification);
            }
            
            isServiceStarted = true;
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Start foreground service
        startForegroundService();
        
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
                getString(R.string.chat_notification_channel),
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription(getString(R.string.chat_notification_description));
            channel.setShowBadge(false);
            notificationManager.createNotificationChannel(channel);
        }
    }

    private Notification createNotification(String content) {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        notificationIntent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        
        @SuppressLint("UnspecifiedImmutableFlag")
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent, 
            PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(content)
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setContentIntent(pendingIntent)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .build();
    }

    private void updateNotification(String content) {
        Notification notification = createNotification(content);
        notificationManager.notify(NOTIFICATION_ID, notification);
    }

    private String getStatusString(BluetoothService.ConnectionStatus status, BluetoothDevice device) {
        String deviceName = device != null ? device.getName() : getString(R.string.no_device_connected);
        switch (status) {
            case NONE:
                return getString(R.string.status_disconnected);
            case LISTENING:
                return getString(R.string.status_listening);
            case CONNECTING:
                return getString(R.string.status_connecting, deviceName);
            case CONNECTED:
                return getString(R.string.status_connected, deviceName);
            default:
                return getString(R.string.status_disconnected);
        }
    }

    private void initializeBluetoothService() {
        try {
            bluetoothService = new BluetoothService(this, messageCallback, connectionCallback);
            bluetoothService.start();
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize BluetoothService", e);
            stopSelf();
        }
    }

    private void sendMessage(String message) {
        if (bluetoothService != null && bluetoothService.isConnected()) {
            BluetoothDevice device = bluetoothService.getConnectedDevice();
            
            // Save message to database
            databaseHelper.saveMessage(message, true, device.getAddress(), username);

            // Send message via Bluetooth
            bluetoothService.sendMessage(message);
        }
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(talkReceiver);
        } catch (IllegalArgumentException e) {
            Log.e(TAG, "Error unregistering receiver", e);
        }
        if (bluetoothService != null) {
            bluetoothService.stop();
        }
        isServiceStarted = false;
    }
}
