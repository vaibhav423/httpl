package com.example.bluetoothchat;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
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
    private RecyclerView messageRecyclerView;
    private MessageAdapter messageAdapter;
    private BluetoothAdapter bluetoothAdapter;

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
        checkBluetoothRequirements();
    }

    private void initializeViews() {
        messageInput = findViewById(R.id.messageInput);
        sendButton = findViewById(R.id.sendButton);
        messageRecyclerView = findViewById(R.id.messageRecyclerView);

        sendButton.setOnClickListener(v -> {
            String message = messageInput.getText().toString().trim();
            if (!message.isEmpty()) {
                Intent intent = new Intent(ACTION_TALK);
                intent.putExtra(EXTRA_MESSAGE, message);
                sendBroadcast(intent);
                messageInput.setText("");
            }
        });
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
        String[] permissions = {
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.BLUETOOTH_SCAN
        };

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
        bluetoothService = new BluetoothService(this, message -> {
            Intent intent = new Intent(ACTION_LISTEN);
            intent.putExtra(EXTRA_MESSAGE, message);
            sendBroadcast(intent);
        });

        IntentFilter talkFilter = new IntentFilter(ACTION_TALK);
        registerReceiver(talkReceiver, talkFilter);

        IntentFilter listenFilter = new IntentFilter(ACTION_LISTEN);
        registerReceiver(listenReceiver, listenFilter);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(talkReceiver);
            unregisterReceiver(listenReceiver);
        } catch (IllegalArgumentException e) {
            // Receivers might not be registered if Bluetooth initialization failed
        }
        if (bluetoothService != null) {
            bluetoothService.stop();
        }
    }
}
