package com.example.bluetoothchat;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import androidx.constraintlayout.widget.ConstraintLayout;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MessageAdapter extends RecyclerView.Adapter<MessageAdapter.ViewHolder> {
    private final List<Message> messages = new ArrayList<>();
    private final SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm", Locale.getDefault());

    public static class Message {
        final String text;
        final boolean isSent;
        final long timestamp;

        Message(String text, boolean isSent) {
            this.text = text;
            this.isSent = isSent;
            this.timestamp = System.currentTimeMillis();
        }
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_message, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(ViewHolder holder, int position) {
        Message message = messages.get(position);
        // Set message text and timestamp
        holder.messageText.setText(message.text);
        holder.timestamp.setText(timeFormat.format(new Date(message.timestamp)));
        
        // Set background and alignment based on message type
        int backgroundRes = message.isSent ? 
            R.drawable.sent_message_background : 
            R.drawable.received_message_background;
        holder.messageText.setBackgroundResource(backgroundRes);
        
        // Align sent messages to the right, received to the left
        ConstraintLayout.LayoutParams params = 
            (ConstraintLayout.LayoutParams) holder.messageText.getLayoutParams();
        params.horizontalBias = message.isSent ? 1.0f : 0.0f;
        holder.messageText.setLayoutParams(params);
        
        // Align timestamp with message
        params = (ConstraintLayout.LayoutParams) holder.timestamp.getLayoutParams();
        params.horizontalBias = message.isSent ? 1.0f : 0.0f;
        holder.timestamp.setLayoutParams(params);
    }

    @Override
    public int getItemCount() {
        return messages.size();
    }

    public void addMessage(String text, boolean isSent) {
        int position = messages.size();
        messages.add(new Message(text, isSent));
        notifyItemInserted(position);
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        final TextView messageText;
        final TextView timestamp;

        ViewHolder(View view) {
            super(view);
            messageText = view.findViewById(R.id.messageText);
            timestamp = view.findViewById(R.id.timestamp);
        }
    }
}
