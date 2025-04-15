package com.persistentportlistener;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;

import java.net.DatagramPacket;
import java.net.DatagramSocket;

public class BackgroundService extends Service {
    private static final int PORT = 9898;
    private boolean isRunning = false;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!isRunning) {
            isRunning = true;
            new Thread(() -> {
                try {
                    DatagramSocket socket = new DatagramSocket(PORT);
                    byte[] buffer = new byte[1024];
                    while (isRunning) {
                        DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                        socket.receive(packet);
                        Log.d("BackgroundService", "Message received: " + new String(packet.getData(), 0, packet.getLength()));

                        // Open YouTube app
                        Intent youtubeIntent = getPackageManager().getLaunchIntentForPackage("com.google.android.youtube");
                        if (youtubeIntent != null) {
                            youtubeIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                            startActivity(youtubeIntent);
                        }
                    }
                    socket.close();
                } catch (Exception e) {
                    Log.e("BackgroundService", "Error in UDP server", e);
                }
            }).start();
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        isRunning = false;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
