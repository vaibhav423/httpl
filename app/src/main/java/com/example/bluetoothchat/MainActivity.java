package com.example.bluetoothchat;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import java.util.Set;
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

public class MainActivity extends AppCompatActivity {
    private static final String ACTION_TALK = "action:talk";
    private static final String ACTION_LISTEN = "action:listen";
    private static final String EXTRA_MESSAGE = "message";
    private static final int PERMISSION_REQUEST_CODE = 1;

    private BluetoothService bluetoothService;
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
    
    private final BroadcastReceiver scanReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (BluetoothDevice.ACTION_FOUND.equals(action)) {
                BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                if (device != null && deviceAdapter != null) {
                    deviceAdapter.addDevice(device);
                    scanDialog.findViewById(R.id.emptyText).setVisibility(View.GONE);
                }
            } else if (BluetoothAdapter.ACTION_DISCOVERY_FINISHED.equals(action)) {
                scanDialog.findViewById(R.id.scanProgress).setVisibility(View.GONE);
                if (deviceAdapter.getItemCount() == 0) {
                    scanDialog.findViewById(R.id.emptyText).setVisibility(View.VISIBLE);
                }
            }
        }
    };

    private final ActivityResultLauncher<Intent> enableBluetoothLauncher = registerForActivityResult(
        new ActivityResultContracts.StartActivityForResult(),
        result -> {
            if (result.getResultCode() == RESULT_OK) {
                initializeBluetoothService();
            } else {
                Toast.makeText(this, "Bluetooth is required for this app", Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    );

    private final BroadcastReceiver talkReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (ACTION_TALK.equals(action)) {
                String message = intent.getStringExtra(EXTRA_MESSAGE);
                if (message != null && bluetoothService != null) {
                    bluetoothService.sendMessage(message);
                }
            }
        }
    };

    private final BroadcastReceiver listenReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (ACTION_LISTEN.equals(action)) {
                String message = intent.getStringExtra(EXTRA_MESSAGE);
                if (message != null) {
                    messageAdapter.addMessage("Received: " + message);
                }
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initializeViews();
        setupRecyclerView();
        setupScanDialog();
        checkBluetoothRequirements();
        
        // Register for broadcasts when a device is discovered
        IntentFilter filter = new IntentFilter();
        filter.addAction(BluetoothDevice.ACTION_FOUND);
        filter.addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED);
        registerReceiver(scanReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
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
            if (!message.isEmpty() && bluetoothService != null) {
                Intent intent = new Intent(ACTION_TALK);
                intent.putExtra(EXTRA_MESSAGE, message);
                sendBroadcast(intent);
                messageInput.setText("");
            }
        });

        scanButton.setOnClickListener(v -> showDeviceScanDialog());
    }

    private void setupRecyclerView() {
        messageAdapter = new MessageAdapter();
        messageRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        messageRecyclerView.setAdapter(messageAdapter);
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
                Manifest.permission.BLUETOOTH_SCAN
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
                Toast.makeText(this, "Bluetooth permissions are required", Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    }

    private void checkBluetoothEnabled() {
        if (!bluetoothAdapter.isEnabled()) {
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            enableBluetoothLauncher.launch(enableBtIntent);
        } else {
            initializeBluetoothService();
        }
    }

    private void initializeBluetoothService() {
        try {
            bluetoothService = new BluetoothService(
                this,
                message -> {
                    Intent intent = new Intent(ACTION_LISTEN);
                    intent.putExtra(EXTRA_MESSAGE, message);
                    sendBroadcast(intent);
                },
                (status, device) -> runOnUiThread(() -> {
                    switch (status) {
                        case NONE:
                            connectionStatus.setText("Status: Disconnected");
                            connectedDevice.setText("No device connected");
                            sendButton.setEnabled(false);
                            scanButton.setEnabled(true);
                            break;
                        case LISTENING:
                            connectionStatus.setText("Status: Waiting for connection");
                            connectedDevice.setText("No device connected");
                            sendButton.setEnabled(false);
                            scanButton.setEnabled(true);
                            break;
                        case CONNECTING:
                            connectionStatus.setText("Status: Connecting...");
                            connectedDevice.setText(device != null ? 
                                "Connecting to: " + device.getName() : "");
                            sendButton.setEnabled(false);
                            scanButton.setEnabled(false);
                            break;
                        case CONNECTED:
                            connectionStatus.setText("Status: Connected");
                            connectedDevice.setText(device != null ? 
                                "Connected to: " + device.getName() : "");
                            sendButton.setEnabled(true);
                            scanButton.setEnabled(true);
                            break;
                    }
                })
            );
            
            // Only register receivers if service initialization succeeded
            if (bluetoothService != null) {
                IntentFilter talkFilter = new IntentFilter(ACTION_TALK);
                registerReceiver(talkReceiver, talkFilter, Context.RECEIVER_NOT_EXPORTED);

                IntentFilter listenFilter = new IntentFilter(ACTION_LISTEN);
                registerReceiver(listenReceiver, listenFilter, Context.RECEIVER_NOT_EXPORTED);

                bluetoothService.start(); // Start the Bluetooth service after initialization
            } else {
                Toast.makeText(this, "Failed to initialize Bluetooth service", Toast.LENGTH_SHORT).show();
                finish();
            }
        } catch (Exception e) {
            Log.e("MainActivity", "Error initializing Bluetooth service", e);
            Toast.makeText(this, "Failed to initialize Bluetooth service: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            finish();
        }
    }

    private void setupScanDialog() {
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_device_list, null);
        RecyclerView deviceList = dialogView.findViewById(R.id.deviceList);
        View scanProgress = dialogView.findViewById(R.id.scanProgress);
        TextView emptyText = dialogView.findViewById(R.id.emptyText);

        deviceAdapter = new DeviceAdapter(device -> {
            if (bluetoothAdapter.isDiscovering()) {
                bluetoothAdapter.cancelDiscovery();
            }
            bluetoothService.connect(device);
            scanDialog.dismiss();
        });

        deviceList.setLayoutManager(new LinearLayoutManager(this));
        deviceList.setAdapter(deviceAdapter);

        AlertDialog.Builder builder = new AlertDialog.Builder(this)
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
        
        // Show progress and hide empty text initially
        scanProgress.setVisibility(View.VISIBLE);
        emptyText.setVisibility(View.GONE);
        
        // Add paired devices first
        Set<BluetoothDevice> pairedDevices = bluetoothAdapter.getBondedDevices();
        if (pairedDevices.size() > 0) {
            for (BluetoothDevice device : pairedDevices) {
                deviceAdapter.addDevice(device);
            }
        }
        
        // Start discovery
        if (bluetoothAdapter.isDiscovering()) {
            bluetoothAdapter.cancelDiscovery();
        }
        
        // Show empty text if no devices found
        if (deviceAdapter.getItemCount() == 0) {
            emptyText.setVisibility(View.VISIBLE);
        }
        
        bluetoothAdapter.startDiscovery();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(talkReceiver);
            unregisterReceiver(listenReceiver);
            unregisterReceiver(scanReceiver);
        } catch (IllegalArgumentException e) {
            // Receivers might not be registered if Bluetooth initialization failed
        }
        if (bluetoothService != null) {
            bluetoothService.stop();
        }
        if (bluetoothAdapter != null && bluetoothAdapter.isDiscovering()) {
            bluetoothAdapter.cancelDiscovery();
        }
    }
}
