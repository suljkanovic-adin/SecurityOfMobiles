package com.example.comadinsuljkanovicmyfirstapp;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import android.widget.Toast;

/**
 * A BroadcastReceiver that listens for a custom broadcast action
 * and shows a Toast + logs a message.
 */
public class MyBroadcastReceiver extends BroadcastReceiver {

    private static final String TAG = "MyBroadcastReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        Log.d(TAG, "Custom broadcast received!");
        Toast.makeText(context, "Received custom broadcast!", Toast.LENGTH_SHORT).show();
    }
}
