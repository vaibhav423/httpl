package com.example.bluetoothchat;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import com.example.bluetoothchat.BluetoothService.ConnectionStatus;
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
import java.util.Set;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
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

    private final BroadcastReceiver discoveryReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (BluetoothDevice.ACTION_FOUND.equals(action)) {
                BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                if (device != null && deviceAdapter != null) {
                    deviceAdapter.addDevice(device);
                    if (scanDialog != null && scanDialog.isShowing()) {
                        scanDialog.findViewById(R.id.emptyText).setVisibility(View.GONE);
                    }
                }
            } else if (BluetoothAdapter.ACTION_DISCOVERY_FINISHED.equals(action)) {
                if (scanDialog != null && scanDialog.isShowing()) {
                    View scanProgress = scanDialog.findViewById(R.id.scanProgress);
                    if (scanProgress != null) {
                        scanProgress.setVisibility(View.GONE);
                    }
                    if (deviceAdapter.getItemCount() == 0) {
                        View emptyText = scanDialog.findViewById(R.id.emptyText);
                        if (emptyText != null) {
                            emptyText.setVisibility(View.VISIBLE);
                        }
                    }
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

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Register for device discovery results
        IntentFilter filter = new IntentFilter();
        filter.addAction(BluetoothDevice.ACTION_FOUND);
        filter.addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED);
        registerReceiver(discoveryReceiver, filter, Context.RECEIVER_NOT_EXPORTED);

        initializeViews();
        setupRecyclerView();
        setupScanDialog();
        checkBluetoothRequirements();
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
            if (!message.isEmpty() && bluetoothService != null && bluetoothService.isConnected()) {
                bluetoothService.sendMessage(message);
                messageAdapter.addMessage(message, true);
                messageInput.setText("");
                messageRecyclerView.smoothScrollToPosition(messageAdapter.getItemCount() - 1);
            } else if (bluetoothService == null || !bluetoothService.isConnected()) {
                Toast.makeText(this, "Not connected to any device", Toast.LENGTH_SHORT).show();
            }
        });

        scanButton.setOnClickListener(v -> showDeviceScanDialog());
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
            if (bluetoothAdapter.isDiscovering()) {
                bluetoothAdapter.cancelDiscovery();
            }
            bluetoothService.connect(device);
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
        
        // Show paired devices first
        Set<BluetoothDevice> pairedDevices = bluetoothAdapter.getBondedDevices();
        if (pairedDevices != null && !pairedDevices.isEmpty()) {
            for (BluetoothDevice device : pairedDevices) {
                deviceAdapter.addDevice(device);
            }
            emptyText.setVisibility(View.GONE);
        }
        
        // Cancel ongoing discovery and start new one
        if (bluetoothAdapter.isDiscovering()) {
            bluetoothAdapter.cancelDiscovery();
        }
        
        if (deviceAdapter.getItemCount() == 0) {
            emptyText.setVisibility(View.VISIBLE);
        }
        
        // Start device discovery
        bluetoothAdapter.startDiscovery();
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
                message -> runOnUiThread(() -> {
                    messageAdapter.addMessage(message, false);
                    messageRecyclerView.smoothScrollToPosition(messageAdapter.getItemCount() - 1);
                }),
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
            
            bluetoothService.start();
        } catch (Exception e) {
            Log.e(TAG, "Error initializing Bluetooth service", e);
            Toast.makeText(this, "Failed to initialize Bluetooth service: " + e.getMessage(), 
                Toast.LENGTH_SHORT).show();
            finish();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(discoveryReceiver);
        } catch (IllegalArgumentException e) {
            // Receiver might not be registered
        }
        if (bluetoothService != null) {
            bluetoothService.stop();
        }
        if (bluetoothAdapter != null && bluetoothAdapter.isDiscovering()) {
            bluetoothAdapter.cancelDiscovery();
        }
    }
}
