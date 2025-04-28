package com.example.bluetoothchat;

import android.Manifest;
import android.app.ActivityManager;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;
import java.util.Set;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private static final int PERMISSION_REQUEST_CODE = 1;

    private EditText messageInput;
    private Button sendButton;
    private Button scanButton;
    private TextView connectionStatus;
    private TextView connectedDevice;
    private RecyclerView messageRecyclerView;
    private MessageAdapter messageAdapter;
    private BluetoothAdapter bluetoothAdapter;
    private DeviceAdapter deviceAdapter;
    private AlertDialog scanDialog;
    private DatabaseHelper databaseHelper;
    private String currentDeviceAddress;
    private boolean receiversRegistered = false;

    private final BroadcastReceiver discoveryReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (BluetoothDevice.ACTION_FOUND.equals(action)) {
                BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                if (device != null && deviceAdapter != null && scanDialog != null && scanDialog.isShowing()) {
                    deviceAdapter.addDevice(device);
                    scanDialog.findViewById(R.id.emptyText).setVisibility(View.GONE);
                }
            } else if (BluetoothAdapter.ACTION_DISCOVERY_FINISHED.equals(action)) {
                if (scanDialog != null && scanDialog.isShowing()) {
                    View scanProgress = scanDialog.findViewById(R.id.scanProgress);
                    if (scanProgress != null) {
                        scanProgress.setVisibility(View.GONE);
                    }
                    if (deviceAdapter.getItemCount() == 0) {
                        scanDialog.findViewById(R.id.emptyText).setVisibility(View.VISIBLE);
                    }
                }
            }
        }
    };

    private final BroadcastReceiver messageReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (ChatService.ACTION_LISTEN.equals(intent.getAction())) {
                String message = intent.getStringExtra(ChatService.EXTRA_MESSAGE);
                if (message != null) {
                    messageAdapter.addMessage(message, false);
                    messageRecyclerView.smoothScrollToPosition(messageAdapter.getItemCount() - 1);
                }
            }
        }
    };

    private final BroadcastReceiver connectionReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String status = intent.getStringExtra("status");
            String deviceName = intent.getStringExtra("device_name");
            String deviceAddress = intent.getStringExtra("device_address");

            updateConnectionStatus(status, deviceName);
            if (deviceAddress != null && !deviceAddress.equals(currentDeviceAddress)) {
                currentDeviceAddress = deviceAddress;
                loadMessageHistory(deviceAddress);
            }
        }
    };

    private final ActivityResultLauncher<Intent> enableBluetoothLauncher = registerForActivityResult(
        new ActivityResultContracts.StartActivityForResult(),
        result -> {
            if (result.getResultCode() == RESULT_OK) {
                startChatService();
            } else {
                Toast.makeText(this, "Bluetooth is required for this app", Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    );

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initializeViews();
        setupRecyclerView();
        setupScanDialog();
        
        databaseHelper = new DatabaseHelper(this);
        
        checkBluetoothRequirements();
    }

    @Override
    protected void onStart() {
        super.onStart();
        registerReceivers();
    }

    @Override
    protected void onStop() {
        super.onStop();
        if (bluetoothAdapter != null && bluetoothAdapter.isDiscovering()) {
            bluetoothAdapter.cancelDiscovery();
        }
        if (receiversRegistered) {
            unregisterReceivers();
        }
    }

    private void registerReceivers() {
        if (!receiversRegistered) {
            IntentFilter discoveryFilter = new IntentFilter();
            discoveryFilter.addAction(BluetoothDevice.ACTION_FOUND);
            discoveryFilter.addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED);
            registerReceiver(discoveryReceiver, discoveryFilter, Context.RECEIVER_NOT_EXPORTED);

            registerReceiver(messageReceiver, new IntentFilter(ChatService.ACTION_LISTEN),
                Context.RECEIVER_NOT_EXPORTED);

            registerReceiver(connectionReceiver,
                new IntentFilter("com.example.bluetoothchat.CONNECTION_STATUS_CHANGED"),
                Context.RECEIVER_NOT_EXPORTED);

            receiversRegistered = true;
        }
    }

    private void unregisterReceivers() {
        try {
            unregisterReceiver(discoveryReceiver);
            unregisterReceiver(messageReceiver);
            unregisterReceiver(connectionReceiver);
            receiversRegistered = false;
        } catch (IllegalArgumentException e) {
            Log.e(TAG, "Error unregistering receivers", e);
        }
    }

    private void initializeViews() {
        messageInput = findViewById(R.id.messageInput);
        sendButton = findViewById(R.id.sendButton);
        scanButton = findViewById(R.id.scanButton);
        connectionStatus = findViewById(R.id.connectionStatus);
        connectedDevice = findViewById(R.id.connectedDevice);
        messageRecyclerView = findViewById(R.id.messageRecyclerView);

        sendButton.setEnabled(false);
        sendButton.setOnClickListener(v -> {
            String message = messageInput.getText().toString().trim();
            if (!message.isEmpty()) {
                Intent intent = new Intent(ChatService.ACTION_TALK);
                intent.putExtra(ChatService.EXTRA_MESSAGE, message);
                sendBroadcast(intent);
                messageInput.setText("");
            }
        });

        scanButton.setOnClickListener(v -> showDeviceScanDialog());
    }

    private void loadMessageHistory(String deviceAddress) {
        messageAdapter.clear();
        List<MessageAdapter.Message> messages = databaseHelper.getMessages(deviceAddress);
        for (MessageAdapter.Message message : messages) {
            messageAdapter.addMessage(message.text, message.isSent);
        }
        if (!messages.isEmpty()) {
            messageRecyclerView.smoothScrollToPosition(messages.size() - 1);
        }
    }

    private void startChatService() {
        if (!isServiceRunning(ChatService.class)) {
            Intent serviceIntent = new Intent(this, ChatService.class);
            serviceIntent.putExtra("username", Build.MODEL);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent);
            } else {
                startService(serviceIntent);
            }
        }
    }

    private boolean isServiceRunning(Class<?> serviceClass) {
        ActivityManager manager = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        for (ActivityManager.RunningServiceInfo service : manager.getRunningServices(Integer.MAX_VALUE)) {
            if (serviceClass.getName().equals(service.service.getClassName())) {
                return true;
            }
        }
        return false;
    }

    private void setupRecyclerView() {
        messageAdapter = new MessageAdapter();
        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        layoutManager.setStackFromEnd(true);
        messageRecyclerView.setLayoutManager(layoutManager);
        messageRecyclerView.setAdapter(messageAdapter);
    }

    private void setupScanDialog() {
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_device_list, null);
        RecyclerView deviceList = dialogView.findViewById(R.id.deviceList);
        View scanProgress = dialogView.findViewById(R.id.scanProgress);
        TextView emptyText = dialogView.findViewById(R.id.emptyText);

        deviceAdapter = new DeviceAdapter(device -> {
            Intent intent = new Intent(this, ChatService.class);
            intent.putExtra("connect_device", device.getAddress());
            startService(intent);
            scanDialog.dismiss();
        });

        deviceList.setLayoutManager(new LinearLayoutManager(this));
        deviceList.setAdapter(deviceAdapter);

        AlertDialog.Builder builder = new AlertDialog.Builder(this)
            .setTitle("Select a Device")
            .setView(dialogView)
            .setNegativeButton("Cancel", (dialog, which) -> {
                if (bluetoothAdapter.isDiscovering()) {
                    bluetoothAdapter.cancelDiscovery();
                }
            });

        scanDialog = builder.create();
    }

    private void showDeviceScanDialog() {
        deviceAdapter.clearDevices();
        scanDialog.show();
        
        View scanProgress = scanDialog.findViewById(R.id.scanProgress);
        TextView emptyText = scanDialog.findViewById(R.id.emptyText);
        
        scanProgress.setVisibility(View.VISIBLE);
        emptyText.setVisibility(View.GONE);
        
        Set<BluetoothDevice> pairedDevices = bluetoothAdapter.getBondedDevices();
        if (pairedDevices != null && !pairedDevices.isEmpty()) {
            for (BluetoothDevice device : pairedDevices) {
                deviceAdapter.addDevice(device);
            }
            emptyText.setVisibility(View.GONE);
        }
        
        if (bluetoothAdapter.isDiscovering()) {
            bluetoothAdapter.cancelDiscovery();
        }
        
        if (deviceAdapter.getItemCount() == 0) {
            emptyText.setVisibility(View.VISIBLE);
        }
        
        bluetoothAdapter.startDiscovery();
    }

    private void updateConnectionStatus(String status, String deviceName) {
        connectionStatus.setText("Status: " + status);
        if (deviceName != null) {
            connectedDevice.setText("Connected to: " + deviceName);
            sendButton.setEnabled(true);
        } else {
            connectedDevice.setText("No device connected");
            sendButton.setEnabled(false);
        }
    }

    private void checkBluetoothRequirements() {
        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            Toast.makeText(this, "Bluetooth is not supported on this device", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            requestBluetoothPermissions();
        } else {
            checkBluetoothEnabled();
        }
    }

    private void requestBluetoothPermissions() {
        String[] permissions;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions = new String[] {
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.FOREGROUND_SERVICE,
                Manifest.permission.POST_NOTIFICATIONS
            };
        } else {
            permissions = new String[] {
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION
            };
        }

        boolean allPermissionsGranted = true;
        for (String permission : permissions) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                allPermissionsGranted = false;
                break;
            }
        }

        if (allPermissionsGranted) {
            checkBluetoothEnabled();
        } else {
            ActivityCompat.requestPermissions(this, permissions, PERMISSION_REQUEST_CODE);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CODE) {
            boolean allPermissionsGranted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allPermissionsGranted = false;
                    break;
                }
            }

            if (allPermissionsGranted) {
                checkBluetoothEnabled();
            } else {
                Toast.makeText(this, "Required permissions not granted", Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    }

    private void checkBluetoothEnabled() {
        if (!bluetoothAdapter.isEnabled()) {
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            enableBluetoothLauncher.launch(enableBtIntent);
        } else {
            startChatService();
        }
    }
}
