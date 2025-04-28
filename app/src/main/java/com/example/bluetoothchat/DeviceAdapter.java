package com.example.bluetoothchat;

import android.bluetooth.BluetoothDevice;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.ArrayList;
import java.util.List;

public class DeviceAdapter extends RecyclerView.Adapter<DeviceAdapter.ViewHolder> {
    private final List<BluetoothDevice> devices = new ArrayList<>();
    private final DeviceClickListener listener;

    public interface DeviceClickListener {
        void onDeviceClick(BluetoothDevice device);
    }

    public DeviceAdapter(DeviceClickListener listener) {
        this.listener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_device, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        BluetoothDevice device = devices.get(position);
        String deviceName = device.getName();
        if (deviceName == null || deviceName.isEmpty()) {
            deviceName = device.getAddress();
        }
        holder.deviceName.setText(deviceName);
        holder.deviceAddress.setText(device.getAddress());
        
        holder.itemView.setOnClickListener(v -> {
            if (listener != null) {
                listener.onDeviceClick(device);
            }
        });
    }

    @Override
    public int getItemCount() {
        return devices.size();
    }

    public void addDevice(BluetoothDevice device) {
        String deviceAddress = device.getAddress();
        for (BluetoothDevice existingDevice : devices) {
            if (existingDevice.getAddress().equals(deviceAddress)) {
                return; // Device already in list
            }
        }
        devices.add(device);
        notifyItemInserted(devices.size() - 1);
    }

    public void clearDevices() {
        int size = devices.size();
        devices.clear();
        notifyItemRangeRemoved(0, size);
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        final TextView deviceName;
        final TextView deviceAddress;

        ViewHolder(View view) {
            super(view);
            deviceName = view.findViewById(R.id.deviceName);
            deviceAddress = view.findViewById(R.id.deviceAddress);
        }
    }
}
