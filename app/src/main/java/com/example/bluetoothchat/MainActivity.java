package com.example.bluetoothchat;

import android.bluetooth.BluetoothAdapter;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

public class MainActivity extends AppCompatActivity {
    private static final String ACTION_TALK = "action:talk";
    private static final String ACTION_LISTEN = "action:listen";
    private static final String EXTRA_MESSAGE = "message";

    private BluetoothService bluetoothService;
    private EditText messageInput;
    private Button sendButton;
    private RecyclerView messageRecyclerView;
    private MessageAdapter messageAdapter;

    private final BroadcastReceiver talkReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (ACTION_TALK.equals(action)) {
                // Handle outgoing message
                String message = intent.getStringExtra(EXTRA_MESSAGE);
                if (message != null && bluetoothService != null) {
                    bluetoothService.sendMessage(message);
                }
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        messageInput = findViewById(R.id.messageInput);
        sendButton = findViewById(R.id.sendButton);
        messageRecyclerView = findViewById(R.id.messageRecyclerView);

        // Set up RecyclerView
        messageAdapter = new MessageAdapter();
        messageRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        messageRecyclerView.setAdapter(messageAdapter);

        // Initialize Bluetooth service
        bluetoothService = new BluetoothService(this, new BluetoothService.MessageCallback() {
            @Override
            public void onMessageReceived(String message) {
                // Broadcast received message with ACTION_LISTEN
                Intent intent = new Intent(ACTION_LISTEN);
                intent.putExtra(EXTRA_MESSAGE, message);
                sendBroadcast(intent);
            }
        });

        // Register receivers for ACTION_TALK and ACTION_LISTEN
        IntentFilter talkFilter = new IntentFilter(ACTION_TALK);
        registerReceiver(talkReceiver, talkFilter);

        IntentFilter listenFilter = new IntentFilter(ACTION_LISTEN);
        registerReceiver(listenReceiver, listenFilter);

        sendButton.setOnClickListener(v -> {
            String message = messageInput.getText().toString().trim();
            if (!message.isEmpty()) {
                // Broadcast message with ACTION_TALK
                Intent intent = new Intent(ACTION_TALK);
                intent.putExtra(EXTRA_MESSAGE, message);
                sendBroadcast(intent);
                messageInput.setText("");
            }
        });
    }

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
    protected void onDestroy() {
        super.onDestroy();
        unregisterReceiver(talkReceiver);
        unregisterReceiver(listenReceiver);
        if (bluetoothService != null) {
            bluetoothService.stop();
        }
    }
}
