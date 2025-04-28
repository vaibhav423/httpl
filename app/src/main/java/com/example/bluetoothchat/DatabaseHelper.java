package com.example.bluetoothchat;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import java.util.ArrayList;
import java.util.List;

public class DatabaseHelper extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "bluetooth_chat.db";
    private static final int DATABASE_VERSION = 1;

    private static final String TABLE_MESSAGES = "messages";
    private static final String COLUMN_ID = "_id";
    private static final String COLUMN_TEXT = "text";
    private static final String COLUMN_IS_SENT = "is_sent";
    private static final String COLUMN_TIMESTAMP = "timestamp";
    private static final String COLUMN_DEVICE_ADDRESS = "device_address";
    private static final String COLUMN_USERNAME = "username";

    private static final String CREATE_TABLE_MESSAGES = 
        "CREATE TABLE " + TABLE_MESSAGES + " (" +
        COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
        COLUMN_TEXT + " TEXT NOT NULL, " +
        COLUMN_IS_SENT + " INTEGER NOT NULL, " +
        COLUMN_TIMESTAMP + " INTEGER NOT NULL, " +
        COLUMN_DEVICE_ADDRESS + " TEXT NOT NULL, " +
        COLUMN_USERNAME + " TEXT NOT NULL)";

    public DatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL(CREATE_TABLE_MESSAGES);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_MESSAGES);
        onCreate(db);
    }

    public long saveMessage(String text, boolean isSent, String deviceAddress, String username) {
        SQLiteDatabase db = getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(COLUMN_TEXT, text);
        values.put(COLUMN_IS_SENT, isSent ? 1 : 0);
        values.put(COLUMN_TIMESTAMP, System.currentTimeMillis());
        values.put(COLUMN_DEVICE_ADDRESS, deviceAddress);
        values.put(COLUMN_USERNAME, username);
        return db.insert(TABLE_MESSAGES, null, values);
    }

    public List<MessageAdapter.Message> getMessages(String deviceAddress) {
        List<MessageAdapter.Message> messages = new ArrayList<>();
        SQLiteDatabase db = getReadableDatabase();
        
        String[] columns = {COLUMN_TEXT, COLUMN_IS_SENT, COLUMN_TIMESTAMP};
        String selection = COLUMN_DEVICE_ADDRESS + " = ?";
        String[] selectionArgs = {deviceAddress};
        String orderBy = COLUMN_TIMESTAMP + " ASC";
        
        try (Cursor cursor = db.query(TABLE_MESSAGES, columns, selection, selectionArgs, 
                null, null, orderBy)) {
            while (cursor.moveToNext()) {
                String text = cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_TEXT));
                boolean isSent = cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_IS_SENT)) == 1;
                long timestamp = cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_TIMESTAMP));
                messages.add(new MessageAdapter.Message(text, isSent));
            }
        }
        
        return messages;
    }

    public List<String> getConnectedDevices() {
        List<String> devices = new ArrayList<>();
        SQLiteDatabase db = getReadableDatabase();
        
        String query = "SELECT DISTINCT " + COLUMN_DEVICE_ADDRESS + 
                      " FROM " + TABLE_MESSAGES + 
                      " ORDER BY " + COLUMN_TIMESTAMP + " DESC";
        
        try (Cursor cursor = db.rawQuery(query, null)) {
            while (cursor.moveToNext()) {
                devices.add(cursor.getString(0));
            }
        }
        
        return devices;
    }

    public String getLastConnectedDevice() {
        SQLiteDatabase db = getReadableDatabase();
        String query = "SELECT " + COLUMN_DEVICE_ADDRESS + 
                      " FROM " + TABLE_MESSAGES + 
                      " ORDER BY " + COLUMN_TIMESTAMP + " DESC LIMIT 1";
        
        try (Cursor cursor = db.rawQuery(query, null)) {
            if (cursor.moveToFirst()) {
                return cursor.getString(0);
            }
        }
        return null;
    }
}
