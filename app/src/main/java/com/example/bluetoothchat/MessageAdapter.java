package com.example.bluetoothchat;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
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
        public final String text;
        public final boolean isSent;
        public final long timestamp;

        public Message(String text, boolean isSent) {
            this.text = text;
            this.isSent = isSent;
            this.timestamp = System.currentTimeMillis();
        }
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_message, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        Message message = messages.get(position);
        
        // Set message text and timestamp
        holder.messageText.setText(message.text);
        holder.timestamp.setText(timeFormat.format(new Date(message.timestamp)));

        // Set background based on message type
        int backgroundRes = message.isSent ? 
            R.drawable.sent_message_background : 
            R.drawable.received_message_background;
        holder.messageText.setBackgroundResource(backgroundRes);

        // Configure LayoutParams for message text
        ConstraintLayout.LayoutParams textParams = 
            (ConstraintLayout.LayoutParams) holder.messageText.getLayoutParams();
        textParams.horizontalBias = message.isSent ? 1.0f : 0.0f;
        int margin = holder.itemView.getResources()
                .getDimensionPixelSize(R.dimen.message_margin_horizontal);
        textParams.setMarginStart(message.isSent ? margin * 2 : margin / 2);
        textParams.setMarginEnd(message.isSent ? margin / 2 : margin * 2);
        holder.messageText.setLayoutParams(textParams);

        // Configure LayoutParams for timestamp
        ConstraintLayout.LayoutParams timeParams = 
            (ConstraintLayout.LayoutParams) holder.timestamp.getLayoutParams();
        timeParams.horizontalBias = message.isSent ? 1.0f : 0.0f;
        timeParams.setMarginStart(message.isSent ? margin * 2 : margin / 2);
        timeParams.setMarginEnd(message.isSent ? margin / 2 : margin * 2);
        holder.timestamp.setLayoutParams(timeParams);
    }

    @Override
    public int getItemCount() {
        return messages.size();
    }

    public void addMessage(String text, boolean isSent) {
        messages.add(new Message(text, isSent));
        notifyItemInserted(messages.size() - 1);
    }

    public void clear() {
        int size = messages.size();
        messages.clear();
        notifyItemRangeRemoved(0, size);
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
